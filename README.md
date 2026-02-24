# 📚 Lectria - Transformando Aulas em Livros

Este projeto automatiza a criação de livros didáticos a partir da transcrição de aulas utilizando o poder multimodal do **Google Gemini**. O sistema processa transcrições, gera sumários inteligentes, redige capítulos em Markdown e extrai imagens relevantes de slides automaticamente.

## 🛠️ Tecnologias Principais

* **Backend:** Python (FastAPI) + FFmpeg
* **Frontend:** React (TypeScript)
* **IA:** Google Gemini API
* **Banco de Dados:** PostgreSQL
* **Infraestrutura:** Docker & Docker Compose
* **Orquestração:** Celery + Redis

---

## 🚀 Como Levantar o Projeto

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

### 1. Pré-requisitos

* **Docker** e **Docker Compose** instalados (no Windows é preciso do **Docker Desktop** e do **WSL2**).
* Uma **API Key** do Google Gemini.

### 2. Configuração do Ambiente

Faça uma cópia do arquivo .env.example chamada .env. Dentro de .env,especifique a chave da API do Google Gemini em `GOOGLE_API_KEY`.

### 3. Subindo os Containers

Abra o terminal na pasta raiz e execute:

```bash
docker-compose up --build

```

> O `--build` garante que o Docker instale o FFmpeg e todas as dependências do Python/Node na primeira execução.

### 4. Acessando as Aplicações

Após o carregamento, as interfaces estarão disponíveis em:

* **Frontend (React):** `http://localhost:3000`
* **Backend (API Docs):** `http://localhost:8000/docs`
* **Banco de Dados:** Porta `5432`

---

## 📂 Estrutura de Pastas

* `/backend`: Lógica da API, integração com Gemini e processamento de vídeo.
* `/frontend`: Interface do usuário para upload e edição do livro.
* `/media_storage`: Pasta local onde ficarão os vídeos e imagens geradas (não versionada no Git).
