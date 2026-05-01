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
   - `corpo` (question body text)
   - `alternativas` (list of alternatives)
   - `alternativaCorreta` (index of the correct alternative)
   - `fonte` (source)
   - `dificuldade` (difficulty: Fácil, Médio, Difícil)
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
   - `corpo` (text)
   - `correta` (boolean)
   - `posicao` (index starting at 0)
4. If there are image indications in the text (like [Figure 1] or similar references), keep that reference in the `corpo`.
5. The output MUST be a valid JSON following strictly the provided schema.
6. Extract a maximum of {limit} questions.

{format_instructions}

RAW DOCUMENT TEXT:
---
{document_text}
---

RETURN ONLY THE JSON:
"""

def log_token_usage(model_name: str, usage_metadata: dict):
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
    cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"| {timestamp} | {model_name} | {input_tokens} | {output_tokens} | {total_tokens} | ${cost:.6f} |\n"
    )
    
    if not os.path.exists(settings.COSTS_FILE):
        with open(settings.COSTS_FILE, "w", encoding="utf-8") as f:
            f.write("# Token Usage and Costs\n\n")
            f.write("| Timestamp | Model | Input | Output | Total | Cost (USD) |\n")
            f.write("|-----------|-------|-------|--------|-------|------------|\n")
            
    with open(settings.COSTS_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    logger.info(f"Tokens used: {total_tokens} (Cost: ${cost:.6f})")

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
    model = get_model(model_name)
    
    # 1. Detect Area
    area_detection_prompt = ChatPromptTemplate.from_template(AREA_DETECTION_PROMPT)
    area_input = area_detection_prompt.format_messages(text=text[:4000]) # Use first 4000 chars for detection
    
    try:
        area_response = await model.ainvoke(area_input)
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
            all_disciplines = []
            for a_id in area_ids:
                disciplines = await list_disciplines_by_area(a_id, token)
                all_disciplines.extend(disciplines)
            
            if all_disciplines:
                context_parts = []
                for d in all_disciplines:
                    d_info = f"Discipline: {d['nome']} (ID: {d['id']})\nSubjects:\n"
                    for s in d.get("assuntos", []):
                        d_info += f"  - {s['nome']} (ID: {s['id']})\n"
                    context_parts.append(d_info)
                context_text = "\n".join(context_parts)
        
        # 3. Main Extraction
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        
        input_data = prompt.format_messages(
            limit=limit,
            format_instructions=parser.get_format_instructions(),
            document_text=text,
            context=context_text,
            detected_areas=area_ids_str
        )
        
        response = await model.ainvoke(input_data)
        
        # Log token usage if metadata is available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            log_token_usage(model_name, response.usage_metadata)
            
        result = parser.parse(response.content)
        return result.questions

    except Exception as e:
        logger.error(f"Error in AI extraction: {e}")
        return []
