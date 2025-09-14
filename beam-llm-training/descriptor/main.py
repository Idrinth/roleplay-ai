from beam import function
from shared.model_for_training import load_model_tokenizer
from shared.dataset_for_training import load_dataset
from shared.trainer_for_training import get_trainer
from shared.constants import GLOBAL_BZ, DEVICES, MAX_SEQUENCE_LENGTH, BZ, IMAGE
from shared.export_results import export

NAME = "descriptor"

def callback(data):
    dataset_list = []
    for response in data["descriptions"]:
        dataset_list.append({
            "messages": [
                {
                    "role": "user",
                    "content": data["messages"][0],
                },
                {
                    "role": "assistant",
                    "content": data["messages"][1],
                },
                {
                    "role": "user",
                    "content": "Create a detailed description of the situation described for Image Generation.",
                },
                {
                    "role": "assistant",
                    "content": response,
                }
            ],
            "text": ">>> User: " + data["messages"][0] + "\n>>> Assistant: " + data["messages"][1] + "\n>>> User: Create a detailed description of the situation described for Image Generation.\n>>> Assistant: " + response + "\n"
        })
    return dataset_list

@function(
    timeout=-1,
    cpu=1,
    gpu_count=1,
    gpu=["A100-40", "H100"],
    memory="8Gi",
    name=f"roleplay-ai-{NAME}-training",
    image=IMAGE,
    secrets=["HUGGINGFACE_TOKEN"],
)
def train():
    model, tokenizer = load_model_tokenizer(
        "Create an image description for the situation described in the user messages taking the information in this message into account."
    )

    dataset = load_dataset(callback)
    trainer = get_trainer(model, tokenizer, dataset)

    trainer.train()

    export(NAME, model, tokenizer, dataset)

if __name__ == "__main__":
    train.remote()
