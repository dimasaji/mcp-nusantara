"""Retain each unchanged baseline line's original newline and BOM.

Only files explicitly patched by this task are written. No broad formatting.
"""
from pathlib import Path
from difflib import SequenceMatcher

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
for reference in OUT.glob("*.before"):
    target = ROOT / reference.name.removesuffix(".before").replace("__", "/")
    before = reference.read_bytes()
    current = target.read_bytes()
    original = before.decode("utf-8-sig").splitlines(keepends=True)
    updated = current.decode("utf-8-sig").splitlines(keepends=True)
    strip = lambda line: line.rstrip("\r\n")
    matcher = SequenceMatcher(a=[strip(line) for line in original],
                              b=[strip(line) for line in updated], autojunk=False)
    output = []
    for operation, left, right, start, end in matcher.get_opcodes():
        if operation == "equal":
            output.extend(original[left:right])
        else:
            neighbor = original[min(left, len(original) - 1)]
            newline = "\r\n" if neighbor.endswith("\r\n") else "\n"
            output.extend(strip(line) + (newline if line.endswith("\n") else "")
                          for line in updated[start:end])
    content = "".join(output).encode("utf-8")
    if before.startswith(b"\xef\xbb\xbf"):
        content = b"\xef\xbb\xbf" + content
    if content != current:
        target.write_bytes(content)
