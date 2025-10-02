def export(name: str, model, tokenizer, dataset):
    import os

    dataset.push_to_hub(f"Idrinth/{name}ai", token=os.environ["HUGGINGFACE_TOKEN"])
    print(f"Saved Dataset at Idrinth/{name}ai")
    model.push_to_hub(f"Idrinth/{name}ai", tokenizer, quantization_method="q4_k_m", token=os.environ["HUGGINGFACE_TOKEN"])
    print(f"Saved Model at Idrinth/{name}ai")
    try:
        model.push_to_hub_gguf(f"Idrinth/{name}ai-gguf", tokenizer, quantization_method="q8_0", token=os.environ["HUGGINGFACE_TOKEN"])
        print(f"Saved Model at Idrinth/{name}ai-gguf")
    except Exception as err:
        print(f"Skipping GGUF export for Idrinth/{name}ai-gguf due to error: {err}")
