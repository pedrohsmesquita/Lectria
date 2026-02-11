"""
Script de teste para upload de vídeo
Demonstra como testar o endpoint /videos/upload

IMPORTANTE: Antes de executar, você precisa:
1. Ter o servidor rodando (uvicorn main:app --reload)
2. Ter criado uma conta de usuário
3. Ter criado um livro (book)
4. Ter um arquivo de vídeo de teste
"""

import requests
import json

# Configuração
BASE_URL = "http://localhost:8000"
TEST_VIDEO_PATH = "test_video.mp4"  # Substitua pelo caminho do seu vídeo de teste

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_step(step_number: int, description: str):
    """Print formatted step"""
    print(f"\n{BLUE}{'='*60}")
    print(f"ETAPA {step_number}: {description}")
    print(f"{'='*60}{RESET}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


# =============================================================================
# ETAPA 1: Registrar usuário (ou fazer login se já existe)
# =============================================================================
print_step(1, "Autenticação - Registrar ou fazer login")

# Tentar registrar novo usuário
register_data = {
    "full_name": "Usuário Teste",
    "email": "teste@lectria.com",
    "password": "senha123"
}

response = requests.post(f"{BASE_URL}/auth/register", json=register_data)

if response.status_code == 201:
    print_success("Usuário registrado com sucesso")
    auth_response = response.json()
    access_token = auth_response["access_token"]
    user_id = auth_response["user"]["id"]
    print(f"Token recebido: {access_token[:30]}...")
    print(f"User ID: {user_id}")
elif response.status_code == 409:
    print("Usuário já existe, fazendo login...")
    
    # Fazer login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print_success("Login realizado com sucesso")
        auth_response = response.json()
        access_token = auth_response["access_token"]
        user_id = auth_response["user"]["id"]
        print(f"Token recebido: {access_token[:30]}...")
        print(f"User ID: {user_id}")
    else:
        print_error(f"Erro no login: {response.text}")
        exit(1)
else:
    print_error(f"Erro ao registrar: {response.text}")
    exit(1)


# =============================================================================
# ETAPA 2: Criar um livro (Book)
# =============================================================================
print_step(2, "Criar livro para associar o vídeo")

# Nota: Esta rota ainda não foi implementada, então precisamos criar manualmente
# Por enquanto, vamos simular que temos um book_id
# Em produção, você faria:
# book_data = {
#     "title": "Fundamentos de Python",
#     "author": "Usuário Teste"
# }
# headers = {"Authorization": f"Bearer {access_token}"}
# response = requests.post(f"{BASE_URL}/books", json=book_data, headers=headers)

print("⚠️  Endpoint de criação de livros ainda não implementado")
print("Para testar, você precisa criar um livro manualmente no banco de dados:")
print(f"""
-- SQL para criar um livro de teste:
INSERT INTO books (id, author_profile_id, title, author, status)
VALUES (
    gen_random_uuid(),  -- ou use um UUID específico
    '{user_id}',
    'Livro de Teste',
    'Usuário Teste',
    'PENDING'
);

-- Para obter o UUID do livro criado:
SELECT id FROM books WHERE author_profile_id = '{user_id}' ORDER BY created_at DESC LIMIT 1;
""")

# Solicitar book_id ao usuário
book_id = input("\nDigite o UUID do livro (book_id): ").strip()

if not book_id:
    print_error("Book ID não fornecido. Abortando teste.")
    exit(1)

print_success(f"Book ID configurado: {book_id}")


# =============================================================================
# ETAPA 3: Testar upload sem autenticação (deve falhar com 401)
# =============================================================================
print_step(3, "Teste de segurança - Upload sem autenticação")

try:
    with open(TEST_VIDEO_PATH, 'rb') as video_file:
        files = {'file': video_file}
        data = {'book_id': book_id}
        
        response = requests.post(
            f"{BASE_URL}/videos/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 401:
            print_success("Segurança OK - Upload bloqueado sem autenticação")
        else:
            print_error(f"Falha de segurança - Status esperado 401, recebido {response.status_code}")
except FileNotFoundError:
    print(f"⚠️  Arquivo de vídeo não encontrado: {TEST_VIDEO_PATH}")
    print("Pulando teste de segurança...")


# =============================================================================
# ETAPA 4: Testar upload com arquivo inválido (deve falhar com 400)
# =============================================================================
print_step(4, "Teste de validação - Upload com arquivo não-vídeo")

# Criar um arquivo de texto temporário
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
    tmp_file.write("Este não é um vídeo")
    tmp_txt_path = tmp_file.name

try:
    with open(tmp_txt_path, 'rb') as text_file:
        files = {'file': ('test.txt', text_file, 'text/plain')}
        data = {'book_id': book_id}
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.post(
            f"{BASE_URL}/videos/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code == 400:
            print_success("Validação OK - Arquivo não-vídeo rejeitado")
            print(f"Mensagem: {response.json().get('detail', '')}")
        else:
            print_error(f"Falha na validação - Status esperado 400, recebido {response.status_code}")
finally:
    import os
    os.unlink(tmp_txt_path)


# =============================================================================
# ETAPA 5: Upload válido de vídeo
# =============================================================================
print_step(5, "Upload válido de vídeo")

try:
    with open(TEST_VIDEO_PATH, 'rb') as video_file:
        files = {'file': (TEST_VIDEO_PATH, video_file, 'video/mp4')}
        data = {'book_id': book_id}
        headers = {'Authorization': f'Bearer {access_token}'}
        
        print("Enviando vídeo para o servidor...")
        print("(Isso pode levar alguns minutos dependendo do tamanho do arquivo)")
        
        response = requests.post(
            f"{BASE_URL}/videos/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=600  # 10 minutos de timeout
        )
        
        if response.status_code == 201:
            print_success("Upload realizado com sucesso!")
            result = response.json()
            
            print(f"\n{BLUE}Detalhes do upload:{RESET}")
            print(f"  Video ID: {result['id']}")
            print(f"  Book ID: {result['book_id']}")
            print(f"  File URI: {result['file_uri']}")
            print(f"  Status: {result['status']}")
            print(f"\n{BLUE}Metadados:{RESET}")
            print(f"  Filename: {result['metadata']['filename']}")
            print(f"  Duration: {result['metadata']['duration']} segundos")
            print(f"  Size: {result['metadata']['size_bytes']} bytes")
            print(f"  Created: {result['metadata']['created_at']}")
            
            # Verificar no banco de dados
            print(f"\n{BLUE}Verificação no banco de dados:{RESET}")
            print(f"Execute este SQL para confirmar:")
            print(f"""
SELECT * FROM videos WHERE id = '{result['id']}';
            """)
            
        else:
            print_error(f"Erro no upload - Status {response.status_code}")
            print(f"Resposta: {response.text}")
            
except FileNotFoundError:
    print_error(f"Arquivo de vídeo não encontrado: {TEST_VIDEO_PATH}")
    print("Por favor, coloque um arquivo de vídeo de teste no mesmo diretório")
except requests.exceptions.Timeout:
    print_error("Timeout - O upload demorou muito tempo")
except Exception as e:
    print_error(f"Erro inesperado: {str(e)}")


# =============================================================================
# Resumo final
# =============================================================================
print(f"\n{BLUE}{'='*60}")
print("RESUMO DOS TESTES")
print(f"{'='*60}{RESET}\n")

print("Para mais testes, você pode:")
print("1. Testar com vídeos de diferentes tamanhos")
print("2. Testar com diferentes formatos (mp4, mov, avi, etc)")
print("3. Verificar o tempo de processamento na Gemini API")
print("4. Testar upload com book_id inválido ou de outro usuário")
print("\nDocumentação da API: http://localhost:8000/docs")
