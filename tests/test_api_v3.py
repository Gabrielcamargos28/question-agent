import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import os
from unittest.mock import patch, MagicMock
from app.models.schemas import QuestionBase, Alternative

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_read_main(client):
    # Tests if the openapi.json is accessible (Swagger documentation check)
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Pluri Question Extraction Agent"

@pytest.mark.asyncio
async def test_extract_questions_no_file(client):
    # Tests the endpoint without a file
    response = await client.post("/extract-questions")
    assert response.status_code == 422 # Validation Error

@pytest.fixture
def mock_questions():
    return [
        QuestionBase(
            corpo="Qual a capital da França?",
            titulo="Geografia",
            alternativas=[
                Alternative(corpo="Paris", correta=True, posicao=1),
                Alternative(corpo="Londres", correta=False, posicao=2)
            ],
            alternativaCorreta=1
        )
    ]

@pytest.mark.asyncio
async def test_extract_questions_success(client, mock_questions):
    # Mocking the AI extraction and API registration to avoid real API calls and costs
    with patch("app.main.parse_document") as mock_parse, \
         patch("app.main.extract_questions_ai") as mock_ai, \
         patch("app.main.register_question") as mock_register:
        
        mock_parse.return_value = ("Texto de exemplo", [])
        mock_ai.return_value = mock_questions
        mock_register.return_value = True

        # Create a dummy file
        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        data = {"model": "gemini-2.5-flash-lite", "limit": "1"}

        response = await client.post("/extract-questions", files=files, data=data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total_extracted"] == 1
        assert json_data["questions"][0]["corpo"] == "Qual a capital da França?"
        assert json_data["api_registration_success"] is True

@pytest.mark.asyncio
async def test_extract_questions_ai_failure(client):
    with patch("app.main.parse_document") as mock_parse, \
         patch("app.main.extract_questions_ai") as mock_ai:
        
        mock_parse.return_value = ("Texto de exemplo", [])
        mock_ai.return_value = [] # Simulate failure to extract

        files = {"file": ("test.pdf", b"content", "application/pdf")}
        response = await client.post("/extract-questions", files=files)

        assert response.status_code == 500
        assert "Could not extract questions" in response.json()["detail"]
