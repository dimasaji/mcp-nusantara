from __future__ import annotations

from typing import Any, Union


class TextParser:
    """Parser untuk TXT dan teks biasa."""

    def parse(self, content: Union[str, bytes], **kwargs: Any) -> str:
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")

        # API content is literal data, never an implicit local file reference.
        return str(content)


class MarkdownParser(TextParser):
    """Parser Markdown."""

    pass


class PDFParser(TextParser):
    """Parser PDF menggunakan pypdf."""

    def parse(self, content: Union[str, bytes], **kwargs: Any) -> str:
        if not isinstance(content, bytes):
            raise ValueError("PDF harus berupa bytes, bukan path file lokal")
        data = content

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "Library pypdf belum terpasang. "
                "Jalankan: pip install pypdf"
            ) from exc

        import io

        reader = PdfReader(io.BytesIO(data))
        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())

        return "\n\n".join(pages)


class DOCXParser(TextParser):
    """Parser Microsoft Word DOCX menggunakan python-docx."""

    def parse(self, content: Union[str, bytes], **kwargs: Any) -> str:
        if not isinstance(content, bytes):
            raise ValueError("DOCX harus berupa bytes, bukan path file lokal")
        data = content

        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError(
                "Library python-docx belum terpasang. "
                "Jalankan: pip install python-docx"
            ) from exc

        import io

        document = Document(io.BytesIO(data))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)


class DocumentParser(TextParser):
    """
    Parser utama yang memilih parser berdasarkan
    content_type atau ekstensi file.
    """

    def parse(
        self,
        content: Union[str, bytes],
        content_type: str = "text/plain",
        filename: str | None = None,
        **kwargs: Any,
    ) -> str:

        content_type = (content_type or "").lower().strip()
        filename = (filename or "").lower().strip()

        if (
            content_type == "application/pdf"
            or filename.endswith(".pdf")
        ):
            return PDFParser().parse(content, **kwargs)

        if (
            content_type
            in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            )
            or filename.endswith(".docx")
        ):
            return DOCXParser().parse(content, **kwargs)

        if (
            content_type in ("text/markdown", "text/x-markdown")
            or filename.endswith(".md")
            or filename.endswith(".markdown")
        ):
            return MarkdownParser().parse(content, **kwargs)

        return TextParser().parse(content, **kwargs)


def parse_document(
    content: Union[str, bytes],
    content_type: str = "text/plain",
    filename: str | None = None,
) -> str:
    """Convenience function untuk parsing dokumen."""

    return DocumentParser().parse(
        content,
        content_type=content_type,
        filename=filename,
    )


PdfParser = PDFParser
DocxParser = DOCXParser
Parser = TextParser


def get_parser(
    content_type: str = "text/plain",
    filename: str | None = None,
):
    """Mengembalikan parser berdasarkan tipe dokumen."""

    content_type = (content_type or "").lower()
    filename = (filename or "").lower()

    if content_type == "application/pdf" or filename.endswith(".pdf"):
        return PDFParser()

    if (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or filename.endswith(".docx")
    ):
        return DOCXParser()

    if content_type in ("text/markdown", "text/x-markdown") or filename.endswith(
        (".md", ".markdown")
    ):
        return MarkdownParser()

    return TextParser()
