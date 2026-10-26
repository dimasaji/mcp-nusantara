#!/c/Users/dmaza/mcp-starter/nusantara-models/.venv/Scripts/python.exe
import json
import sys
import time

import torch
from transformers import AutoTokenizer, AutoModel


MODEL = "indobenchmark/indobert-base-p1"
MAX_LENGTH = 128


def log(data):
    print(
        json.dumps(data, ensure_ascii=False),
        file=sys.stderr,
        flush=True,
    )


# LOAD MODEL SEKALI
log({
    "event": "loading",
    "engine": "indobert-worker",
    "model": MODEL,
})


load_start = time.perf_counter()

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModel.from_pretrained(MODEL)

model.eval()

load_seconds = time.perf_counter() - load_start


log({
    "event": "ready",
    "engine": "indobert-worker",
    "model": MODEL,
    "dimension": int(model.config.hidden_size),
    "load_seconds": round(load_seconds, 3),
})


def mean_pooling(model_output, attention_mask):

    token_embeddings = model_output.last_hidden_state

    mask = attention_mask.unsqueeze(-1).expand(
        token_embeddings.size()
    ).float()

    summed = torch.sum(
        token_embeddings * mask,
        dim=1,
    )

    counts = torch.clamp(
        mask.sum(dim=1),
        min=1e-9,
    )

    return summed / counts


def encode(text):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
    )

    start = time.perf_counter()

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

    inference_seconds = time.perf_counter() - start

    return embedding[0], inference_seconds


def handle_request(request):

    text = request.get("text", "")

    if not isinstance(text, str):
        text = str(text)

    text = text.strip()

    if not text:
        return {
            "ok": False,
            "engine": "indobert-worker",
            "error": "text wajib diisi",
        }

    embedding, inference_seconds = encode(text)

    return {
        "ok": True,
        "engine": "indobert-worker",
        "model": MODEL,
        "dimension": int(embedding.shape[0]),
        "inference_seconds": round(
            inference_seconds,
            4,
        ),
        "text": text,
        "embedding": embedding.tolist(),
    }


def main():

    for line in sys.stdin:

        line = line.strip()

        if not line:
            continue

        try:

            request = json.loads(line)

            result = handle_request(request)

            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                ),
                flush=True,
            )

        except json.JSONDecodeError as exc:

            print(
                json.dumps(
                    {
                        "ok": False,
                        "engine": "indobert-worker",
                        "error": f"JSON tidak valid: {exc}",
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

        except Exception as exc:

            print(
                json.dumps(
                    {
                        "ok": False,
                        "engine": "indobert-worker",
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()