import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, ingestion_status
from unittest.mock import patch, MagicMock, AsyncMock
import os

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_ingest_question_bank_directory_not_found(client):
    # If the directory doesn't exist, should return 404
    response = await client.post("/ingest-question-bank", params={"directory_path": "non_existent_folder"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_ingest_question_bank_success(client):
    # Reset ingestion_status
    ingestion_status["status"] = "idle"
    
    # Mocking os.path.exists to allow fake directory
    with patch("app.main.os.path.exists") as mock_exists, \
         patch("app.main.os.walk") as mock_walk, \
         patch("builtins.open", MagicMock()), \
         patch("app.main.parse_document") as mock_parse, \
         patch("app.main.extract_questions_ai") as mock_extract, \
         patch("app.main.process_question_images") as mock_proc, \
         patch("app.main.register_question") as mock_register:
         
        mock_exists.return_value = True
        # Mocking finding one file under "data/banco_questoes/2023-3"
        mock_walk.return_value = [
            ("data/banco_questoes/2023-3", [], ["prova-pluri-ELE-2.pdf"])
        ]
        mock_parse.return_value = ("Texto extraído", [b"img"])
        
        # Mock extracted question
        mock_question = MagicMock()
        mock_question.ano = None
        mock_question.model_dump.return_value = {"corpo": "Mock question"}
        mock_extract.return_value = [mock_question]
        mock_proc.return_value = mock_question
        mock_register.return_value = True
        
        # Call endpoint
        response = await client.post("/ingest-question-bank", params={"directory_path": "data/banco_questoes"})
        
        assert response.status_code == 200
        assert "started" in response.json()["message"]
        
        # Test status endpoint
        status_response = await client.get("/ingestion-status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] in ["running", "completed"]
