from metaflow import FlowSpec, step, batch, ollama #, pypi


class HelloOllamaFlow(FlowSpec):

    @ollama(models=["qwen:0.5b"])
    @batch(cpu=6, queue="job-queue-metaflow2", image="docker.io/eddieob/ollama-metaflow-task:cpu")
    @step
    def start(self):
        from ollama import chat

        response_qwen = chat(
            model="qwen:0.5b",
            messages=[
                {
                    "role": "user",
                    "content": "What are the leading Chinese tech companies?",
                },
            ],
        )
        print(
            f"\n\n Response from qwen:0.5b {response_qwen['message']['content']} \n\n"
        )
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    HelloOllamaFlow()
