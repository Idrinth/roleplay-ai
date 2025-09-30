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
{%- if messages[0]['role'] == 'system' -%}
  {%- set system_message = messages[0]['content'] if messages[0]['content'] is string else messages[0]['content']['text'] -%}
  {%- set messages = messages[1:] -%}
{%- else -%}
  {%- set system_message = '' -%}
{%- endif -%}
{%- if system_message -%}
{{ bos_token }}[INST] {{ system_message }}

{%- endif -%}
{%- for message in messages -%}
  {%- set content = message['content'] if message['content'] is string else message['content']['text'] -%}
  {%- if message['role'] == 'user' -%}
    {%- if loop.first and system_message -%}
{{ content }} [/INST]
    {%- else -%}
{{ bos_token }}[INST] {{ content }} [/INST]
    {%- endif -%}
  {%- elif message['role'] == 'assistant' -%}
 {{ content }}{{ eos_token }}
  {%- endif -%}
{%- endfor -%}
{%- if add_generation_prompt -%}

{%- endif -%}
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
    for tok in ("[/INST]", "<|eot_id|>"):
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
    )

    return tokenizer.decode(out[0, inputs.shape[-1]:], skip_special_tokens=True)
