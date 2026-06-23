from google import genai
import os
from dotenv import load_dotenv

# Carrega o arquivo .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERRO: Não encontrei seu arquivo .env ou a variável GEMINI_API_KEY.")
else:
    try:
        # Na biblioteca nova, criamos o Client em vez de usar genai.configure()
        client = genai.Client(api_key=API_KEY)

        print("--- Buscando modelos disponíveis para sua API Key ---")

        modelos_encontrados = 0
        # O jeito novo de iterar sobre os modelos
        for m in client.models.list():
            # Mostra o modelo. O Gemini 1.5 e 2.0 geralmente suportam generate_content
            print(f"Modelo encontrado: {m.name}")
            modelos_encontrados += 1

        print("-----------------------------------------------------")

        if modelos_encontrados == 0:
            print("Nenhum modelo compatível foi encontrado. Isso pode ser um problema com a API Key.")
        else:
            print("Por favor, copie um dos nomes de modelo acima (ex: 'gemini-2.5-flash')")
            print("e cole no seu agente se quiser atualizar a versão.")

    except Exception as e:
        print(f"Ocorreu um erro ao listar os modelos: {e}")