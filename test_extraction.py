import asyncio
from services.ai_extractor import extract_questions_ai
from services.document_parser import parse_document
import os

async def test_extraction():
    file_path = "prova-pluri-ELE-2.pdf"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    print(f"Parsing {file_path}...")
    with open(file_path, "rb") as f:
        content = f.read()
    
    text, images = parse_document(content, file_path)
    print(f"Extracted text length: {len(text)}")
    print(f"Extracted images count: {len(images)}")

    print("Extracting questions via AI (gemini-2.0-flash)...")
    questions = await extract_questions_ai(text, "gemini-2.0-flash", limit=2)
    
    if questions:
        print(f"Successfully extracted {len(questions)} questions!")
        for i, q in enumerate(questions):
            print(f"\nQuestion {i+1}: {q.titulo}")
            print(f"Corpo: {q.corpo[:100]}...")
    else:
        print("Failed to extract questions.")

if __name__ == "__main__":
    asyncio.run(test_extraction())
