from beam import endpoint, Image, QueueDepthAutoscaler
from shared.download_models import CACHE_PATH
from shared.allowed_gpus import ALL_POSSIBLE_GPUS
from shared.volumes import VOLUMES
from shared.enable_snapshotting import ENABLE_SNAPSHOTTING

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
    volumes=VOLUMES,
    cpu=2,
    gpu=ALL_POSSIBLE_GPUS,
    memory="6Gi",
    autoscaler=QueueDepthAutoscaler(
        max_containers=5,
        tasks_per_container=1,
    ),
    keep_warm_seconds=90,
    authorized=True,
    checkpoint_enabled=ENABLE_SNAPSHOTTING,
    image=Image(
        python_version="python3.11",
        python_packages="requirements.remote.txt",
        env_vars={
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "HF_HOME": CACHE_PATH,
        }
    ),
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
