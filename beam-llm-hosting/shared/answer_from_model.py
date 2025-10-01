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
            "content": {
                "text": message["content"],
                "type": "text",
            },
            "role": roles[message["role"]],
        })

    tokenizer = processor.tokenizer
    template = r"""
{{- bos_token }}

{%- if messages[0]['role'] == 'system' %}
    {%- set system_message = messages[0]['content']['text'] %}
    {%- set loop_messages = messages[1:] %}
{%- else %}
    {{- raise_exception('System message required!') }}
{%- endif %}
{{- '[SYSTEM_PROMPT]' + system_message + '[/SYSTEM_PROMPT]' }}

{%- for message in loop_messages %}
    {%- if message['role'] == 'user' %}
        {{- '[INST]' }}
        {{- message['content']['text'] }}
        {{- '[/INST]' }}
    {%- elif message['role'] == 'assistant' %}
        {{- message['content']['text'] + eos_token }}
    {%- else %}
        {{- raise_exception('Only user, assistant roles are supported!') }}
    {%- endif %}
{%- endfor %}
    """
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
        chat_template=template,
    )
    pad_id = tokenizer.pad_token_id
    if pad_id is None:
        pad_id = tokenizer.eos_token_id

    stop_ids = [tokenizer.eos_token_id]
    for tok in ("[/INST]", "<|eot_id|>", "[/SYSTEM_PROMPT]"):
        tid = tokenizer.convert_tokens_to_ids(tok)
        if tid is not None and tid != tokenizer.unk_token_id:
            stop_ids.append(tid)
    attn = (inputs != pad_id).long()

    out = model.to("cuda:0").generate(
        input_ids=inputs.to("cuda:0"),
        attention_mask=attn.to("cuda:0"),
        max_new_tokens=max_tokens,
        pad_token_id=pad_id,
        eos_token_id=stop_ids,
        repetition_penalty=1.5,
        temperature=0.45,
        do_sample=True,
    )

    llm_result = tokenizer.batch_decode(
        out[:, inputs.shape[1]:],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    if llm_result == "":
        raise Exception("No answer from model")
    return llm_result
