from pathlib import Path

path = Path(r".\app\knowledge\parser.py")
text = path.read_text(encoding="utf-8")

old = '''    def parse(self, content: Union[str, bytes], **kwargs: Any) -> str:
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return str(content)
'''

new = '''    def parse(self, content: Union[str, bytes], **kwargs: Any) -> str:
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")

        value = str(content)

        # Jika string merupakan path file lokal,
        # baca isi file tersebut.
        path = Path(value)

        if path.is_file():
            return path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        return value
'''

if old not in text:
    print("BLOK TEXTPARSER TIDAK DITEMUKAN")
    raise SystemExit(1)

path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("TEXTPARSER FILE READER BERHASIL")
