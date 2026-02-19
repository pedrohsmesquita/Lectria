"""
FastAPI Backend - Sistema de Transformação de Vídeo em Livro Didático
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from fastapi.staticfiles import StaticFiles

from database import get_db, check_database_connection
from routes.auth_routes import router as auth_router
from routes.video_routes import router as video_router
from routes.book_routes import router as book_router
from routes.chapter_routes import router as chapter_router
from routes.processing_routes import router as processing_router
from routes.transcript_routes import router as transcript_router
from routes.section_routes import router as section_router
from routes.books_export_routes import router as books_export_router
from routes.asset_routes import router as asset_router
from routes.bibliography_routes import router as bibliography_router

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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    import logging
    logger = logging.getLogger("uvicorn.error")
    # Clean up errors to make them JSON serializable
    clean_errors = []
    for error in exc.errors():
        error_copy = error.copy()
        if "input" in error_copy:
            # Convert UploadFile or other objects to string for logging/JSON
            error_copy["input"] = str(error_copy["input"])
        clean_errors.append(error_copy)
    
    logger.error(f"Validation Error: {clean_errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": clean_errors},
    )

# Include routers
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(book_router)
app.include_router(chapter_router)
app.include_router(processing_router)
app.include_router(transcript_router)
app.include_router(section_router)
app.include_router(books_export_router)
app.include_router(asset_router)
app.include_router(bibliography_router)

# Mount media directory for serving extracted images
media_path = os.getenv("MEDIA_STORAGE_PATH", "/app/media")
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")

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
