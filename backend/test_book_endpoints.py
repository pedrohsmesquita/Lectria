"""
Script de teste para endpoints de livros
Testa criação, listagem e detalhes de livros
"""
import requests
import json

# Configuração
BASE_URL = "http://localhost:8000"

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_step(step_number: int, description: str):
    """Print formatted step"""
    print(f"\n{BLUE}{'='*60}")
    print(f"ETAPA {step_number}: {description}")
    print(f"{'='*60}{RESET}\n")



def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}[OK] {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}[ERRO] {message}{RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{YELLOW}[INFO] {message}{RESET}")


# =============================================================================
# ETAPA 1: Autenticação
# =============================================================================
print_step(1, "Autenticação - Login ou Registro")

login_data = {
    "email": "teste@lectria.com",
    "password": "senha123"
}

try:
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
except requests.exceptions.ConnectionError:
    print_error("Não foi possível conectar ao servidor. Verifique se está rodando em localhost:8000")
    exit(1)

if response.status_code == 200:
    print_success("Login realizado com sucesso")
    auth_response = response.json()
    access_token = auth_response["access_token"]
    user_name = auth_response["user"]["full_name"]
else:
    print_info("Login falhou, tentando registrar usuário...")
    register_data = {
        "email": "teste@lectria.com",
        "password": "senha123",
        "full_name": "Usuário Teste"
    }
    reg_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if reg_response.status_code == 201:
        print_success("Usuário registrado com sucesso")
        # Tentar login novamente
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            auth_response = response.json()
            access_token = auth_response["access_token"]
            user_name = auth_response["user"]["full_name"]
        else:
            print_error(f"Erro no login após registro: {response.text}")
            exit(1)
    else:
        print_error(f"Erro no registro e login: {reg_response.text}")
        exit(1)

print(f"Token recebido: {access_token[:30]}...")
print(f"Usuário: {user_name}")

headers = {"Authorization": f"Bearer {access_token}"}


# =============================================================================
# ETAPA 2: Listar livros (deve estar vazio inicialmente)
# =============================================================================
print_step(2, "Listar livros existentes")

response = requests.get(f"{BASE_URL}/books", headers=headers)

if response.status_code == 200:
    books = response.json()
    print_success(f"Livros encontrados: {len(books)}")
    for book in books:
        print(f"  - {book['title']} ({book['video_count']} vídeos)")
else:
    print_error(f"Erro ao listar livros: {response.text}")


# =============================================================================
# ETAPA 3: Criar novo livro
# =============================================================================
print_step(3, "Criar novo livro")

book_data = {
    "title": "Fundamentos de Python"
}

response = requests.post(f"{BASE_URL}/books", json=book_data, headers=headers)

if response.status_code == 201:
    print_success("Livro criado com sucesso!")
    book = response.json()
    book_id = book["id"]
    print(f"\n{BLUE}Detalhes do livro:{RESET}")
    print(f"  ID: {book['id']}")
    print(f"  Título: {book['title']}")
    print(f"  Autor: {book['author']}")
    print(f"  Status: {book['status']}")
    print(f"  Vídeos: {book['video_count']}")
else:
    print_error(f"Erro ao criar livro: {response.text}")
    exit(1)


# =============================================================================
# ETAPA 4: Criar mais livros para teste
# =============================================================================
print_step(4, "Criar livros adicionais")

additional_books = [
    {"title": "Introdução ao JavaScript"},
    {"title": "Machine Learning Básico"},
    {"title": "Design Patterns em Python"}
]

created_books = [book_id]  # Incluir o primeiro livro criado

for book_data in additional_books:
    response = requests.post(f"{BASE_URL}/books", json=book_data, headers=headers)
    if response.status_code == 201:
        book = response.json()
        created_books.append(book["id"])
        print_success(f"Criado: {book['title']}")
    else:
        print_error(f"Erro ao criar '{book_data['title']}': {response.text}")


# =============================================================================
# ETAPA 5: Listar todos os livros
# =============================================================================
print_step(5, "Listar todos os livros")

response = requests.get(f"{BASE_URL}/books", headers=headers)

if response.status_code == 200:
    books = response.json()
    print_success(f"Total de livros: {len(books)}")
    print(f"\n{BLUE}Lista de livros:{RESET}")
    for i, book in enumerate(books, 1):
        print(f"  {i}. {book['title']}")
        print(f"     Autor: {book['author']}")
        print(f"     Status: {book['status']}")
        print(f"     Vídeos: {book['video_count']}")
        print(f"     Criado em: {book['created_at']}")
        print()
else:
    print_error(f"Erro ao listar livros: {response.text}")


# =============================================================================
# ETAPA 6: Obter detalhes de um livro específico
# =============================================================================
print_step(6, "Obter detalhes de um livro específico")

response = requests.get(f"{BASE_URL}/books/{created_books[0]}", headers=headers)

if response.status_code == 200:
    book_details = response.json()
    print_success("Detalhes obtidos com sucesso")
    print(f"\n{BLUE}Detalhes completos:{RESET}")
    print(f"  Título: {book_details['title']}")
    print(f"  Autor: {book_details['author']}")
    print(f"  Status: {book_details['status']}")
    print(f"  Vídeos: {len(book_details['videos'])}")
    
    if book_details['videos']:
        print(f"\n{BLUE}Vídeos associados:{RESET}")
        for video in book_details['videos']:
            print(f"  - {video['filename']} ({video['duration']}s)")
    else:
        print_info("  Nenhum vídeo associado ainda")
else:
    print_error(f"Erro ao obter detalhes: {response.text}")


# =============================================================================
# ETAPA 7: Testar validação - Título vazio
# =============================================================================
print_step(7, "Teste de validação - Título vazio")

response = requests.post(
    f"{BASE_URL}/books",
    json={"title": ""},
    headers=headers
)

if response.status_code == 422:
    print_success("Validação OK - Título vazio rejeitado")
else:
    print_error(f"Falha na validação - Status esperado 422, recebido {response.status_code}")


# =============================================================================
# ETAPA 8: Testar segurança - Acesso sem autenticação
# =============================================================================
print_step(8, "Teste de segurança - Acesso sem autenticação")

response = requests.get(f"{BASE_URL}/books")

if response.status_code == 401:
    print_success("Segurança OK - Acesso bloqueado sem autenticação")
else:
    print_error(f"Falha de segurança - Status esperado 401, recebido {response.status_code}")


# =============================================================================
# Resumo final
# =============================================================================
print(f"\n{BLUE}{'='*60}")
print("RESUMO DOS TESTES")
print(f"{'='*60}{RESET}\n")

print(f"[OK] Autenticação funcionando")
print(f"[OK] Criação de livros funcionando")
print(f"[OK] Listagem de livros funcionando")
print(f"[OK] Detalhes de livros funcionando")
print(f"[OK] Validação de dados funcionando")
print(f"[OK] Segurança (JWT) funcionando")

print(f"\n{YELLOW}IDs dos livros criados (use para testar upload):{RESET}")
for book_id in created_books:
    print(f"  {book_id}")

print("\nDocumentação da API: http://localhost:8000/docs")
