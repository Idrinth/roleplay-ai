CACHE_PATH = "/weights"

def download_model(model_name: str):
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from huggingface_hub import login
    from peft import PeftModel
    import torch
    import os

    login(
        token=os.getenv("HUGGINGFACE_TOKEN", "") or "",
        new_session=False,
    )

    base_model_name = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"

    base_model = AutoModelForImageTextToText.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        cache_dir=CACHE_PATH,
        device_map="auto",
        # attn_implementation="flash_attention_2", not possible with beam atm
        # rope_scaling={"type": "dynamic", "factor": 2},
    )

    model = PeftModel.from_pretrained(
        base_model,
        model_name,
        cache_dir=CACHE_PATH,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(
        base_model_name,
        cache_dir=CACHE_PATH,
        trust_remote_code=True,
    )

    return model.to('cuda:0'), processor
