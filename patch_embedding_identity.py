from pathlib import Path
from datetime import datetime
import shutil

path = Path("app/knowledge/indobert_embedding.py")
source = path.read_text(encoding="utf-8")

start_marker = '        embedding = result.get("embedding")'
end_marker = '        return [float(value) for value in embedding]'

if source.count(start_marker) != 1 or source.count(end_marker) != 1:
raise SystemExit("ABORT: target adapter tidak ditemukan secara unik.")

start = source.index(start_marker)
end = source.index(end_marker, start) + len(end_marker)

replacement = """        expected_model = "indobenchmark/indobert-base-p1"
actual_model = result.get("model")
actual_dimension = result.get("dimension")

```
    if actual_model != expected_model:
        raise RuntimeError("Identitas model IndoBERT tidak sesuai.")

    if isinstance(actual_dimension, bool) or actual_dimension != 768:
        raise RuntimeError("Dimensi yang dilaporkan worker IndoBERT tidak sesuai.")

    embedding = result.get("embedding")
    if not isinstance(embedding, list):
        raise RuntimeError("Response IndoBERT tidak memiliki embedding yang valid.")

    if len(embedding) != actual_dimension:
        raise RuntimeError("Dimensi vektor IndoBERT tidak sesuai dengan metadata.")

    try:
        vector = [float(value) for value in embedding]
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError("Vektor embedding IndoBERT tidak valid.") from exc

    if not all(math.isfinite(value) for value in vector):
        raise RuntimeError("Vektor embedding IndoBERT mengandung nilai non-finite.")

    return vector"""
```

updated = source[:start] + replacement + source[end:]

if updated == source or "import math" not in updated:
raise SystemExit("ABORT: hasil patch tidak valid.")

backup = path.with_name(
path.name + ".bak-identity-" + datetime.now().strftime("%Y%m%d-%H%M%S")
)
shutil.copy2(path, backup)
path.write_text(updated, encoding="utf-8", newline="")

print("PATCH OK: validasi identitas ditambahkan.")
print("BACKUP:", backup)
