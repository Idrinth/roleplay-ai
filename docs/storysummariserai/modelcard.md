---
library_name: adapter-transformers
tags:
- unsloth
license: mit
language:
- en
base_model:
- unsloth/mistral-7b-instruct-v0.3-bnb-4bit
pipeline_tag: text-generation
datasets:
- Idrinth/storysummariserai
---

# Model Card for Idrinth/StorySummariserAI

This model is fine-tuned to provide a summarising service for mind theatre role play sessions. Currently the tuning is VERY LIMITED, but we are adding more story bits over time to fix that.


## Model Details

### Model Description

This model is trained to focus on player related action. This should lead to better role playing summaries with it.

### Model Sources

- **Repository:** [GitHub](https://github.com/bjoern-buettner/roleplay-ai)
