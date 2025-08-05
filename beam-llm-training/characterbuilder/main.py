from beam import function, Image
from shared.model_for_training import load_model_tokenizer
from shared.dataset_for_training import load_dataset
from shared.trainer_for_training import get_trainer
from shared.constants import GLOBAL_BZ, DEVICES, MAX_SEQUENCE_LENGTH, BZ
from shared.export_results import export

NAME = "characterbuilder"

def callback(data):
    dataset_list = []
    prompt = f"Name: {data['name']}\nGender: {data['gender']}\nRace: {data['race']}\nWear/Clothing: {data['wear']}\nProfession: {data['profession']}\nlocation: {data['location']}\nPurpose/Goal: {data['purpose']}\nMood/Feeling: {data['mood']}\nGenre: {data['genre']}\nWorld: {' ,'.join(data['world'])}\nWeather: {data['weather']}\n"
    for introduction in data["introductions"]:
        dataset_list.append({
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
                {
                    "role": "assistant",
                    "content": introduction,
                }
            ],
            "text": ">>> User: " + prompt + "\n>>> Assistant: " + introduction + "\n"
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
        "You are a PLAYER in a ROLE PLAYING GAME. React to provided information with an introductionary statement of situation and character."
    )

    dataset = load_dataset(callback)
    trainer = get_trainer(model, tokenizer, dataset)

    trainer.train()

    export(NAME, model, tokenizer, dataset)

if __name__ == "__main__":
    train.remote()
