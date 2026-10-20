from pathlib import Path
import sys

FILE = Path(r"C:\Users\dmaza\mcp-starter\developer_core_engine.py")

text = FILE.read_text(encoding="utf-8")

marker = 'if __name__ == "__main__":'

if marker not in text:
    text += r'''

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8010,
        log_level="info",
    )
'''

FILE.write_text(text, encoding="utf-8")

print("PATCH OK")
print(FILE)
