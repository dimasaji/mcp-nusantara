from pypdf import PdfReader, PdfWriter
import pymupdf
from PIL import Image
import io,json
buffer=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(buffer)
raw=buffer.getvalue()
with pymupdf.open(stream=raw,filetype='pdf') as document:
    result={'pypdf_pages':len(PdfReader(io.BytesIO(raw)).pages),'pymupdf_pages':len(document),'image_size':list(Image.new('RGB',(2,3)).size)}
assert result=={'pypdf_pages':1,'pymupdf_pages':1,'image_size':[2,3]}
print(json.dumps(result))
