import json
import sys

import torch
from transformers import AutoTokenizer, AutoModel


MODEL = "indobenchmark/indobert-base-p1"


tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModel.from_pretrained(MODEL)
model.eval()


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state

    mask = attention_mask.unsqueeze(-1).expand(
        token_embeddings.size()
    ).float()

    return torch.sum(token_embeddings * mask, dim=1) / torch.clamp(
        mask.sum(dim=1),
        min=1e-9,
    )


def encode(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    embedding = mean_pooling(
        outputs,
        inputs["attention_mask"],
    )

    embedding = torch.nn.functional.normalize(
        embedding,
        p=2,
        dim=1,
    )

    return embedding[0]


def main():
    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        try:
            request = json.loads(line)

            text = request.get("text", "")

            if not isinstance(text, str):
                text = str(text)

            embedding = encode(text)

            result = {
                "ok": True,
                "model": MODEL,
                "engine": "indobert-local",
                "dimension": int(embedding.shape[0]),
                "embedding": embedding.tolist(),
            }

            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                ),
                flush=True,
            )

        except Exception as exc:
            result = {
                "ok": False,
                "engine": "indobert-local",
                "error": str(exc),
            }

            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()