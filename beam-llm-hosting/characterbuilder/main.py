from beam import endpoint, Image, QueueDepthAutoscaler, Volume
from shared.download_models import CACHE_PATH

NAME = 'characterbuilder'

with open('./rules.md', 'r', encoding="utf-8") as md_file:
    rules = md_file.read()

def download_models():
    from shared.download_models import download_model
    return download_model(f"Idrinth/{NAME}ai")

@endpoint(
    secrets=["HUGGINGFACE_TOKEN"],
    name=f"roleplay-ai-{NAME}",
    on_start=download_models,
    volumes=[Volume(name="roleplay-ai-cache", mount_path=CACHE_PATH)],
    cpu=2,
    gpu=["T4", "A10G", "RTX4090", "A100-40", "H100"],
    memory="6Gi",
    autoscaler=QueueDepthAutoscaler(
        max_containers=5,
        tasks_per_container=1,
    ),
    keep_warm_seconds=90,
    authorized=True,
    image=Image(python_version="python3.11", python_packages="requirements.remote.txt", env_vars="HF_HUB_ENABLE_HF_TRANSFER=1"),
)
def answer(context, **params):
    from shared.answer_from_model import answer_from_model
    model, tokenizer = context.on_start_value
    messages = [
        {
           "role": "system",
           "content": rules,
        },
    ]
    for message in params["messages"]:
        messages.append(message)
    return {
        "answer": answer_from_model(model, tokenizer, messages, 1100)
    }
