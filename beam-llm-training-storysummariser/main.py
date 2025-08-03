from beam import function, Image

GLOBAL_BZ = 32
DEVICES = [0]
MAX_SEQUENCE_LENGTH = 32768
BZ=1

unsloth_template = \
    "You are reading a role playing session. SUMMARISE the most important points of the following message.\n" \
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

@function(
    timeout=-1,
    cpu=1,
    gpu_count=1,
    gpu=["A100-40", "H100"],
    memory="8Gi",
    name="roleplay-ai-storysummariser-training",
    image=Image(python_version="python3.12", python_packages="requirements.remote.txt", env_vars="HF_HUB_ENABLE_HF_TRANSFER=1"),
    secrets=["HUGGINGFACE_TOKEN"],
)
def train():
    import yaml
    import unsloth
    from datasets import Dataset
    import os
    from trl import SFTConfig, SFTTrainer

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

    dataset_list = []
    for fname in os.listdir("./raw-data"):
        try:
            if fname.endswith(".yml"):
                with open(f"./raw-data/{fname}", "r") as file:
                    data = yaml.load(file, yaml.SafeLoader)
                    for response in data["summaries"]:
                        dataset_list.append({
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "\n\n".join(data["messages"]),
                                },
                                {
                                    "role": "assistant",
                                    "content": response,
                                }
                            ],
                            "text": ">>> User: " + data["prompt"] + "\n>>> Assistant: " + response + "\n"
                        })
        except Exception as e:
            print(f"{fname}: {e}")

    dataset = Dataset.from_list(dataset_list)
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQUENCE_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=SFTConfig(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=60,
            learning_rate=2e-4,
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir="outputs",
            report_to="none",
        ),
    )

    trainer.train()

    dataset.push_to_hub("Idrinth/storysummariserai", token=os.environ["HUGGINGFACE_TOKEN"])
    model.push_to_hub("Idrinth/storysummariserai", tokenizer, quantization_method="q4_k_m", token=os.environ["HUGGINGFACE_TOKEN"])
    print(f"Saved Model at Idrinth/storysummariserai")

if __name__ == "__main__":
    train.remote()
