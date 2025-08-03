---
license: mit
task_categories:
- text-generation
language:
- en
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
dataset_info:
  features:
  - name: messages
    list:
    - name: content
      dtype: string
    - name: role
      dtype: string
  - name: text
    dtype: string
  splits:
  - name: train
    num_bytes: 8900
    num_examples: 5
  download_size: 10965
  dataset_size: 8900
pretty_name: CharacterBuilderAI
---
# Dataset Card for CharacterBuilderAI

This is a human written training set of prompts and responses to finetune a model to be a better character creator.

## Dataset Details

### Dataset Description

This is a human-curated training dataset designed to fine-tune language models for tabletop role-playing game (RPG) character creator scenarios. The dataset contains carefully crafted prompt-response pairs that demonstrate how an AI should respond as when introducing a character in single-player role-playing scenarios.

### Dataset Summary

- **Curated by:** Björn 'Idrinth' Büttner
- **Language(s) (NLP):** English
- **License:** MIT

### Dataset Sources

Repository: https://github.com/bjoern-buettner/roleplay-ai

### Data Structure
The dataset contains training examples with the following structure:
  - messages: List of conversation turns with content (the message text) and role (user/assistant)
  - text: Formatted text representation of the conversation

Each example demonstrates proper character creator responses to player descriptions in role-playing scenarios.

## Intended Uses

## Primary Use Case
Fine-tuning language models to serve AI character creator for:
  - Single-player tabletop RPG sessions
  - Interactive storytelling applications
  - Role-playing game assistance tools

Example Applications
  - Digital D&D campaigns
  - Solo adventure gaming
  - Creative writing prompts
  - Interactive fiction development

## Usage Example
```py
from datasets import load_dataset
```

### Load the dataset
```py
dataset = load_dataset("Idrinth/characterbuilderai")
```

#### Access training examples
```py
train_data = dataset["train"]
print(f"Number of examples: {len(train_data)}")
```

### View a sample conversation
```py
sample = train_data[0]
print("Sample conversation:")
for message in sample["messages"]:
    print(f"{message['role']}: {message['content']}")
```

## Limitations and Considerations
  - Small dataset size: Currently only 5 training examples, limiting models's exposure to
    diverse scenarios
  - Domain-specific: Focused specifically on RPG/fantasy scenarios
  - English only: No multilingual support
  - Early stage: Dataset is actively being expanded with more training scenarios

## Contributing
The dataset is actively being expanded. Contributors can help by:
  - Adding new RPG scenario examples
  - Improving existing conversatin quality
  - Suggesting additional use cases

For contributions, visit the [GitHub Repository](https://github.com/bjoern-buettner/roleplay-ai) or join the [Discord community](https://discord.gg/idrinth).

## Citation
If you use this dataset in your research or applications, please cite
```
@dataset{characterbuilderai,
  title={Character Builder AI Training Dataset},
  author={Björn Büttner},
  year={2025},
  url={https://huggingface.co/datasets/Idrinth/characterbuilderai}
}
```
