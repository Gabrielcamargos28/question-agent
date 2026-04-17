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

logger = logging.getLogger(__name__)

# Set Google Application Credentials if configured
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

class QuestionList(BaseModel):
    questions: List[QuestionCreate]

# Configuration of the Parser to force structured output
parser = PydanticOutputParser(pydantic_object=QuestionList)

PROMPT_TEMPLATE = """
You are an expert in education and data processing. 
Your task is to extract questions from raw text originating from PDF or DOCX documents.

INSTRUCTIONS:
1. Analyze the text and identify the questions.
2. Each question must contain: 
   - `titulo` (title)
   - `corpo` (question body text)
   - `alternativas` (list of alternatives)
   - `alternativaCorreta` (index of the correct alternative)
   - `fonte` (source)
   - `dificuldade` (difficulty: FACIL, MEDIA, DIFICIL)
   - `area`: (Long) Map the question content to the correct ID based on this table:
     * 7: ADMINISTRAÇÃO / TÉCNICA ADMINISTRAÇÃO / ADM
     * 1: ATUALIDADES / ATU
     * 2: CIÊNCIAS DA NATUREZA / NAT
     * 8: CONTABILIDADE / TÉCNICA CONTABILIDADE / CON
     * 9: ELETRÔNICA / TÉCNICA ELETRÔNICA / ELE
     * 3: HUMANAS / CIÊNCIAS HUMANAS / HUM
     * 10: INFORMÁTICA / TÉCNICA INFORMÁTICA / INF
     * 4: LINGUAGENS / CÓDIGOS E TECNOLOGIAS / LNG
     * 6: REDAÇÃO / RED
)
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

async def extract_questions_ai(text: str, model_name: str, limit: int = 5) -> List[QuestionCreate]:
    """Uses LLM to transform raw text into Question objects."""
    model = get_model(model_name)
    
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    
    # Prepare the input for the model
    input_data = prompt.format_messages(
        limit=limit,
        format_instructions=parser.get_format_instructions(),
        document_text=text
    )
    
    try:
        response = await model.ainvoke(input_data)
        
        # Log token usage if metadata is available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            log_token_usage(model_name, response.usage_metadata)
            
        result = parser.parse(response.content)
        return result.questions

    except Exception as e:
        logger.error(f"Error in AI extraction: {e}")
        return []
