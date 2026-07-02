import os
import logging
import re
import traceback
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Optional, Annotated
import json
from datetime import datetime

from app.core.config import settings
from app.models.schemas import ExtractionResponse
from app.services.document_parser import parse_document
from app.services.ai_extractor import extract_questions_ai
from app.services.api_client import upload_image, register_question
from app.services.image_handler import process_question_images

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
        uploaded_cache = {}
        processed_questions = []
        for q_pydantic in questions_pydantic:
            if q_pydantic.fonte:
                q_pydantic.fonte = f"{q_pydantic.fonte} - {file.filename}"
            else:
                q_pydantic.fonte = file.filename
            processed_q = await process_question_images(q_pydantic, images, token, uploaded_cache)
            processed_questions.append(processed_q)
            
        # 4. Local Logging and API Registration
        questions_dict = [q.model_dump(mode='json') for q in processed_questions]
        save_questions_locally(questions_dict)
        
        registration_results = []
        for q in questions_dict:
            print("question: ", q)
            success = await register_question(q, token)
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

# Ingestion Status Global Store
ingestion_status = {
    "status": "idle",
    "current_file": "",
    "files_processed": 0,
    "total_files": 0,
    "questions_extracted": 0,
    "questions_registered": 0,
    "errors": [],
    "start_time": "",
    "end_time": ""
}

async def run_ingestion(directory_path: str, model: str, limit_per_file: int, token: str):
    global ingestion_status
    ingestion_status["status"] = "running"
    ingestion_status["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ingestion_status["errors"] = []
    ingestion_status["files_processed"] = 0
    ingestion_status["questions_extracted"] = 0
    ingestion_status["questions_registered"] = 0
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    questions_dir = os.path.dirname(settings.QUESTIONS_FILE)
    if questions_dir:
        os.makedirs(questions_dir, exist_ok=True)
    log_file = "logs/ingestion_log.md"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n# Ingestion Started at {ingestion_status['start_time']}\n")
        f.write(f"- Directory: `{directory_path}`\n")
        f.write(f"- Model: `{model}`\n")
        f.write(f"- Limit per file: {limit_per_file}\n\n")

    try:
        # Find files
        files_to_process = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.pdf', '.docx')):
                    files_to_process.append(os.path.join(root, file))
                    
        ingestion_status["total_files"] = len(files_to_process)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Found {len(files_to_process)} files to process.\n\n")
            f.write("| File | Year | Extracted | Registered | Status |\n")
            f.write("|------|------|-----------|------------|--------|\n")

        for filepath in files_to_process:
            filename = os.path.basename(filepath)
            ingestion_status["current_file"] = filename
            
            # Extract year from parent folder name
            parent_folder = os.path.basename(os.path.dirname(filepath))
            year_match = re.search(r"(\d{4})", parent_folder)
            ano = int(year_match.group(1)) if year_match else None
            
            try:
                # Read file content
                with open(filepath, "rb") as file_obj:
                    content = file_obj.read()
                    
                # 1. Parse document
                text, images = parse_document(content, filename)
                
                # 2. AI Extraction
                questions_pydantic = await extract_questions_ai(text, model, limit_per_file, token)
                
                extracted_count = len(questions_pydantic)
                ingestion_status["questions_extracted"] += extracted_count
                
                # 3. Image processing and registration
                registered_count = 0
                if questions_pydantic:
                    uploaded_cache = {}
                    processed_questions = []
                    for q_pydantic in questions_pydantic:
                        # Programmatically set year
                        if ano:
                            q_pydantic.ano = ano
                            
                        # Concatenate filename to fonte
                        if q_pydantic.fonte:
                            q_pydantic.fonte = f"{q_pydantic.fonte} - {filename}"
                        else:
                            q_pydantic.fonte = filename

                        # Process images
                        processed_q = await process_question_images(q_pydantic, images, token, uploaded_cache)
                        processed_questions.append(processed_q)
                        
                    # Save and register
                    questions_dict = [q.model_dump(mode='json') for q in processed_questions]
                    save_questions_locally(questions_dict)
                    
                    for q in questions_dict:
                        success = await register_question(q, token)
                        if success:
                            registered_count += 1
                            ingestion_status["questions_registered"] += 1
                            
                # Log file result
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"| `{filename}` | {ano or 'N/A'} | {extracted_count} | {registered_count} | Success |\n")
                    
            except Exception as file_ex:
                err_msg = f"Error processing {filename}: {str(file_ex)}"
                logger.error(err_msg)
                ingestion_status["errors"].append(err_msg)
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"| `{filename}` | {ano or 'N/A'} | 0 | 0 | Failed: {str(file_ex)} |\n")
                    
            ingestion_status["files_processed"] += 1
            
        ingestion_status["status"] = "completed"
        
    except Exception as ex:
        ingestion_status["status"] = "failed"
        ingestion_status["errors"].append(traceback.format_exc())
        
    ingestion_status["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Write final summary to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n## Ingestion Summary ({ingestion_status['status']})\n")
        f.write(f"- End Time: `{ingestion_status['end_time']}`\n")
        f.write(f"- Files Processed: {ingestion_status['files_processed']}/{ingestion_status['total_files']}\n")
        f.write(f"- Questions Extracted: {ingestion_status['questions_extracted']}\n")
        f.write(f"- Questions Registered: {ingestion_status['questions_registered']}\n")
        if ingestion_status["errors"]:
            f.write("\n### Errors Encountered:\n")
            for err in ingestion_status["errors"]:
                f.write(f"- {err}\n")
        f.write("\n---\n")
        
    log_iteration_context(f"Ingestion completed. Files: {ingestion_status['files_processed']}, Extracted: {ingestion_status['questions_extracted']}, Registered: {ingestion_status['questions_registered']}")

@app.post(
    "/ingest-question-bank",
    summary="Ingest educational questions database",
    description="Asynchronously scans directories under the specified path, extracts questions from all PDF/DOCX files (associating the correct year from folder name), uploads and maps images inside tags, and registers questions to the target API.",
    tags=["Ingestion"]
)
async def ingest_question_bank(
    background_tasks: BackgroundTasks,
    directory_path: str = "data/banco_questoes",
    model: str = "gemini-2.5-flash-lite",
    limit_per_file: int = 5,
    token: str = ""
):
    if ingestion_status["status"] == "running":
        raise HTTPException(status_code=400, detail="Ingestion is already running.")
        
    if not os.path.exists(directory_path):
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found.")
        
    background_tasks.add_task(
        run_ingestion,
        directory_path=directory_path,
        model=model,
        limit_per_file=limit_per_file,
        token=token
    )
    
    return {
        "message": "Question bank ingestion started in the background.",
        "log_file": "logs/ingestion_log.md"
    }

@app.get(
    "/ingestion-status",
    summary="Get current question bank ingestion status",
    description="Returns current status of the background ingestion process.",
    tags=["Ingestion"]
)
async def get_ingestion_status():
    return ingestion_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
