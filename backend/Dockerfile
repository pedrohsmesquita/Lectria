# Backend Dockerfile - FastAPI + FFmpeg
FROM python:3.11-slim

# Instalar dependências do sistema (FFmpeg para processamento de vídeo/áudio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivo de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para media storage com permissões adequadas
RUN mkdir -p /app/media && chmod -R 777 /app/media

# Expor porta do FastAPI
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
