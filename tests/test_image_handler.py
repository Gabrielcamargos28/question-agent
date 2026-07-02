import pytest
from unittest.mock import patch, AsyncMock
from app.models.schemas import QuestionCreate, Alternative, FileModel
from app.services.image_handler import process_question_images

@pytest.mark.asyncio
async def test_process_question_images_success():
    # Setup mock question
    question = QuestionCreate(
        corpo="Pergunta com imagem: [IMAGE_0]",
        introducaoAlternativa="Introdução com imagem: [IMAGE_1]",
        alternativas=[
            Alternative(corpo="Alternativa 1 com imagem: [IMAGE_0]", correta=True, posicao=1),
            Alternative(corpo="Alternativa 2 limpa", correta=False, posicao=2)
        ],
        alternativaCorreta=1,
        arquivos=[]
    )
    
    # Mock images bytes (2 images)
    images = [b"fake_image_0_bytes", b"fake_image_1_bytes"]
    
    # Mock upload_image to return URLs
    with patch("app.services.image_handler.upload_image", new_callable=AsyncMock) as mock_upload:
        mock_upload.side_effect = ["http://api/img0.png", "http://api/img1.png"]
        
        uploaded_cache = {}
        processed_q = await process_question_images(
            question=question,
            images=images,
            token="test-token",
            uploaded_cache=uploaded_cache
        )
        
        # Verify upload_image calls
        assert mock_upload.call_count == 2
        mock_upload.assert_any_call(b"fake_image_0_bytes", "test-token")
        mock_upload.assert_any_call(b"fake_image_1_bytes", "test-token")
        
        # Verify cache is populated
        assert uploaded_cache[0] == "http://api/img0.png"
        assert uploaded_cache[1] == "http://api/img1.png"
        
        # Verify text replacements
        assert '<img src="http://api/img0.png"' in processed_q.corpo
        assert '[IMAGE_0]' not in processed_q.corpo
        assert '<img src="http://api/img1.png"' in processed_q.introducaoAlternativa
        assert '[IMAGE_1]' not in processed_q.introducaoAlternativa
        
        assert '<img src="http://api/img0.png"' in processed_q.alternativas[0].corpo
        assert '[IMAGE_0]' not in processed_q.alternativas[0].corpo
        assert "Alternativa 2 limpa" in processed_q.alternativas[1].corpo
        
        # Verify arquivos fields are populated
        assert len(processed_q.arquivos) == 2
        assert processed_q.arquivos[0].url == "http://api/img0.png"
        assert processed_q.arquivos[1].url == "http://api/img1.png"
        
        assert len(processed_q.alternativas[0].arquivos) == 1
        assert processed_q.alternativas[0].arquivos[0].url == "http://api/img0.png"
        assert len(processed_q.alternativas[1].arquivos) == 0

@pytest.mark.asyncio
async def test_process_question_images_no_images():
    question = QuestionCreate(
        corpo="Pergunta com imagem invalida: [IMAGE_0]",
        alternativas=[
            Alternative(corpo="Alternativa 1: [IMAGE_1]", correta=True, posicao=1)
        ],
        alternativaCorreta=1,
        arquivos=[]
    )
    
    # Empty images list
    processed_q = await process_question_images(
        question=question,
        images=[],
        token="test-token",
        uploaded_cache={}
    )
    
    # Placeholders should be stripped
    assert "[IMAGE_0]" not in processed_q.corpo
    assert "[IMAGE_1]" not in processed_q.alternativas[0].corpo
    assert len(processed_q.arquivos) == 0
