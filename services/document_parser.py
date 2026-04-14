import fitz  # PyMuPDF
from docx import Document
import io
from typing import List, Tuple

def parse_pdf(file_content: bytes) -> Tuple[str, List[bytes]]:
    """Extracts text and images from a PDF file."""
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    images = []
    
    for page in doc:
        text += page.get_text()
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            images.append(image_bytes)
            
    return text, images

def parse_docx(file_content: bytes) -> Tuple[str, List[bytes]]:
    """Extracts text and images from a DOCX file."""
    doc = Document(io.BytesIO(file_content))
    text = ""
    images = []
    
    for para in doc.paragraphs:
        text += para.text + "\n"
        
    # Extract images from DOCX
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            images.append(rel.target_part.blob)
            
    return text, images

def parse_document(file_content: bytes, filename: str) -> Tuple[str, List[bytes]]:
    """Identifies file type and calls the appropriate parser."""
    if filename.lower().endswith(".pdf"):
        return parse_pdf(file_content)
    elif filename.lower().endswith(".docx"):
        return parse_docx(file_content)
    else:
        raise ValueError("Unsupported file format. Use .pdf or .docx")
