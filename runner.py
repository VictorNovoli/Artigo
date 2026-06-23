import os
import time

# --- CONFIGURAÇÃO ---
SCRIPT_AGENTE = "agenteaspirador.py"  # Nome do seu arquivo principal
PASTA_IMAGENS = "cenarios_teste"      # Pasta com as imagens

def rodar_tudo():
    # 1. Pega todas as imagens da pasta
    try:
        arquivos = os.listdir(PASTA_IMAGENS)
    except FileNotFoundError:
        print(f"ERRO: A pasta '{PASTA_IMAGENS}' não existe.")
        return

    # Filtra só o que é imagem
    lista_imagens = [f for f in arquivos if f.endswith(('.png', '.jpg'))]

    if not lista_imagens:
        print("Nenhuma imagem encontrada!")
        return

    print(f"--- ENCONTRADAS {len(lista_imagens)} IMAGENS PARA TESTAR ---\n")

    # 2. Loop simples
    for imagem in lista_imagens:
        print(f"==========================================")
        print(f" TESTANDO: {imagem}")
        print(f"==========================================")
        
        # Monta o caminho: "cenarios_teste/imagem.png"
        caminho_imagem = os.path.join(PASTA_IMAGENS, imagem)
        
        # O comando mágico. As aspas duplas servem caso o nome tenha espaços.
        comando = f'python {SCRIPT_AGENTE} "{caminho_imagem}"'
        
        # Executa e mostra na tela imediatamente
        os.system(comando)
        
        print("\n--> Cenário finalizado. Aguardando 2s para o próximo...\n")
        time.sleep(2)

if __name__ == "__main__":
    rodar_tudo()