import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional, Annotated
import json
from datetime import datetime

from app.core.config import settings
from app.models.schemas import ExtractionResponse
from app.services.document_parser import parse_document
from app.services.ai_extractor import extract_questions_ai
from app.services.api_client import upload_image, register_question

# Logging Configuration
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

description = """
Pluri Question Extraction Agent API helps you extract educational questions from PDF and DOCX documents using AI.

## Endpoints

* **Extract Questions**: Upload a document and get a structured list of questions ready for registration.
"""

app = FastAPI(
    title="Pluri Question Extraction Agent",
    description=description,
    version="1.0.0",
    contact={
        "name": "Pluri Education",
        "url": "https://pluriedu.com.br",
    },
)

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
    for file in [settings.ITERATIONS_FILE, settings.QUESTIONS_FILE, settings.COSTS_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                f.write(f"# {file.replace('.md', '').replace('_', ' ').split('/')[-1].capitalize()}\n\n")

@app.post(
    "/extract-questions",
    summary="Extract questions from a document",
    description="Reads a PDF or DOCX file, uses AI to identify questions and alternatives, and optionally registers them in the target API.",
    tags=["Extraction"],
    response_model=ExtractionResponse
)
async def extract_questions(
    file: Annotated[UploadFile, File(description="The document (PDF or DOCX) to extract questions from")],
    model: Annotated[str, Form(description="The AI model to use for extraction")] = "gemini-2.5-flash-lite",
    limit: Annotated[int, Form(description="Maximum number of questions to extract")] = 5,
    token: Annotated[str, Form(description="Optional authentication token for the target API")] = ""
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
        questions_pydantic = await extract_questions_ai(text, model, limit, token)
        
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
            print("question: ", q)
            success = await register_question(q,token)
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
