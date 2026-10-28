class TextParser:
    def parse(self, content): return content
class MarkdownParser(TextParser): pass
class PDFParser(TextParser): pass
class DocumentParser(TextParser): pass
def parse_document(content, content_type="text/plain"): return content
PdfParser = PDFParser

Parser = TextParser
def get_parser(content_type='text/plain'):
    return TextParser()
