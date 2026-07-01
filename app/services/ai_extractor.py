import logging
import os
from datetime import datetime
from typing import List

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from pydantic import BaseModel

from app.core.config import settings
from app.models.schemas import QuestionCreate
from app.services.api_client import list_disciplines_by_area

logger = logging.getLogger(__name__)

# Set Google Application Credentials if configured
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

class QuestionList(BaseModel):
    questions: List[QuestionCreate]

# Configuration of the Parser to force structured output
parser = PydanticOutputParser(pydantic_object=QuestionList)

AREA_DETECTION_PROMPT = """
Analyze the following text and identify which educational area it belongs to.
Choose the MOST APPROPRIATE area ID from this list:
* 7: ADMINISTRAÇÃO / TÉCNICA ADMINISTRAÇÃO / ADM
* 1: ATUALIDADES / ATU
* 2: CIÊNCIAS DA NATUREZA / NAT
* 8: CONTABILIDADE / TÉCNICA CONTABILIDADE / CON
* 9: ELETRÔNICA / TÉCNICA ELETRÔNICA / ELE
* 3: HUMANAS / CIÊNCIAS HUMANAS / HUM
* 10: INFORMÁTICA / TÉCNICA INFORMÁTICA / INF
* 4: LINGUAGENS / CÓDIGOS E TECNOLOGIAS / LNG
* 6: REDAÇÃO / RED

If there are multiple areas, list them separated by commas.
RETURN ONLY THE ID(S), NOTHING ELSE.

TEXT:
{text}
"""

PROMPT_TEMPLATE = """
You are an expert in education and data processing. 
Your task is to extract questions from raw text originating from PDF or DOCX documents.

We have already identified that the document likely belongs to the following Area IDs: {detected_areas}

I will provide a list of available Disciplines and Subjects for these areas. 
You MUST use the IDs from this list to populate `disciplinas` and `assuntos`.
Even though they are arrays, you should usually pick the ONE best fit for each.

AVAILABLE CONTEXT (Disciplines and Subjects):
{context}

INSTRUCTIONS:
1. Analyze the text and identify the questions.
2. Each question must contain: 
   - `titulo` (title based in question body text)
   - `corpo`: (String) The main text of the question. Wrap the text in HTML paragraphs using `<p>` tags. For example: `<p>Question text here...</p>`. If there are image placeholders like `[IMAGE_X]` in the raw text, preserve them exactly inside or between the `<p>` tags (e.g., `<p>[IMAGE_0]</p>`).
   - `alternativas` (list of alternatives)
   - `alternativaCorreta` (index of the correct alternative)
   - `fonte`: (String) The specific source, exam name, or origin identified in the question text (e.g., "ENEM 2023", "Vestibular UNICAMP 2022", "Questão 15"). Do not leave this empty if there is any indication of origin in the text.
   - `dificuldade`: (String) Difficulty level. Must be one of: FACIL, MEDIA, DIFICIL.
   - `area`: (Integer) The ID of the area this question belongs to. Choose from the detected areas ({detected_areas}) or from this table:
     * 7: ADMINISTRAÇÃO / TÉCNICA ADMINISTRAÇÃO / ADM
     * 1: ATUALIDADES / ATU
     * 2: CIÊNCIAS DA NATUREZA / NAT
     * 8: CONTABILIDADE / TÉCNICA CONTABILIDADE / CON
     * 9: ELETRÔNICA / TÉCNICA ELETRÔNICA / ELE
     * 3: HUMANAS / CIÊNCIAS HUMANAS / HUM
     * 10: INFORMÁTICA / TÉCNICA INFORMÁTICA / INF
     * 4: LINGUAGENS / CÓDIGOS E TECNOLOGIAS / LNG
     * 6: REDAÇÃO / RED
   - `disciplinas`: (List[Integer]) The ID of the discipline from the context above that best matches the question.
   - `assuntos`: (List[Integer]) The ID of the subject from the context above that best matches the question.
3. Each alternative must contain:
   - `corpo`: (String) The text content of the alternative. Wrap it in HTML paragraphs/tags (e.g., `<p>Alternative text</p>`).
   - `correta` (boolean)
   - `posicao` (index starting at 1)
4. IMPORTANT: If there are image placeholders in the text like `[IMAGE_0]`, `[IMAGE_1]`, etc., you MUST keep those placeholders exactly as they are in the correct place inside the HTML (`corpo` or alternative's `corpo`). Do not remove or rename them.
5. The output MUST be a valid JSON following strictly the provided schema.
6. Extract a maximum of {limit} questions.

{format_instructions}

RAW DOCUMENT TEXT:
---
{document_text}
---

RETURN ONLY THE JSON:
"""

def save_prompt_log(prompt_text: str, model_name: str, task: str):
    """Saves the prompt to a central Markdown file for auditing."""
    prompt_file = "all_prompts.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not os.path.exists(prompt_file):
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write("# Project Prompt Audit Log\n\n")
            
    with open(prompt_file, "a", encoding="utf-8") as f:
        f.write(f"## [{timestamp}] Task: {task} | Model: {model_name}\n\n")
        f.write("### Prompt:\n")
        f.write("```text\n")
        f.write(prompt_text)
        f.write("\n```\n\n")
        f.write("---\n\n")

