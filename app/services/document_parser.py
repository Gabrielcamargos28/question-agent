import fitz  # PyMuPDF
from docx import Document
import io
import logging
import hashlib
from typing import List, Tuple

logger = logging.getLogger(__name__)

def parse_pdf(file_content: bytes, filename: str = "unknown") -> Tuple[str, List[bytes]]:
    """Extracts text and images from a PDF file, keeping them in visual order and deduplicating by content hash."""
    logger.info(f"Starting PDF parsing block-by-block for file: '{filename}'...")
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    images = []
    image_hashes = {}  # hash -> index
    
    for page_num, page in enumerate(doc):
        logger.debug(f"Processing PDF page {page_num + 1}/{len(doc)} for file '{filename}'...")
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:  # text block
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"] + " "
                    block_text += "\n"
                text += block_text + "\n"
            elif block["type"] == 1:  # image block
                img_bytes = block.get("image")
                if img_bytes:
                    img_hash = hashlib.md5(img_bytes).hexdigest()
                    if img_hash in image_hashes:
                        img_idx = image_hashes[img_hash]
                        text += f"\n[IMAGE_{img_idx}]\n"
                        logger.debug(f"Page {page_num + 1} of '{filename}': Duplicate image (seen at [IMAGE_{img_idx}]), referencing existing index.")
                    else:
                        img_idx = len(images)
                        image_hashes[img_hash] = img_idx
                        images.append(img_bytes)
                        text += f"\n[IMAGE_{img_idx}]\n"
                        logger.info(f"Page {page_num + 1} of '{filename}': Found new image, mapping to [IMAGE_{img_idx}] ({len(img_bytes)} bytes)")
            
    logger.info(f"Finished PDF parsing for file '{filename}'. Total text length: {len(text)} chars, Deduplicated images: {len(images)}")
    return text, images

def parse_docx(file_content: bytes, filename: str = "unknown") -> Tuple[str, List[bytes]]:
    """Extracts text and images from a DOCX file, keeping them in visual order and deduplicating by content hash."""
    logger.info(f"Starting DOCX parsing for file: '{filename}'...")
    doc = Document(io.BytesIO(file_content))
    text = ""
    images = []
    image_hashes = {}  # hash -> index
    
    for idx, para in enumerate(doc.paragraphs):
        para_text = para.text
        drawings = para._p.xpath('.//w:drawing')
        if drawings:
            logger.debug(f"Paragraph {idx} of '{filename}': Found {len(drawings)} drawing elements.")
            for drawing in drawings:
                blips = drawing.xpath('.//a:blip')
                for blip in blips:
                    embed = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if embed and embed in doc.part.related_parts:
                        part = doc.part.related_parts[embed]
                        img_bytes = part.blob
                        img_hash = hashlib.md5(img_bytes).hexdigest()
                        if img_hash in image_hashes:
                            img_idx = image_hashes[img_hash]
                            para_text += f"\n[IMAGE_{img_idx}]\n"
                            logger.debug(f"Paragraph {idx} of '{filename}': Duplicate image (seen at [IMAGE_{img_idx}]), referencing existing index.")
                        else:
                            img_idx = len(images)
                            image_hashes[img_hash] = img_idx
                            images.append(img_bytes)
                            para_text += f"\n[IMAGE_{img_idx}]\n"
                            logger.info(f"Paragraph {idx} of '{filename}': Found new image relation {embed}, mapping to [IMAGE_{img_idx}] ({len(img_bytes)} bytes)")
        text += para_text + "\n"
            
    logger.info(f"Finished DOCX parsing for file '{filename}'. Total text length: {len(text)} chars, Deduplicated images: {len(images)}")
    return text, images

def parse_document(file_content: bytes, filename: str) -> Tuple[str, List[bytes]]:
    """Identifies file type and calls the appropriate parser."""
    logger.info(f"Incoming document to parse: '{filename}'")
    if filename.lower().endswith(".pdf"):
        return parse_pdf(file_content, filename)
    elif filename.lower().endswith(".docx"):
        return parse_docx(file_content, filename)
    else:
        logger.error(f"Unsupported file format for file: '{filename}'")
        raise ValueError("Unsupported file format. Use .pdf or .docx")
