def get_trainer(model, tokenizer, dataset):
    from trl import SFTConfig, SFTTrainer
    from transformers import DataCollatorForLanguageModeling
    import torch
    from .constants import MAX_SEQUENCE_LENGTH

    class CustomDataCollator(DataCollatorForLanguageModeling):
        def __call__(self, examples):
            batch = super().__call__(examples)
            # Fix attention mask dtype
            if 'attention_mask' in batch and batch['attention_mask'].dtype == torch.long:
                batch['attention_mask'] = batch['attention_mask'].to(torch.bool)
            return batch

    data_collator = CustomDataCollator(
        tokenizer=tokenizer,
        mlm=False,
    )

    return SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQUENCE_LENGTH,
        dataset_num_proc=2,
        packing=False,
        data_collator=data_collator,
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
            dataloader_pin_memory=False,
            bf16=True,
        ),
    )
