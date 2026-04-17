import json
import logging
import os
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from app.models.schemas import QuestionCreate
from app.core.config import settings

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
        result = parser.parse(response.content)
        return result.questions

    except Exception as e:
        logger.error(f"Error in AI extraction: {e}")
        return []
