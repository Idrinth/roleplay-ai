import os

from beam import endpoint, Image, QueueDepthAutoscaler, Volume, env

CACHE_PATH = "./weights"

def download_models():
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from huggingface_hub import login
    import os
    login(
        token=os.getenv("HUGGINGFACE_TOKEN", "") or "",
        new_session=False,
    )
    model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3", cache_dir=CACHE_PATH)
    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3", cache_dir=CACHE_PATH)

    return model, tokenizer

@endpoint(
    secrets=["HUGGINGFACE_TOKEN"],
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
    image=Image(python_version="python3.11", python_packages="requirements.remote.txt", env_vars="HF_HUB_ENABLE_HF_TRANSFER=1"),
)
def answer(context, **params):
    model, tokenizer = context.on_start_value

    print(params["messages"])
    params["messages"][len(params["messages"]) - 1]["content"] += "\n\nYou are the Game Master, react as the world."
    messages = []
    roles = {
        "user": "user",
        "agent": "assistant",
        "assistant": "assistant",
        "system": "system",
    }
    for message in params["messages"]:
        messages.append({
            "content": message["content"],
            "role": roles[message["role"]],
        })

    text = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False, return_tensors="pt")
    generated = model.to("cuda:0").generate(text.to("cuda:0"), max_new_tokens=550)
    result = tokenizer.batch_decode(
        generated,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]

    outputs = result.split(params["messages"][len(params["messages"]) - 1]["content"])
    output = outputs[len(outputs) - 1]
    print(output)
    return {"answer": output}
