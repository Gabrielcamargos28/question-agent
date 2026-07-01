import httpx
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

async def upload_image(image_bytes: bytes, token: Optional[str] = None) -> Optional[str]:
    """Uploads an image to the storage endpoint and returns the URL."""
    url = f"{settings.TARGET_API_BASE_URL}/controle-de-arquivos/enviar/"
    auth_token = token or settings.TARGET_API_TOKEN
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    files = {"image": ("image.png", image_bytes, "image/png")}
    
    logger.info(f"Uploading image file ({len(image_bytes)} bytes) to endpoint: '{url}'...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files)
            logger.info(f"Upload image response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            # The API returns the download path under the key "path" (or fallback to "url")
            path = data.get("path") or data.get("url")
            logger.info(f"Image upload successful. Path: '{path}'")
            return path
    except Exception as e:
        logger.error(f"Error uploading image to '{url}': {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"API Response: {e.response.text}")
        return None

async def register_question(question_json: Dict[str, Any], token: str) -> bool:
    """Sends the question JSON to the registration API."""
    url = f"{settings.TARGET_API_BASE_URL}/questao/criar-questao"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Detached entity fix: The Spring Boot backend's QuestaoService has a duplicate-saving bug.
    # It manually saves files in the 'arquivos' list and then saves the Questao entity,
    # which cascades the save operation back to the same files, causing a "detached entity passed to persist" error.
    # To fix this, we clear the 'arquivos' list in the JSON payload.
    # The backend will still correctly extract and save the images from the HTML body/alternatives
    # via its processarImagensDoHTML method.
    clean_payload = question_json.copy()
    clean_payload["arquivos"] = []
    if "alternativas" in clean_payload:
        clean_payload["alternativas"] = [
            {**alt, "arquivos": []} for alt in clean_payload["alternativas"]
        ]
        
    title = clean_payload.get("titulo", "Untitled")
    area = clean_payload.get("area", "N/A")
    logger.info(f"Registering question. Title: '{title}' | Area ID: {area} to: '{url}'...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=clean_payload)
            logger.info(f"Register question response status: {response.status_code}")
            response.raise_for_status()
            logger.info(f"Question '{title}' registered successfully!")
            return True
    except Exception as e:
        logger.error(f"Error registering question '{title}' to '{url}': {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"API Response: {e.response.text}")
        return False

async def list_disciplines_by_area(area_id: int, token: str) -> List[Dict[str, Any]]:
    """
    Lists disciplines and their subjects for a given area ID.
    Uses the /disciplina/listar-disciplinas-por-area endpoint.
    """
    url = f"{settings.TARGET_API_BASE_URL}/disciplina/listar-disciplinas-por-area"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Query parameters for GET request
    params = {
        "page": 0,
        "size": 100,
        "sort": "nome",
        "areaId": area_id
    }
    
    logger.info(f"Fetching disciplines from API: '{url}' for Area ID: {area_id}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            content = data.get("content", [])
            logger.info(f"Fetched {len(content)} disciplines for Area ID {area_id}.")
            return content
    except Exception as e:
        logger.error(f"Error fetching disciplines for area {area_id} from '{url}': {e}")
        if hasattr(e, 'response') and e.response:
             logger.error(f"API Response: {e.response.text}")
        return []
