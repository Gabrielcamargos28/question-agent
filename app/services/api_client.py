import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

async def upload_image(image_bytes: bytes) -> Optional[str]:
    """Uploads an image to the storage endpoint and returns the URL."""
    url = f"{settings.TARGET_API_BASE_URL}/controle-de-arquivos/enviar/"
    headers = {"Authorization": f"Bearer {settings.TARGET_API_TOKEN}"}
    files = {"image": ("image.png", image_bytes, "image/png")}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files)
            response.raise_for_status()
            data = response.json()
            return data.get("url")
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return None

async def register_question(question_json: Dict[str, Any], token: str) -> bool:
    """Sends the question JSON to the registration API."""
    url = f"{settings.TARGET_API_BASE_URL}/questao/criar-questao"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=question_json)
            response.raise_for_status()
            logger.info("Question registered successfully!")
            return True
    except Exception as e:
        logger.error(f"Error registering question: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"API Response: {e.response.text}")
        return False
