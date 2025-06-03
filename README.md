## Metaflow GPU Cloudformation

A modified version of the blessed [Metaflow Cloudformation template](https://github.com/outerbounds/metaflow-tools/blob/master/aws/cloudformation/metaflow-cfn-template.yml) that enables a GPU queue by default.

There are three changes to pay attention to as you set up your cluster.

### 1. Choosing instance type
This section in the `Parameters`:
```
  GPUComputeEnvInstanceTypes:
    Type: CommaDelimitedList
    Default: "p3.2xlarge,p3.8xlarge,p3.16xlarge"
    Description: "The instance types for the p3 GPU compute environment as a comma-separated list"
```

### 2. Creating a second compute environment

This section in the `Resources`:
```
  ComputeEnvironmentGPU:
    Type: AWS::Batch::ComputeEnvironment
    Properties:
      Type: MANAGED
      ServiceRole: !GetAtt 'BatchExecutionRole.Arn'
      ComputeResources:
        MaxvCpus: !Ref MaxVCPUBatchGPUEnv
        SecurityGroupIds:
          - !GetAtt VPC.DefaultSecurityGroup
        Type: !If [EnableFargateOnBatch, 'FARGATE', 'EC2']
        Subnets:
          - !Ref Subnet1
          - !Ref Subnet2
        MinvCpus: !If [EnableFargateOnBatch, !Ref AWS::NoValue, !Ref MinVCPUBatch]
        InstanceRole: !If [EnableFargateOnBatch, !Ref AWS::NoValue, !GetAtt 'ECSInstanceProfile.Arn']
        InstanceTypes: !If [EnableFargateOnBatch, !Ref AWS::NoValue, !Ref GPUComputeEnvInstanceTypes]
        DesiredvCpus: !If [EnableFargateOnBatch, !Ref AWS::NoValue, !Ref DesiredVCPUBatch]
      State: ENABLED
```

### 3. Creating a second job queue
The `JobQueueGPU` section in the `Resources`:
```
  JobQueueGPU:
    DependsOn: ComputeEnvironmentGPU
    Type: AWS::Batch::JobQueue
    Properties:
      ComputeEnvironmentOrder:
        - Order: 1
          ComputeEnvironment: !Ref ComputeEnvironmentGPU
      State: ENABLED
      Priority: 1
      JobQueueName: !Join [ '-', [ 'job-queue-gpu', !Ref AWS::StackName ] ]
```

## Create the Cloudformation deployment
Go to AWS Console, and upload the `cfn.yaml` file (it is too big for char count using AWS CLI). 

## Testing the Metaflow deployment

### Set up virtual environemnt
```bash
pip install metaflow boto3
```

### Configure Metaflow

You can either do this manually by setting up the Metaflow config file using the `Outputs` tab in Cloudformation console, or run this script (assumes your AWS credentials are set).
```bash
STACK_NAME=metaflow
python mf_configure.py -s $STACK_NAME
```

### Run a flow in your CPU queue

This will run in the `job-queue-metaflow` queue (unless you changed the name).
```bash
python flow.py run
```

### Run a flow in your GPU queue, verifying the hardware is working

**Note**: By default, a fresh AWS account that I created in April 2024 had 0 on-demand P instance type quotas.
In order to run this code, go in AWS Console to `Service Quotas/AWS services/Amazon Elastic Compute Cloud (Amazon EC2)/Running On-Demand P instances`.

This will run in the `job-queue-gpu-metaflow` queue (look at the `start` step `@batch` decorator).
```bash
python gpu_flow.py run
```

## Issues

### Wrong RDS version

AWS seems to have all sorts of churn in Postgres versions on RDS. 
Activate your desired AWS profile, and run this command to find available versions:
```bash
aws rds describe-db-engine-versions --engine postgres --query 'DBEngineVersions[].EngineVersion' --output table
```

Edit the `EngineVersion` of this section

```
  RDSMasterInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBName: 'metaflow'
      AllocatedStorage: 20
      DBInstanceClass: 'db.t3.small'
      DeleteAutomatedBackups: 'true'
      StorageType: 'gp2'
      Engine: 'postgres'
      EngineVersion: '16.4'
      MasterUsername: !Join ['', ['{{resolve:secretsmanager:', !Ref MyRDSSecret, ':SecretString:username}}' ]]
      MasterUserPassword: !Join ['', ['{{resolve:secretsmanager:', !Ref MyRDSSecret, ':SecretString:password}}' ]]
      VPCSecurityGroups:
        - !Ref 'RDSSecurityGroup'
      DBSubnetGroupName: !Ref 'DBSubnetGroup'
```