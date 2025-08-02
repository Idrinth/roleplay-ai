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
pretty_name: Gamemaster AI
---
# Dataset Card for Gamemaster AI

This is a human written training set of prompts and responses to finetune a model to be a better game master.

## Dataset Details

### Dataset Description

This is a human written training set of prompts and responses to finetune a model to be a better game master.

- **Curated by:** Björn 'Idrinth' Büttner
- **Language(s) (NLP):** English
- **License:** MIT

### Dataset Sources

- **Repository:** [github.com/bjoern-buettner/roleplay-ai](https://github.com/bjoern-buettner/roleplay-ai)

## Uses

This set is intended to be used for fine tuning a model to provide a better conversation partner in single player role play.
