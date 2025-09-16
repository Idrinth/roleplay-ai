from beam import endpoint, Image, QueueDepthAutoscaler
from shared.download_models import CACHE_PATH
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

    return (DiffusionPipeline
            .from_pretrained("ovedrive/qwen-image-4bit", dtype=torch.bfloat16)
            .to("cuda:0"))

@endpoint(
    secrets=["HUGGINGFACE_TOKEN"],
    name=f"roleplay-ai-{NAME}",
    on_start=download_models,
    volumes=VOLUMES,
    cpu=2,
    gpu=["A100-40"],
    memory="6Gi",
    autoscaler=QueueDepthAutoscaler(
        max_containers=5,
        tasks_per_container=1,
    ),
    keep_warm_seconds=30,
    authorized=True,
    timeout=720,
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
    from io import BytesIO
    import base64
    image_pipe = context.on_start_value
    image = image_pipe(
        prompt=params.get("messages")[0] + ", " + whitelist,
        negative_prompt=blacklist,
        width=1664,
        height=928,
        num_inference_steps=15,
        true_cfg_scale=4.0,
        generator=torch.Generator(device="cuda").manual_seed(42)
    ).images[0]

    buf = BytesIO()
    image.save(buf, format="JPEG", quality=90, optimize=True)
    image_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {
        "image": image_b64,
    }
