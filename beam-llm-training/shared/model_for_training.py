def load_model_tokenizer(system_prompt: str):
    import unsloth
    import torch
    from .constants import MAX_SEQUENCE_LENGTH

    unsloth_template = "{{- bos_token }}\n[SYSTEM_PROMPT]" + system_prompt + """[/SYSTEM_PROMPT]\n
{% for message in messages %}
    {%- if message['role'] == 'user' %}
        {{- '[INST]' }}
        {{- message['content']['text'] }}
        {{- '[/INST]' }}
    {%- elif message['role'] == 'assistant' %}
        {{- message['content']['text'] + eos_token }}
    {% endif %}" \
{% endfor %}"
"""
    unsloth_eos_token = "eos_token"

    model, tokenizer = unsloth.FastLanguageModel.from_pretrained(
        model_name="unsloth/Mistral-Small-3.2-24B-Instruct-2506",
        max_seq_length=MAX_SEQUENCE_LENGTH,
        max_memory={"cpu": "8GiB", 0: "40GiB"},
        dtype=torch.bfloat16,
        load_in_4bit=True,
        device_map="auto",
    )

    model = unsloth.FastLanguageModel.get_peft_model(
        model,
        r=8,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )
    tokenizer = unsloth.get_chat_template(
        tokenizer,
        chat_template=(unsloth_template, unsloth_eos_token,),
        mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
        map_eos_token=True,
    )

    original_call = tokenizer.__call__

    def fixed_call(*args, **kwargs):
        result = original_call(*args, **kwargs)
        if hasattr(result, 'attention_mask') and result.attention_mask is not None:
            if result.attention_mask.dtype == torch.long:
                result.attention_mask = result.attention_mask.to(torch.bool)
        return result

    tokenizer.__call__ = fixed_call

    return model, tokenizer
