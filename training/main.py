import yaml
import unsloth
from datasets import Dataset
import os
from trl import SFTConfig, SFTTrainer
from opensloth.opensloth_config import FastModelArgs, LoraArgs, OpenSlothConfig, TrainingArguments
from opensloth.scripts.opensloth_sft_trainer import run_mp_training, setup_envs

GLOBAL_BZ = 32
DEVICES = [0, 1]
MAX_SEQUENCE_LENGTH = 16384
BZ=1

model, tokenizer = unsloth.FastLanguageModel.from_pretrained(
    model_name="unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    max_seq_length=MAX_SEQUENCE_LENGTH,
    max_memory={"cpu": "48GiB", 0: "8GiB", 1: "8GiB"},
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

unsloth_template = \
    "You are a GAME MASTER. React to provided actions with in character responses of NPCs.\n" \
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

tokenizer = unsloth.get_chat_template(
    tokenizer,
    chat_template=(unsloth_template, unsloth_eos_token,),
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
    map_eos_token=True,
)

dataset_list = []
for fname in os.listdir("/raw-data"):
    try:
        if fname.endswith(".yml"):
            with open(f"/raw-data/{fname}", "r") as file:
                data = yaml.load(file, yaml.SafeLoader)
                for response in data["answers"]:
                    dataset_list.append({
                        "messages": [
                            {
                                "role": "user",
                                "content": data["prompt"],
                            },
                            {
                                "role": "assistant",
                                "content": response,
                            }
                        ],
                        "text": ">>> User: " + data["prompt"] + "\n"
                                                                ">>> Assistant: " + response + "\n"
                    })
    except Exception as e:
        print(f"{fname}: {e}")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=Dataset.from_list(dataset_list),
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

trainer.train_dataset.save_to_disk("data/mistral-7b-instruct-v0.3-bnb-4bit/")

opensloth_config = OpenSlothConfig(
    data_cache_path="data/mistral-7b-instruct-v0.3-bnb-4bit/",
    devices=DEVICES,
    fast_model_args=FastModelArgs(
        model_name="unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
        max_seq_length=MAX_SEQUENCE_LENGTH,
        load_in_4bit=True,
        max_memory={"cpu": "48GiB", 0: "8GiB", 1: "8GiB"},
    ),
    lora_args=LoraArgs(
        r=8,
        lora_alpha=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0,
        bias="none",
        use_rslora=False,
    ),
    sequence_packing=True,
)
training_config = TrainingArguments(
    output_dir="outputs/exps/mistral-7b-instruct-v0.3-bnb-4bit",
    resume_from_checkpoint="outputs/exps/mistral-7b-instruct-v0.3-bnb-4bit",
    save_only_model=False,
    max_steps=10,
    per_device_train_batch_size=BZ,
    gradient_accumulation_steps=GLOBAL_BZ // (len(DEVICES) * BZ),
    learning_rate=1e-5,
    logging_steps=1,
    num_train_epochs=1,
    lr_scheduler_type="linear",
    warmup_steps=5,
    save_total_limit=1,
    weight_decay=0.01,
    optim="adamw_8bit",
    seed=3407,
    report_to="none",
)

if __name__ == '__main__':
    os.environ["WANDB_PROJECT"] = "opensloth"
    os.environ["WANDB_NAME"] = (
        f"mistral-7b-instruct-v0.3-bnb-4bit_2gpu_packing_globalbz{GLOBAL_BZ}_samples10000"
    )

    print(
        f"Global batch size: {len(DEVICES) * BZ * training_config.gradient_accumulation_steps}"
    )
    print(f"Gradient accumulation steps: {training_config.gradient_accumulation_steps}")

    setup_envs(opensloth_config, training_config)
    run_mp_training(DEVICES, opensloth_config, training_config)

    model.push_to_hub_gguf("Idrinth/gamemasterai", tokenizer, quantization_method="q4_k_m")
    print(f"Saved Model at Idrinth/gamemasterai")