def log_token_usage(model_name: str, usage_metadata: dict, task: str = "Extraction"):
    """Calculates and logs the cost of the AI request."""
    input_tokens = usage_metadata.get("input_tokens", 0)
    output_tokens = usage_metadata.get("output_tokens", 0)
    total_tokens = usage_metadata.get("total_tokens", 0)
    
    # Identify the base model for pricing
    base_model = "gemini-1.5-flash"  # default
    for m in settings.MODEL_PRICING.keys():
        if m in model_name.lower():
            base_model = m
            break
            
    pricing = settings.MODEL_PRICING.get(base_model, settings.MODEL_PRICING["gemini-1.5-flash"])
    input_cost = (input_tokens / 1_000_000 * pricing["input"])
    output_cost = (output_tokens / 1_000_000 * pricing["output"])
    total_cost = input_cost + output_cost
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Updated table structure with more detail
    log_entry = (
        f"| {timestamp} | {task} | {model_name} | {input_tokens} | {output_tokens} | {total_tokens} | ${total_cost:.6f} |\n"
    )
    
    if not os.path.exists(settings.COSTS_FILE):
        with open(settings.COSTS_FILE, "w", encoding="utf-8") as f:
            f.write("# Token Usage and Costs\n\n")
            f.write("| Timestamp | Task | Model | Input | Output | Total | Cost (USD) |\n")
            f.write("|-----------|------|-------|-------|--------|-------|------------|\n")
            
    with open(settings.COSTS_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    logger.info(f"Task: {task} | Tokens: {total_tokens} | Cost: ${total_cost:.6f}")

def get_model(model_name: str):
    """Returns the AI model instance based on the name."""
    if "gemini" in model_name.lower():
        # If GOOGLE_APPLICATION_CREDENTIALS is set, prefer Vertex AI (GCP)
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            logger.info(f"Using Vertex AI for model {model_name} in {settings.GOOGLE_CLOUD_LOCATION} ({settings.GOOGLE_CLOUD_PROJECT or 'auto-project'}).")
            return ChatVertexAI(
                model_name=model_name,
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.GOOGLE_CLOUD_LOCATION,
                temperature=0.1
            )
        
        # Fallback to Google AI Studio (API Key)
        if not settings.GEMINI_API_KEY:
            raise ValueError("Neither GEMINI_API_KEY nor GOOGLE_APPLICATION_CREDENTIALS configured.")
            
        logger.info(f"Using Google AI Studio for model {model_name} with API Key.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1
        )
    elif "ollama" in model_name.lower() or "llama" in model_name.lower():
        return ChatOllama(
            model=model_name.replace("ollama-", ""),
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1
        )
    else:
        raise ValueError(f"Model {model_name} not supported.")

async def extract_questions_ai(text: str, model_name: str, limit: int = 5, token: str = None) -> List[QuestionCreate]:
    """Uses LLM to transform raw text into Question objects with area, discipline and subject correlation."""
    logger.info(f"Initiating AI extraction using model: '{model_name}' (limit: {limit} questions)...")
    model = get_model(model_name)
    
    # 1. Detect Area
    logger.info("Step 1: Detecting educational area from raw text...")
    area_detection_prompt = ChatPromptTemplate.from_template(AREA_DETECTION_PROMPT)
    area_input = area_detection_prompt.format_messages(text=text[:4000]) # Use first 4000 chars for detection
    
    # Log the prompt
    save_prompt_log(area_detection_prompt.format(text=text[:4000]), model_name, "Area Detection")
    
    try:
        logger.debug("Calling LLM for area detection...")
        area_response = await model.ainvoke(area_input)
        
        # Log token usage for area detection
        if hasattr(area_response, "usage_metadata") and area_response.usage_metadata:
            log_token_usage(model_name, area_response.usage_metadata, "Area Detection")
            
        area_ids_str = area_response.content.strip()
        logger.info(f"Detected areas: {area_ids_str}")
        
        # Parse area IDs
        area_ids = []
        for part in area_ids_str.split(","):
            try:
                # Try to find digits in case the model returns something like "Area: 10"
                import re
                match = re.search(r"\d+", part)
                if match:
                    area_ids.append(int(match.group()))
            except ValueError:
                continue
                
        # 2. Fetch Context from API
        context_text = "No specific context available."
        if area_ids and token:
            logger.info(f"Step 2: Fetching disciplines and subjects for area IDs: {area_ids} from target API...")
            all_disciplines = []
            for a_id in area_ids:
                logger.debug(f"Fetching disciplines for area ID: {a_id}...")
                disciplines = await list_disciplines_by_area(a_id, token)
                all_disciplines.extend(disciplines)
            
            logger.info(f"Fetched {len(all_disciplines)} disciplines in total from API.")
            if all_disciplines:
                context_parts = []
                for d in all_disciplines:
                    d_info = f"Discipline: {d['nome']} (ID: {d['id']})\nSubjects:\n"
                    for s in d.get("assuntos", []):
                        d_info += f"  - {s['nome']} (ID: {s['id']})\n"
                    context_parts.append(d_info)
                context_text = "\n".join(context_parts)
        else:
            logger.warning("Skipping step 2: No area IDs or auth token provided to fetch context.")
        
        # 3. Main Extraction (with Chunking if needed)
        chunk_size = 20000
        overlap = 3000
        
        if len(text) <= 25000:
            chunks = [text]
        else:
            chunks = []
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                if end >= len(text):
                    break
                start = end - overlap
        
        # Pre-build mapping dictionaries for empty discipline/subject fallbacks
        discipline_to_subject = {}
        global_discipline_id = None
        global_subject_id = None
        
        for d in all_disciplines:
            d_id = d.get("id")
            if d_id:
                if not global_discipline_id:
                    global_discipline_id = d_id
                subjects = d.get("assuntos", [])
                for s in subjects:
                    s_id = s.get("id")
                    if s_id:
                        if d_id not in discipline_to_subject:
                            discipline_to_subject[d_id] = s_id
                        if not global_subject_id:
                            global_subject_id = s_id
                            global_discipline_id = d_id
                            
        logger.info(f"Step 3: Preparing main prompt for question extraction. Text length: {len(text)}. Total chunks to process: {len(chunks)}.")
        
        all_extracted_questions = []
        seen_keys = set()
        
        import asyncio
        import re
        
        for idx, chunk in enumerate(chunks):
            # If we already reached the limit, stop processing further chunks
            if len(all_extracted_questions) >= limit:
                logger.info("Reached the extraction limit. Skipping remaining chunks.")
                break
                
            logger.info(f"Processing chunk {idx + 1}/{len(chunks)} (size: {len(chunk)} chars)...")
            
            # Adjust limit for this chunk to not exceed the overall limit
            chunk_limit = limit - len(all_extracted_questions)
            
            prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
            prompt_text = prompt.format(
                limit=chunk_limit,
                format_instructions=parser.get_format_instructions(),
                document_text=chunk,
                context=context_text,
                detected_areas=area_ids_str
            )
            
            # Log the prompt
            save_prompt_log(prompt_text, model_name, f"Question Extraction - Chunk {idx + 1}")
            
            input_data = prompt.format_messages(
                limit=chunk_limit,
                format_instructions=parser.get_format_instructions(),
                document_text=chunk,
                context=context_text,
                detected_areas=area_ids_str
            )
            
            logger.info(f"Invoking LLM ('{model_name}') for chunk {idx + 1}...")
            response = await model.ainvoke(input_data)
            
            # Log token usage for main extraction
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                log_token_usage(model_name, response.usage_metadata, f"Question Extraction - Chunk {idx + 1}")
                
            logger.info("Received response from LLM. Parsing structured JSON output...")
            try:
                result = parser.parse(response.content)
                chunk_questions = result.questions
                logger.info(f"Extracted {len(chunk_questions)} questions from chunk {idx + 1}.")
                
                # Apply fallback logic for empty disciplinas or assuntos to satisfy backend validation
                for q in chunk_questions:
                    if not q.disciplinas:
                        if global_discipline_id:
                            q.disciplinas = [global_discipline_id]
                            logger.info(f"Question '{q.titulo or 'Untitled'}': Empty 'disciplinas' list, fell back to default ID: {global_discipline_id}")
                    
                    if not q.assuntos:
                        assigned_subject = None
                        if q.disciplinas:
                            for d_id in q.disciplinas:
                                if d_id in discipline_to_subject:
                                    assigned_subject = discipline_to_subject[d_id]
                                    break
                        if not assigned_subject and global_subject_id:
                            assigned_subject = global_subject_id
                        
                        if assigned_subject:
                            q.assuntos = [assigned_subject]
                            logger.info(f"Question '{q.titulo or 'Untitled'}': Empty 'assuntos' list, fell back to default ID: {assigned_subject}")
                
                # De-duplicate questions based on a hash of their title/body
                added_count = 0
                for q in chunk_questions:
                    # Clean title/body of whitespace to create a robust key
                    key_text = q.titulo or q.corpo or ""
                    key = re.sub(r"\s+", "", key_text[:120]).lower()
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        all_extracted_questions.append(q)
                        added_count += 1
                    else:
                        logger.warning(f"Discarding duplicate question from overlap: '{q.titulo or 'Untitled'}'")
                        
                logger.info(f"Added {added_count} unique questions from chunk {idx + 1}.")
            except Exception as parse_err:
                logger.error(f"Error parsing LLM response for chunk {idx + 1}: {parse_err}")
                
            # Add a small delay between chunks to prevent 429 Rate Limit (TPM/RPM)
            if idx < len(chunks) - 1:
                logger.info("Sleeping for 2 seconds to respect rate limits...")
                await asyncio.sleep(2.0)
                
        logger.info(f"Successfully finished AI extraction. Total unique questions extracted: {len(all_extracted_questions)}")
        return all_extracted_questions[:limit]

    except Exception as e:
        logger.error(f"Error in AI extraction: {e}")
        return []
