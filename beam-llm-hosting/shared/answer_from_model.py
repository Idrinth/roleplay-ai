from unittest import result

import torch
from typing import List, Dict

def answer_from_model(model, processor, incoming_messages: List[Dict[str, str]], max_tokens: int= 550):
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

    text = processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    print(f"Total Prompt Length: {len(processor.apply_chat_template(messages, tokenize=False))}")
    generated = model.to("cuda:0").generate(
        **text.to("cuda:0"),
        max_new_tokens=max_tokens,
        pad_token_id=processor.tokenizer.eos_token_id,
    )
    llm_result = processor.batch_decode(
        generated,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    if llm_result == "":
        raise Exception("No answer from model")
    last_message = incoming_messages[len(incoming_messages) - 1]["content"].strip()
    outputs = llm_result.split(last_message)
    strip_position = 0
    while len(outputs) == 1:
        # something was changed in the last message, likely dot or comma placement corrections
        strip_position += 1
        if strip_position >= len(last_message) - 3:
            raise Exception("Can't find last message in output.")
        outputs = llm_result.split(last_message[strip_position:])
    output = outputs[len(outputs) - 1].strip()
    if output == "":
        raise Exception("No answer from model")
    return output
