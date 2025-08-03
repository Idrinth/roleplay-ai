def export(name: str, model, tokenizer, dataset):
    import os

    dataset.push_to_hub(f"Idrinth/{name}ai", token=os.environ["HUGGINGFACE_TOKEN"])
    print(f"Saved Dataset at Idrinth/{name}ai")
    model.push_to_hub(f"Idrinth/{name}ai", tokenizer, quantization_method="q4_k_m", token=os.environ["HUGGINGFACE_TOKEN"])
    print(f"Saved Model at Idrinth/{name}ai")
