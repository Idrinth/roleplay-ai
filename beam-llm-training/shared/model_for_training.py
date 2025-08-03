def load_model_tokenizer(system_prompt: str):
    import unsloth
    from .constants import MAX_SEQUENCE_LENGTH

    unsloth_template = \
        system_prompt + "\n" \
        "{% for message in messages %}" \
        "{% if message['role'] == 'user' %}" \
        "{{ '>>> User: ' + message['content'] + '\n' }}" \
        "{% elif message['role'] == 'assistant' %}" \
        "{{ '>>> Assistant: ' + message['content'] + eos_token + '\n' }}" \
        "{% endif %}" \
        "{% endfor %}" \
        "{% if add_generation_prompt %}" \
        "{{ '>>> Assistant: ' }}" \
        "{% endif %}"
    unsloth_eos_token = "eos_token"

    model, tokenizer = unsloth.FastLanguageModel.from_pretrained(
        model_name="unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
        max_seq_length=MAX_SEQUENCE_LENGTH,
        max_memory={"cpu": "8GiB", 0: "40GiB"},
        dtype=None,
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

    return model, tokenizer
