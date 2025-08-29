from beam import endpoint, Image, QueueDepthAutoscaler
from shared.download_models import CACHE_PATH
from shared.allowed_gpus import ALL_POSSIBLE_GPUS
from shared.volumes import VOLUMES
from shared.enable_snapshotting import ENABLE_SNAPSHOTTING

NAME = 'painter'

with open('./blacklist.md', 'r', encoding="utf-8") as md_file:
    blacklist = md_file.read()

with open('./whitelist.md', 'r', encoding="utf-8") as md_file:
    whitelist = md_file.read()

def download_models():
    from diffusers import DiffusionPipeline
    from huggingface_hub import login
    import torch
    import os

    login(
        token=os.getenv("HUGGINGFACE_TOKEN", "") or "",
        new_session=False,
    )

    return DiffusionPipeline.from_pretrained("Qwen/Qwen-Image", torch_dtype=torch.bfloat16).to("cuda")

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
    import torch
    import uuid
    import base64
    image_pipe = context.on_start_value
    image = image_pipe(
        prompt=params.get("description") + " " + params.get("world") + ", " + whitelist,
        negative_prompt=blacklist,
        width=1664,
        height=928,
        num_inference_steps=50,
        true_cfg_scale=4.0,
        generator=torch.Generator(device="cuda").manual_seed(42)
    ).images[0]

    name = str(uuid.uuid4()) + ".jpg"
    image.save(name)
    with open(name, "rb") as image_file:
        return {
            "image": base64.b64encode(image_file.read()),
        }
