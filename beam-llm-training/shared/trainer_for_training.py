def get_trainer(model, tokenizer, dataset):
    from trl import SFTConfig, SFTTrainer, DataCollatorForCompletionOnlyLM
    from .constants import MAX_SEQUENCE_LENGTH

    response_template = ">>> Assistant:"
    collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

    return SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQUENCE_LENGTH,
        dataset_num_proc=2,
        packing=False,
        data_collator=collator,
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
