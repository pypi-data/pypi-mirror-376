import torch
from transformers import AutoModel, AutoTokenizer
from longdllm import adapt_for_long_context
import logging

# logging.basicConfig(level=logging.INFO)

# Load your model as usual
model = AutoModel.from_pretrained(
    "apple/DiffuCoder-7B-Instruct",
    torch_dtype=torch.float16,
    attn_implementation="flash_attention_2",
    trust_remote_code=True
)

model_path = "apple/DiffuCoder-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)


model = adapt_for_long_context(model, target_length=131072)
model = model.to("cuda").eval()

with open("./passkey-32k-idx-2.txt", "r") as f:
    query = f.read().strip()
prompt = f"""<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
{query.strip()}
<|im_end|>
<|im_start|>assistant
""" ## following the template of qwen; you can also use apply_chat_template function

TOKEN_PER_STEP = 1 # diffusion timesteps * TOKEN_PER_STEP = total new tokens

inputs = tokenizer(prompt, return_tensors="pt")
input_ids = inputs.input_ids.to(device="cuda")
attention_mask = inputs.attention_mask.to(device="cuda")
# import pdb; pdb.set_trace()

# Use the adapted model with long sequences
output = model.diffusion_generate(
    input_ids,
    attention_mask=attention_mask,
    max_new_tokens=10,
    output_history=True,
    return_dict_in_generate=True,
    steps=10,
    temperature=0.3,
    top_p=0.95,
    alg="entropy",
    alg_temp=0.,
)

generations = [
    tokenizer.decode(g[len(p) :].tolist())
    for p, g in zip(input_ids, output.sequences)
]

print(generations[0].split('<|dlm_pad|>')[0])