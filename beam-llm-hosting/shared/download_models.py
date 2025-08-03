CACHE_PATH = "./weights"

def download_model(model_name: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from huggingface_hub import login
    from peft import PeftModel
    import torch
    import os

    login(
        token=os.getenv("HUGGINGFACE_TOKEN", "") or "",
        new_session=False,
    )

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
