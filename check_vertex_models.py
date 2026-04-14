import os
from google.cloud import aiplatform
from config import settings

def list_models():
    print(f"--- Diagnóstico Vertex AI ---")
    print(f"Projeto: {settings.GOOGLE_CLOUD_PROJECT or 'Padrão do JSON'}")
    print(f"Região: {settings.GOOGLE_CLOUD_LOCATION}")
    print(f"Credentials: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
    
    try:
        aiplatform.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION
        )
        
        print("\nVerificando modelos disponíveis...")
        # Nota: Listar modelos de fundação requer permissões específicas
        # Vamos tentar inicializar um modelo para ver o erro real
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel("gemini-1.5-flash")
        print("API Vertex AI parece estar respondendo corretamente.")
        
    except Exception as e:
        print(f"\nERRO DETECTADO: {e}")
        if "Vertex AI API has not been used" in str(e) or "disabled" in str(e).lower():
            print("\n>>> AÇÃO NECESSÁRIA: Habilite a 'Vertex AI API' no Console do Google Cloud.")
            print(f">>> Link: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={settings.GOOGLE_CLOUD_PROJECT or 'seu-projeto'}")

if __name__ == "__main__":
    list_models()
