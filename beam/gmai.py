from beam import endpoint, Image, QueueDepthAutoscaler, Volume

CACHE_PATH = "./weights"

def download_models():
    from transformers import AutoTokenizer, AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained("teknium/OpenHermes-2.5-Mistral-7B", cache_dir=CACHE_PATH)
    tokenizer = AutoTokenizer.from_pretrained("teknium/OpenHermes-2.5-Mistral-7B", cache_dir=CACHE_PATH)

    return model, tokenizer

@endpoint(
    name="gamemaster-ai",
    on_start=download_models,
    volumes=[Volume(name="gamemaster-ai-cache", mount_path=CACHE_PATH)],
    cpu=1,
    gpu=["A100-40", "H100"],
    memory="32Gi",
    autoscaler=QueueDepthAutoscaler(
        max_containers=5,
        tasks_per_container=1,
    ),
    keep_warm_seconds=90,
    authorized=True,
    image=Image(python_version="python3.12", python_packages="requirements.remote.txt", env_vars="HF_HUB_ENABLE_HF_TRANSFER=1"),
)
def answer(context, **params):
    model, tokenizer = context.on_start_value

    text = tokenizer.apply_chat_template(params["messages"], tokenize=True, add_generation_prompt=True, return_tensors="pt")
    generate_ids = model.generate(text, max_length=550)
    result = tokenizer.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True
    )[0]

    parts = result.split("\n assistant\n")
    return {"answer": parts[len(parts) - 1]}
