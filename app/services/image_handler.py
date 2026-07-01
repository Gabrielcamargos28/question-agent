import re
import logging
from typing import List, Dict, Any
from app.models.schemas import QuestionCreate, FileModel
from app.services.api_client import upload_image

logger = logging.getLogger(__name__)

async def process_question_images(
    question: QuestionCreate, 
    images: List[bytes], 
    token: str, 
    uploaded_cache: Dict[int, str]
) -> QuestionCreate:
    """
    Identifies image placeholders ([IMAGE_X]) in the question's text fields,
    uploads the corresponding image to the server, replaces the placeholders with 
    HTML <img> tags, and adds them to the question's 'arquivos' list.
    """
    logger.info(f"Processing image placeholders for question: '{question.titulo or 'Untitled'}'...")
    if not images:
        logger.warning("No images available in document. Stripping any remaining placeholders from question text...")
        # If no images are available, strip any remaining placeholders to keep clean text
        question.corpo = re.sub(r"\[IMAGE_\d+\]", "", question.corpo)
        if question.introducaoAlternativa:
            question.introducaoAlternativa = re.sub(r"\[IMAGE_\d+\]", "", question.introducaoAlternativa)
        for alt in question.alternativas:
            alt.corpo = re.sub(r"\[IMAGE_\d+\]", "", alt.corpo)
        return question

    async def get_uploaded_url(idx: int) -> str:
        """Helper to get cached or upload a new image."""
        if idx < 0 or idx >= len(images):
            logger.error(f"Image placeholder index {idx} is out of bounds (total images parsed: {len(images)}).")
            return ""
        if idx in uploaded_cache:
            logger.debug(f"Cache hit for image index {idx}: {uploaded_cache[idx]}")
            return uploaded_cache[idx]
        
        logger.info(f"Cache miss for image index {idx}. Initiating upload to storage API...")
        url = await upload_image(images[idx], token)
        if url:
            logger.info(f"Image {idx} uploaded successfully. URL returned: {url}")
            uploaded_cache[idx] = url
            return url
        logger.error(f"Failed to upload image {idx} to storage API.")
        return ""

    # 1. Process corpo
    body_placeholders = re.findall(r"\[IMAGE_(\d+)\]", question.corpo)
    if body_placeholders:
        logger.debug(f"Found body placeholders: {body_placeholders}")
    for img_idx_str in body_placeholders:
        idx = int(img_idx_str)
        url = await get_uploaded_url(idx)
        if url:
            img_tag = f'<p><img src="{url}" style="max-width: 100%; height: auto;"></p>'
            question.corpo = question.corpo.replace(f"[IMAGE_{idx}]", img_tag)
            # Add to files list if not already present
            if not any(f.url == url for f in question.arquivos):
                question.arquivos.append(FileModel(nome=f"image_{idx}.png", url=url))
                logger.info(f"Attached image {idx} to question files list.")
        else:
            question.corpo = question.corpo.replace(f"[IMAGE_{idx}]", "")

    # 2. Process introducaoAlternativa
    if question.introducaoAlternativa:
        intro_placeholders = re.findall(r"\[IMAGE_(\d+)\]", question.introducaoAlternativa)
        if intro_placeholders:
            logger.debug(f"Found introduction placeholders: {intro_placeholders}")
        for img_idx_str in intro_placeholders:
            idx = int(img_idx_str)
            url = await get_uploaded_url(idx)
            if url:
                img_tag = f'<p><img src="{url}" style="max-width: 100%; height: auto;"></p>'
                question.introducaoAlternativa = question.introducaoAlternativa.replace(f"[IMAGE_{idx}]", img_tag)
                if not any(f.url == url for f in question.arquivos):
                    question.arquivos.append(FileModel(nome=f"image_{idx}.png", url=url))
                    logger.info(f"Attached image {idx} to question files list (via introduction).")
            else:
                question.introducaoAlternativa = question.introducaoAlternativa.replace(f"[IMAGE_{idx}]", "")

    # 3. Process alternatives
    for alt_idx, alt in enumerate(question.alternativas):
        alt_placeholders = re.findall(r"\[IMAGE_(\d+)\]", alt.corpo)
        if alt_placeholders:
            logger.debug(f"Found alternative {alt_idx + 1} placeholders: {alt_placeholders}")
        for img_idx_str in alt_placeholders:
            idx = int(img_idx_str)
            url = await get_uploaded_url(idx)
            if url:
                img_tag = f'<p><img src="{url}" style="max-width: 100%; height: auto;"></p>'
                alt.corpo = alt.corpo.replace(f"[IMAGE_{idx}]", img_tag)
                if not any(f.url == url for f in alt.arquivos):
                    alt.arquivos.append(FileModel(nome=f"image_{idx}.png", url=url))
                    logger.info(f"Attached image {idx} to alternative {alt.posicao} files list.")
            else:
                alt.corpo = alt.corpo.replace(f"[IMAGE_{idx}]", "")

    logger.info(f"Finished processing images for question: '{question.titulo or 'Untitled'}'")
    return question
