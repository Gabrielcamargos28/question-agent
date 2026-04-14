import asyncio
import os
import json
from services.document_parser import parse_document
from services.ai_extractor import extract_questions_ai
from config import settings

async def main():
    # Caminho do arquivo de prova
    pdf_path = "prova-pluri-ELE-2.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Erro: Arquivo {pdf_path} não encontrado.")
        return

    print(f"--- Lendo o arquivo: {pdf_path} ---")
    with open(pdf_path, "rb") as f:
        file_content = f.read()
    
    # Extrai o texto do PDF
    text, images = parse_document(file_content, pdf_path)
    print(f"Texto extraído ({len(text)} caracteres).")
    
    # Define o modelo (pode ser gemini-1.5-pro, gemini-1.5-flash, etc)
    model_name = "gemini-2.5-flash-lite"
    
    print(f"--- Chamando a IA ({model_name}) ---")
    try:
        # Extrai no máximo 3 questões para teste
        questions = await extract_questions_ai(text, model_name=model_name, limit=3)
        
        if questions:
            print(f"Sucesso! {len(questions)} questões extraídas:")
            for i, q in enumerate(questions):
                print(f"\nQuestão {i+1}: {q.titulo}")
                print(f"Corpo: {q.corpo[:100]}...")
                print(f"Alternativas: {len(q.alternativas)}")
                for alt in q.alternativas:
                    status = "[X]" if alt.correta else "[ ]"
                    print(f"  {status} {alt.corpo}")
        else:
            print("Nenhuma questão foi extraída. Verifique suas credenciais no .env.")
            
    except Exception as e:
        print(f"Erro na extração: {e}")

if __name__ == "__main__":
    asyncio.run(main())
