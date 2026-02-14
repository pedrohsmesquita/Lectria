"""
FastAPI Backend - Sistema de Transformação de Vídeo em Livro Didático
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from database import get_db, check_database_connection
from routes.auth_routes import router as auth_router
from routes.video_routes import router as video_router
from routes.book_routes import router as book_router
from routes.chapter_routes import router as chapter_router
from routes.processing_routes import router as processing_router
from routes.transcript_routes import router as transcript_router

app = FastAPI(
    title="Video to Book API",
    description="Sistema de transformação de vídeos educacionais em livros didáticos",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(book_router)
app.include_router(chapter_router)
app.include_router(processing_router)
app.include_router(transcript_router)

@app.get("/")
async def root():
    """Endpoint de health check"""
    return {
        "status": "online",
        "message": "Video to Book API is running",
        "media_storage": os.getenv("MEDIA_STORAGE_PATH", "/app/media")
    }

@app.get("/health")
async def health_check():
    """Verificação de saúde da aplicação"""
    db_status = "connected" if check_database_connection() else "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "ffmpeg": "available"  # TODO: Verificar se FFmpeg está instalado
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
