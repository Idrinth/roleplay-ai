import torch
from typing import List, Dict

def answer_from_model(model, tokenizer, incoming_messages: List[Dict[str, str]], max_tokens: int= 550):
    messages = []
    roles = {
        "user": "user",
        "agent": "assistant",
        "assistant": "assistant",
        "system": "system",
        "developer": "system",
    }
    for message in incoming_messages:
        messages.append({
            "content": message["content"],
            "role": roles[message["role"]],
        })

    text = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
    attention_mask = torch.ones(text.shape, dtype=torch.long)
    generated = model.to("cuda:0").generate(
        text.to("cuda:0"),
        attention_mask=attention_mask.to("cuda:0"),
        max_new_tokens=max_tokens,
        pad_token_id=tokenizer.eos_token_id,
    )
    result = tokenizer.batch_decode(
        generated,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    outputs = result.split("\n assistant\n")
    output = outputs[len(outputs) - 1]
    outputs = output.split(incoming_messages[len(incoming_messages) - 1]["content"])
    return outputs[len(outputs) - 1]
