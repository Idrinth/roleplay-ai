import json

import unsloth
from datasets import load_dataset
import torch
import os
from trl import SFTConfig, SFTTrainer

max_seq_length = 2048

model, tokenizer = unsloth.FastLanguageModel.from_pretrained(
    model_name = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    max_seq_length = max_seq_length,
    dtype = None,
    load_in_4bit = True,
)

model = unsloth.FastLanguageModel.get_peft_model(
    model,
    r = 8,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

unsloth_template = \
    "{{ bos_token }}"\
    "{% for message in messages %}"\
        "{% if message['role'] == 'user' %}"\
            "{{ '>>> User: ' + message['content'] + '\n' }}"\
        "{% elif message['role'] == 'assistant' %}"\
            "{{ '>>> Assistant: ' + message['content'] + eos_token + '\n' }}"\
        "{% endif %}"\
    "{% endfor %}"\
    "{% if add_generation_prompt %}"\
        "{{ '>>> Assistant: ' }}"\
    "{% endif %}"
unsloth_eos_token = "eos_token"

tokenizer = unsloth.get_chat_template(
    tokenizer,
    chat_template = (unsloth_template, unsloth_eos_token,),
    mapping = {"role" : "role", "content" : "content", "user" : "user", "assistant" : "assistant"},
    map_eos_token = True,
)

for fname in ["dwarf-at-inn", "gate-of-lothern"]:
    try:
        with open(f"/raw-data/{fname}.json", "r") as file:
            dataset = []
            for dts in json.load(file):
                dataset.append({
                    "messages": [
                        {
                            "role": "user",
                            "content": dts["Prompt"],
                        },
                        {
                            "role": "assistant",
                            "content": dts["Response"],
                        }
                    ],
                    "text": [
                        ">>> User: " + dts["Prompt"] + "\n",
                        ">>> Assistant: " + dts["Response"] + "\n"
                    ]
                })
            with open(f"/training-data/{fname}.json", "w") as file2:
                file2.write(json.dumps(dataset))
    except Exception as e:
        print(f"{fname}: {e}")

def formatting_func(examples):
    return {"text": examples["text"]}

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = load_dataset('/training-data')['train'],
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    formatting_function = formatting_func,
    dataset_num_proc = 2,
    packing = False,
    args = SFTConfig(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60,
        learning_rate = 2e-4,
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none",
    ),
)

trainer.train()

model.save_pretrained_gguf(os.getenv("LLM_MODEL"), tokenizer,)