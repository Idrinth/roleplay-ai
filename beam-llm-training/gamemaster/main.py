from beam import function
from shared.constants import IMAGE

NAME = "gamemaster"

def callback(data):
    dataset_list = []
    for response in data["answers"]:
        dataset_list.append({
            "messages": [
                {
                    "role": "user",
                    "content": data["prompt"],
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
    image=IMAGE,
    secrets=["HUGGINGFACE_TOKEN"],
)
def train():
    import unsloth
    from shared.model_for_training import load_model_tokenizer
    from shared.dataset_for_training import load_dataset
    from shared.trainer_for_training import get_trainer
    from shared.constants import GLOBAL_BZ, DEVICES, MAX_SEQUENCE_LENGTH, BZ
    from shared.export_results import export
    import shared.patches

    model, tokenizer = load_model_tokenizer(
        "You are a GAME MASTER. React to provided actions with in character responses of NPCs."
    )

    dataset = load_dataset(callback)
    trainer = get_trainer(model, tokenizer, dataset)

    trainer.train()

    export(NAME, model, tokenizer, dataset)

if __name__ == "__main__":
    train.remote()
