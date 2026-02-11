"""
Celery Tasks - Video Processing
"""
from celery_app import celery_app
from database import get_db
from models.books import Books
from models.videos import Videos
from models.chapters import Chapters
from models.sections import Sections
from utils.ffmpeg_utils import extract_audio_from_video
from utils.gemini_utils import upload_audio_to_gemini, call_gemini_discovery
import os
import shutil
from uuid import UUID


@celery_app.task(bind=True)
def process_book_videos(self, book_id: str):
    """
    Task principal: processa todos os vídeos de um livro.
    
    Fluxo:
    1. Atualiza status do livro para PROCESSING
    2. Extrai áudio de cada vídeo
    3. Faz upload dos áudios para Gemini File API
    4. Chama Discovery (Gemini 2.5 Flash)
    5. Salva chapters e sections no banco
    6. Atualiza status para DISCOVERY_COMPLETE
    7. Limpa arquivos temporários
    
    Em caso de erro:
    - Marca livro como ERROR
    - Limpa arquivos temporários
    - Propaga exceção
    
    Args:
        book_id: UUID do livro a ser processado
    
    Returns:
        Dict com status e book_id
    """
    db = next(get_db())
    temp_audio_dir = None
    
    try:
        print(f"[Task] Iniciando processamento do livro {book_id}")
        
        # 1. Atualizar status do livro para PROCESSING
        book = db.query(Books).filter(Books.id == UUID(book_id)).first()
        if not book:
            raise Exception(f"Livro {book_id} não encontrado")
        
        print(f"[Task] Livro encontrado: {book.title}")
        
        book.status = "EXTRACTING_AUDIO"
        book.processing_progress = 0
        book.current_step = "Extraindo áudio dos vídeos"
        db.commit()
        
        print(f"[Task] Status atualizado para EXTRACTING_AUDIO")
        
        # 2. Buscar todos os vídeos do livro
        videos = db.query(Videos).filter(Videos.book_id == UUID(book_id)).all()
        
        if not videos:
            raise Exception(f"Nenhum vídeo encontrado para o livro {book_id}")
        
        print(f"[Task] {len(videos)} vídeo(s) encontrado(s)")
        
        # 3. Criar pasta temporária para áudios
        user_id = str(book.author_profile_id)
        temp_audio_dir = f"/app/media/{user_id}/{book_id}/temp_audio"
        os.makedirs(temp_audio_dir, exist_ok=True)
        
        print(f"[Task] Pasta temporária criada: {temp_audio_dir}")
        
        # 4. Extrair áudio de cada vídeo
        audio_extractions = []
        
        for idx, video in enumerate(videos, 1):
            print(f"[Task] Extraindo áudio do vídeo {idx}/{len(videos)}: {video.filename}")
            
            audio_filename = f"{video.id}.mp3"
            audio_path = os.path.join(temp_audio_dir, audio_filename)
            
            success = extract_audio_from_video(video.storage_path, audio_path)
            
            if not success:
                raise Exception(f"Falha ao extrair áudio do vídeo {video.id} ({video.filename})")
            
            audio_extractions.append({
                "video_id": str(video.id),
                "audio_path": audio_path
            })
            
            # Atualizar progresso (0-30% para extração de áudio)
            progress = int((idx / len(videos)) * 30)
            book.processing_progress = progress
            db.commit()
            
            print(f"[Task] Áudio extraído: {audio_path} (Progresso: {progress}%)")
        
        print(f"[Task] Todos os áudios extraídos com sucesso")
        
        # 5. Upload dos áudios para Gemini
        book.status = "UPLOADING_TO_GEMINI"
        book.processing_progress = 30
        book.current_step = "Enviando áudios para análise"
        db.commit()
        
        gemini_files = []
        
        for idx, extraction in enumerate(audio_extractions, 1):
            print(f"[Task] Upload {idx}/{len(audio_extractions)} para Gemini File API")
            
            file_name = upload_audio_to_gemini(
                audio_path=extraction["audio_path"],
                display_name=extraction["video_id"]  # UUID como display_name
            )
            
            gemini_files.append({
                "video_id": extraction["video_id"],
                "file_name": file_name
            })
            
            # Atualizar progresso (30-60% para upload)
            progress = 30 + int((idx / len(audio_extractions)) * 30)
            book.processing_progress = progress
            db.commit()
            
            print(f"[Task] Upload concluído: {file_name} (Progresso: {progress}%)")
        
        print(f"[Task] Todos os uploads concluídos")
        
        # 6. Chamar Gemini Discovery
        book.status = "ANALYZING_CONTENT"
        book.processing_progress = 60
        book.current_step = "Analisando conteúdo com IA"
        db.commit()
        
        print(f"[Task] Iniciando fase Discovery com Gemini 2.5 Flash")
        
        discovery_result = call_gemini_discovery(gemini_files)
        
        book.processing_progress = 80
        db.commit()
        
        print(f"[Task] Discovery concluída. Salvando no banco de dados...")
        
        # 7. Salvar chapters e sections no banco
        book.status = "GENERATING_STRUCTURE"
        book.current_step = "Gerando estrutura do livro"
        db.commit()
        for chapter_data in discovery_result["chapters"]:
            chapter = Chapters(
                book_id=UUID(book_id),
                title=chapter_data["title"],
                order=chapter_data["order"]
            )
            db.add(chapter)
            db.flush()  # Para obter o ID do capítulo
            
            print(f"[Task] Capítulo criado: {chapter.title} (order: {chapter.order})")
            
            for section_data in chapter_data["sections"]:
                section = Sections(
                    chapter_id=chapter.id,
                    video_id=UUID(section_data["video_id"]),
                    title=section_data["title"],
                    order=section_data["order"],
                    start_time=section_data["start_time"],
                    end_time=section_data["end_time"],
                    status="PENDING"
                )
                db.add(section)
                
                print(f"[Task]   Seção criada: {section.title} ({section.start_time}s - {section.end_time}s)")
        
        # 8. Atualizar status do livro para COMPLETED
        book.status = "COMPLETED"
        book.processing_progress = 100
        book.current_step = "Processamento concluído"
        db.commit()
        
        print(f"[Task] Status atualizado para DISCOVERY_COMPLETE")
        
        # 9. Limpar arquivos temporários
        if temp_audio_dir and os.path.exists(temp_audio_dir):
            shutil.rmtree(temp_audio_dir)
            print(f"[Task] Arquivos temporários removidos")
        
        print(f"[Task] Processamento concluído com sucesso!")
        
        return {
            "status": "success",
            "book_id": book_id,
            "chapters_created": len(discovery_result["chapters"])
        }
        
    except Exception as e:
        print(f"[Task] ERRO: {str(e)}")
        
        # Em caso de erro, marcar livro como ERROR
        try:
            book = db.query(Books).filter(Books.id == UUID(book_id)).first()
            if book:
                book.status = "ERROR"
                db.commit()
                print(f"[Task] Status do livro atualizado para ERROR")
        except Exception as db_error:
            print(f"[Task] Erro ao atualizar status do livro: {str(db_error)}")
        
        # Tentar limpar arquivos temporários
        try:
            if temp_audio_dir and os.path.exists(temp_audio_dir):
                shutil.rmtree(temp_audio_dir)
                print(f"[Task] Arquivos temporários removidos após erro")
        except Exception as cleanup_error:
            print(f"[Task] Erro ao limpar arquivos temporários: {str(cleanup_error)}")
        
        # Propagar exceção
        raise e
        
    finally:
        db.close()
