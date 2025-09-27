CACHE_PATH = "/weights"

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
        device_map="auto",
        use_cache=True,
        # attn_implementation="flash_attention_2", not possible with beam atm
        # rope_scaling={"type": "dynamic", "factor": 2},
        max_position_embeddings=65536,
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
        trust_remote_code=True,
        model_max_length= 65536,
        padding_side= "left",
    )

    return model.to('cuda:0'), tokenizer
