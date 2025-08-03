from beam import endpoint, Image, QueueDepthAutoscaler, Volume, env

CACHE_PATH = "./weights"

def download_models():
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from huggingface_hub import login
    from peft import PeftModel
    import torch
    import os

    login(
        token=os.getenv("HUGGINGFACE_TOKEN", "") or "",
        new_session=False,
    )

    model_name = "Idrinth/characterbuilderai"
    base_model_name = "mistralai/Mistral-7B-Instruct-v0.3"

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        cache_dir=CACHE_PATH,
        device_map="auto"
    )

    model = PeftModel.from_pretrained(
        base_model,
        model_name,
        cache_dir=CACHE_PATH,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_name,
        cache_dir=CACHE_PATH,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )

    return model, tokenizer

@endpoint(
    secrets=["HUGGINGFACE_TOKEN"],
    name="roleplay-ai-characterbuilder",
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
    import torch
    model, tokenizer = context.on_start_value

    params["messages"][len(params["messages"]) - 1]["content"] += "\n\n" + params["messages"][0]["content"]
    messages = []
    roles = {
        "user": "user",
        "agent": "assistant",
        "assistant": "assistant",
        "system": "system",
        "developer": "system",
    }
    for message in params["messages"]:
        messages.append({
            "content": message["content"],
            "role": roles[message["role"]],
        })

    text = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
    attention_mask = torch.ones(text.shape, dtype=torch.long)
    generated = model.to("cuda:0").generate(
        text.to("cuda:0"),
        attention_mask=attention_mask.to("cuda:0"),
        max_new_tokens=550,
        pad_token_id=tokenizer.eos_token_id,
    )
    result = tokenizer.batch_decode(
        generated,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    outputs = result.split("\n assistant\n")
    output = outputs[len(outputs) - 1]
    outputs = output.split(params["messages"][len(params["messages"]) - 1]["content"])
    output = outputs[len(outputs) - 1]
    return {"answer": output}
