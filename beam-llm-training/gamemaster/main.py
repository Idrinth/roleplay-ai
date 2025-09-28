from beam import function
from shared.model_for_training import load_model_tokenizer
from shared.dataset_for_training import load_dataset
from shared.trainer_for_training import get_trainer
from shared.constants import GLOBAL_BZ, DEVICES, MAX_SEQUENCE_LENGTH, BZ, IMAGE
from shared.export_results import export

NAME = "gamemaster"

def callback(data):
    dataset_list = []
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
            "text": ">>> User: " + data["prompt"] + "\n>>> Assistant: " + response + "\n"
        })
    return dataset_list

@function(
    timeout=-1,
    cpu=1,
    gpu_count=1,
    gpu=["A100-40", "H100"],
    memory="8Gi",
    name=f"roleplay-ai-{NAME}-training",
    image=IMAGE,
    secrets=["HUGGINGFACE_TOKEN"],
)
def train():
    import unsloth
    from transformers.models.mistral.modeling_mistral import MistralModel
    import torch
    from functools import wraps
    import torch.nn.functional as F

    original_forward = MistralModel.forward

    def patched_forward(self, input_ids=None, attention_mask=None, **kwargs):
        if attention_mask is not None and attention_mask.dtype == torch.long:
            attention_mask = attention_mask.to(torch.bool)
        return original_forward(self, input_ids=input_ids, attention_mask=attention_mask, **kwargs)

    MistralModel.forward = patched_forward

    original_sdpa = F.scaled_dot_product_attention

    @wraps(original_sdpa)
    def patched_sdpa(query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False, **kwargs):
        if attn_mask is not None:
            if attn_mask.dtype == torch.long:
                attn_mask = attn_mask.to(torch.bool)
            if attn_mask.dim() == 2:
                batch_size, seq_len = attn_mask.shape
                attn_mask = attn_mask.view(batch_size, 1, 1, seq_len)
            elif attn_mask.dim() == 3 and query.dim() == 4:
                attn_mask = attn_mask.unsqueeze(1)
            if query.size(-2) != attn_mask.size(-1):
                target_len = query.size(-2)
                if attn_mask.size(-1) > target_len:
                    attn_mask = attn_mask[..., :target_len]
                elif attn_mask.size(-1) < target_len:
                    pad_size = target_len - attn_mask.size(-1)
                    attn_mask = F.pad(attn_mask, (0, pad_size), value=0)

        return original_sdpa(query, key, value, attn_mask, dropout_p, is_causal, **kwargs)

    F.scaled_dot_product_attention = patched_sdpa

    model, tokenizer = load_model_tokenizer(
        "You are a GAME MASTER. React to provided actions with in character responses of NPCs."
    )

    dataset = load_dataset(callback)
    trainer = get_trainer(model, tokenizer, dataset)

    trainer.train()

    export(NAME, model, tokenizer, dataset)

if __name__ == "__main__":
    train.remote()
