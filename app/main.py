import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional
import json
from datetime import datetime

from app.core.config import settings
from app.services.document_parser import parse_document
from app.services.ai_extractor import extract_questions_ai
from app.services.api_client import upload_image, register_question

# Logging Configuration
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pluri Question Extraction Agent")

def log_iteration_context(message: str):
    """Writes iteration context logs to a local Markdown file."""
    with open(settings.ITERATIONS_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"### [{timestamp}] {message}\n\n")

def save_questions_locally(questions: List[dict]):
    """Saves the extracted question JSONs to a local Markdown file."""
    with open(settings.QUESTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(f"## Extraction at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for q in questions:
            f.write("```json\n")
            f.write(json.dumps(q, indent=2, ensure_ascii=False))
            f.write("\n```\n\n")

@app.on_event("startup")
async def startup_event():
    # Initialize files if they don't exist
    for file in [settings.ITERATIONS_FILE, settings.QUESTIONS_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                f.write(f"# {file.replace('.md', '').replace('_', ' ').capitalize()}\n\n")

@app.post("/extract-questions")
async def extract_questions(
    file: UploadFile = File(...),
    model: str = Form("gemini-2.0-flash"),
    limit: int = Form(5)
):
    """
    Main endpoint to extract questions from PDF/DOCX documents.
    Receives file via multipart/form-data.
    """
    log_iteration_context(f"Starting extraction for file: {file.filename} using model: {model}")
    
    try:
        # 1. Read file
        content = await file.read()
        text, images = parse_document(content, file.filename)
        
        # 2. AI Extraction
        questions_pydantic = await extract_questions_ai(text, model, limit)
        
        if not questions_pydantic:
            raise HTTPException(status_code=500, detail="Could not extract questions from the document.")
            
        # 3. Image Processing (If any)
        if images:
            log_iteration_context(f"Found {len(images)} images in the document.")
            # Note: Specific logic to link images to questions can be improved later
            
        # 4. Local Logging and API Registration
        questions_dict = [q.model_dump(mode='json') for q in questions_pydantic]
        save_questions_locally(questions_dict)
        
        registration_results = []
        for q in questions_dict:
            success = await register_question(q)
            registration_results.append(success)
            
        log_iteration_context(f"Extraction completed: {len(questions_dict)} questions processed.")
        
        return {
            "total_extracted": len(questions_dict),
            "questions": questions_dict,
            "api_registration_success": all(registration_results) if registration_results else False,
            "registration_details": registration_results
        }

    except Exception as e:
        logger.error(f"Error in extract-questions endpoint: {e}")
        log_iteration_context(f"FAILURE in extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
