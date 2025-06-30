import json

import unsloth
import subprocess
from datasets import Dataset
import torch
import os
from trl import SFTConfig, SFTTrainer
from peft import PeftModel
import transformers
import huggingface_hub

max_seq_length = 2048

model, tokenizer = unsloth.FastLanguageModel.from_pretrained(
    model_name = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    max_seq_length = max_seq_length,
    max_memory = {"cpu": "40GIB", 0: "4GIB"},
    dtype = None,
    load_in_4bit = True,
    device_map="auto",
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
    "You are a GAME MASTER. React to provided actions with in character responses of NPCs.\n"\
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

dataset_list = []
for fname in ["dwarf-at-inn", "gate-of-lothern"]:
    try:
        with open(f"/raw-data/{fname}.json", "r") as file:
            for dts in json.load(file):
                dataset_list.append({
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
                    "text": ">>> User: " + dts["Prompt"] + "\n"
                        ">>> Assistant: " + dts["Response"] + "\n"
                })
    except Exception as e:
        print(f"{fname}: {e}")

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = Dataset.from_list(dataset_list),
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
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

try:
    model.to("cpu")
    model_name = os.getenv("LLM_MODEL")
    if model_name is None:
        model_name = "trained_model"
        print("Warning: LLM_MODEL environment variable not set, using 'trained_model' as filename")

    save_path = f"/trained/{model_name}"
    model.to("cpu")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    print(f"Saved HF-Model at: {save_path}")

    huggingface_hub.login(
        token=os.getenv("HF_TOKEN"),
        new_session=False,
    )
    base_model = transformers.AutoModelForCausalLM.from_pretrained(
        "mistralai/Mistral-7B-Instruct-v0.3",
        max_memory = {"cpu": "40GIB", 0: "4GIB"},
        torch_dtype=torch.float16,
        device_map={"": "cpu"},
    )

    merged_model = PeftModel.from_pretrained(base_model, save_path)
    merged_model = merged_model.merge_and_unload()
    print(f"Model merged")
    merged_path = f"{save_path}_merged"
    merged_model.to("cpu")
    merged_model.save_pretrained(merged_path)
    tokenizer.save_pretrained(merged_path)
    print(f"Saved Merged HF-Model at: {merged_path}")
    #subprocess.run(
    #    [
    #        "cp",
    #        "/training/config.json",
    #        f"{save_path}_merged/config.json",
    #    ]
    #)
    out = subprocess.run(
        [
            "/ollama/.venv/bin/python3",
            "/ollama/convert_hf_to_gguf.py",
            merged_path,
            "--outfile",
            f"{save_path}.gguf",
        ],
        stderr=subprocess.STDOUT,
        text=True,
        stdout=subprocess.PIPE,
    )
    print(out.stdout)
    print(f"Saved OLLAMA-Model at: {save_path}.gguf")
except Exception as e:
    print(f"Error: {e}")