import torch
from transformers import AutoTokenizer, AutoModel

MODEL = "indobenchmark/indobert-base-p1"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModel.from_pretrained(MODEL)

text = "Pelayanan administrasi kependudukan sangat membantu masyarakat."

inputs = tokenizer(
    text,
    return_tensors="pt",
    truncation=True,
    padding=True
)

with torch.no_grad():
    outputs = model(**inputs)

print("Text:")
print(text)

print("\nInput shape:")
print(inputs["input_ids"].shape)

print("\nOutput shape:")
print(outputs.last_hidden_state.shape)

print("\nInference IndoBERT BERHASIL.")