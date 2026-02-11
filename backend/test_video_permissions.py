
import requests
import os
import sys

# Configuração
BASE_URL = "http://localhost:8000"
TEST_VIDEO_PATH = "temp_test_video.mp4"

# Cores
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def print_success(msg): print(f"{GREEN}[OK] {msg}{RESET}")
def print_error(msg): print(f"{RED}[ERRO] {msg}{RESET}")

def create_dummy_video():
    with open(TEST_VIDEO_PATH, "wb") as f:
        f.write(b"dummy video content" * 1024)

def cleanup():
    if os.path.exists(TEST_VIDEO_PATH):
        os.remove(TEST_VIDEO_PATH)

def run_test():
    create_dummy_video()
    try:
        # 1. Login/Register Owner
        print("1. Autenticando usuario Owner...")
        auth_data = {"email": "owner@test.com", "password": "password123", "full_name": "Owner User"}
        try:
            requests.post(f"{BASE_URL}/auth/register", json=auth_data)
        except: pass
        
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": auth_data["email"], "password": auth_data["password"]})
        if resp.status_code != 200:
            print_error(f"Login failed: {resp.text}")
            return
        owner_token = resp.json()["access_token"]
        print_success("Usuario Owner autenticado")

        # 2. Login/Register Attacker
        print("2. Autenticando usuario Attacker...")
        attacker_data = {"email": "attacker@test.com", "password": "password123", "full_name": "Attacker User"}
        try: 
            requests.post(f"{BASE_URL}/auth/register", json=attacker_data)
        except: pass
        
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": attacker_data["email"], "password": attacker_data["password"]})
        if resp.status_code != 200:
            print_error(f"Login failed: {resp.text}")
            return
        attacker_token = resp.json()["access_token"]
        print_success("Usuario Attacker autenticado")

        # 3. Create Book (Owner)
        print("3. Criando livro do Owner...")
        resp = requests.post(f"{BASE_URL}/books", json={"title": "Owner Book"}, headers={"Authorization": f"Bearer {owner_token}"})
        if resp.status_code != 201:
            print_error(f"Create book failed: {resp.text}")
            return
        book_id = resp.json()["id"]
        print_success(f"Livro criado: {book_id}")

        # 4. Test Upload (Owner) - Should Success
        print("4. Testando upload pelo Owner (Deve funcionar)...")
        with open(TEST_VIDEO_PATH, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            data = {"book_id": book_id}
            headers = {"Authorization": f"Bearer {owner_token}"}
            resp = requests.post(f"{BASE_URL}/videos/upload", files=files, data=data, headers=headers)
            
            # Nota: Pode falhar se a API do Gemini validar o arquivo real, mas o erro seria 500 ou 400 da API, não 403.
            # Estamos testando permissão aqui. Se passar do 403, considero sucesso de permissão.
            if resp.status_code in [201, 500, 400]: 
                # 500/400 aceitável pois o video é fake, mas 403 não.
                # Se for 403, falhou no teste de permissão (owner deve ter permissão)
                print_success(f"Upload Owner passou da verificação de permissão (Status: {resp.status_code})")
            elif resp.status_code == 403:
                print_error("Owner recebeu 403 Forbidden! (Erro na correção)")
            else:
                print_error(f"Status inesperado: {resp.status_code} - {resp.text}")

        # 5. Test Upload (Attacker) - Should Fail 403
        print("5. Testando upload pelo Attacker (Deve falhar com 403)...")
        with open(TEST_VIDEO_PATH, "rb") as f:
            files = {"file": ("video.mp4", f, "video/mp4")}
            data = {"book_id": book_id}
            headers = {"Authorization": f"Bearer {attacker_token}"}
            resp = requests.post(f"{BASE_URL}/videos/upload", files=files, data=data, headers=headers)
            
            if resp.status_code == 403:
                print_success("Attacker bloqueado com sucesso (403 Forbidden)")
            else:
                print_error(f"Attacker NÃO foi bloqueado! Status: {resp.status_code}")

    finally:
        cleanup()

if __name__ == "__main__":
    run_test()
