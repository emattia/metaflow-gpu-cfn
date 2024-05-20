from metaflow import FlowSpec, step, batch


class HelloCPUFlow(FlowSpec):

    @batch(queue="job-queue-metaflow")
    @step
    def start(self):
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    HelloCPUFlow()
