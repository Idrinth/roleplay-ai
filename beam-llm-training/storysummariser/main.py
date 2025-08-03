from beam import function, Image
from shared.model_for_training import load_model_tokenizer
from shared.dataset_for_training import load_dataset
from shared.trainer_for_training import get_trainer
from shared.constants import GLOBAL_BZ, DEVICES, MAX_SEQUENCE_LENGTH, BZ
from shared.export_results import export

NAME = "storysummariser"

def callback(data):
    dataset_list = []
    for response in data["summaries"]:
        dataset_list.append({
            "messages": [
                {
                    "role": "user",
                    "content": "\n\n".join(data["messages"]),
                },
                {
                    "role": "assistant",
                    "content": response,
                }
            ],
            "text": ">>> User: " + data["prompt"] + "\n>>> Assistant: " + response + "\n"
        })
    return dataset_list

@function(
    timeout=-1,
    cpu=1,
    gpu_count=1,
    gpu=["A100-40", "H100"],
    memory="8Gi",
    name=f"roleplay-ai-{NAME}-training",
    image=Image(python_version="python3.12", python_packages="requirements.remote.txt", env_vars="HF_HUB_ENABLE_HF_TRANSFER=1"),
    secrets=["HUGGINGFACE_TOKEN"],
)
def train():
    model, tokenizer = load_model_tokenizer(
        "You are reading a role playing session. SUMMARISE the most important points of the following message."
    )

    dataset = load_dataset(callback)
    trainer = get_trainer(model, tokenizer, dataset)

    trainer.train()

    export(NAME, model, tokenizer, dataset)

if __name__ == "__main__":
    train.remote()
