import torch
from transformers import AutoModel, AutoTokenizer
from longdllm import adapt_for_long_context
import logging

# logging.basicConfig(level=logging.INFO)

# Load your model as usual
model_path = "GSAI-ML/LLaDA-8B-Instruct"
model = AutoModel.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    trust_remote_code=True
)

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)


model = adapt_for_long_context(model, target_length=131072)
model = model.to("cuda").eval()

with open("./passkey-32k-idx-2.txt", "r") as f:
    query = f.read().strip()

# Apply chat template for instruct model
m = [{"role": "user", "content": query}]
formatted_prompt = tokenizer.apply_chat_template(m, add_generation_prompt=True, tokenize=False)

inputs = tokenizer(formatted_prompt, return_tensors="pt")
input_ids = inputs.input_ids.to(device="cuda")
attention_mask = inputs.attention_mask.to(device="cuda")
# import pdb; pdb.set_trace()

# Use the adapted model with long sequences
output = model.diffusion_generate(
    input_ids,
    attention_mask=attention_mask,
    steps=10,
    gen_length=10,
    block_length=10,
    temperature=0.,
    cfg_scale=0.0,
    remasking='low_confidence',
)

response = tokenizer.batch_decode(output[:, input_ids.shape[1]:], skip_special_tokens=True)[0]

print(response)
