"""
Celery Tasks - Transcription and Slide Processing
"""
from celery_app import celery_app
from database import get_db
from models.books import Books
from models.transcriptions import Transcription
from models.slides import Slide
from models.chapters import Chapters
from models.sections import Sections
from models.section_assets import SectionAssets
from services.gemini_service import generate_book_discovery, generate_section_content
import os
from uuid import UUID
import logging
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_book_transcripts_task(self, book_id: str):
    """
    Orchestrator Task:
    1. Runs Global Discovery to create the book skeleton.
    2. Stops after creating the structure (Review Phase).
    """
    db = next(get_db())
    try:
        book = db.query(Books).filter(Books.id == UUID(book_id)).first()
        if not book:
            raise Exception(f"Book {book_id} not found")

        book.status = "PROCESSANDO"
        book.current_step = "Analisando documentos..."
        book.processing_progress = 10
        db.commit()

        # Fetch all transcriptions and slides
        transcriptions_db = db.query(Transcription).filter(Transcription.book_id == UUID(book_id)).all()
        slides_db = db.query(Slide).filter(Slide.book_id == UUID(book_id)).all()

        transcripts_info = [{"id": str(t.id), "path": t.storage_path} for t in transcriptions_db]
        slides_info = [{"id": str(s.id), "path": s.storage_path} for s in slides_db]

        # Phase 1: Discovery
        import asyncio
        discovery_result = asyncio.run(
            generate_book_discovery(transcripts_info, slides_info)
        )

        # Prepare valid ID sets for validation
        valid_transcription_ids = {t["id"] for t in transcripts_info}
        valid_slide_ids = {s["id"] for s in slides_info}

        # Save Skeleton
        for chapter_data in discovery_result["chapters"]:
            chapter = Chapters(
                book_id=UUID(book_id),
                title=chapter_data["title"],
                order=chapter_data["order"]
            )
            db.add(chapter)
            db.flush()

            for section_data in chapter_data["sections"]:
                # Validation: ensure IDs exist and are in the correct category
                s_trans_id = section_data.get("source_transcription_id")
                s_slide_id = section_data.get("source_slide_id")
                
                final_trans_id = None
                if s_trans_id and s_trans_id in valid_transcription_ids:
                    final_trans_id = UUID(s_trans_id)
                else:
                    logger.warning(f"Invalid source_transcription_id '{s_trans_id}' from AI. Fallback to first available.")
                    if transcripts_info:
                        final_trans_id = UUID(transcripts_info[0]["id"])
                
                final_slide_id = None
                if s_slide_id and s_slide_id in valid_slide_ids:
                    final_slide_id = UUID(s_slide_id)
                elif s_slide_id:
                    logger.warning(f"Invalid source_slide_id '{s_slide_id}' from AI. Setting to None.")
                
                section = Sections(
                    chapter_id=chapter.id,
                    title=section_data["title"],
                    order=section_data["order"],
                    source_transcription_id=final_trans_id,
                    source_slide_id=final_slide_id,
                    status="PENDENTE",
                    start_time=0.0,
                    end_time=0.0
                )
                db.add(section)
        
        book.status = "ESTRUTURA_GERADA"
        book.current_step = "Sumário concluído"
        book.processing_progress = 100
        db.commit()

        return {"status": "Discovery complete", "book_id": book_id}

    except Exception as e:
        logger.exception(f"Error in discovery task for book {book_id}")
        book = db.query(Books).filter(Books.id == UUID(book_id)).first()
        if book:
            book.status = "ERRO"
            db.commit()
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def process_book_content_sequential_task(self, book_id: str):
    """
    Sequential Orchestrator:
    Finds the next PENDENTE section and triggers its processing.
    """
    db = next(get_db())
    try:
        # Find next pending section for this book
        section = db.query(Sections).join(Chapters).filter(
            Chapters.book_id == UUID(book_id),
            Sections.status == "PENDENTE"
        ).order_by(Chapters.order, Sections.order).first()

        book = db.query(Books).filter(Books.id == UUID(book_id)).first()
        if not book: return

        if not section:
            # All done!
            book.status = "CONCLUIDO"
            book.current_step = "Livro gerado com sucesso!"
            book.processing_progress = 100
            db.commit()
            return {"status": "All sections completed"}

        # Update progress
        all_sections = db.query(Sections).join(Chapters).filter(Chapters.book_id == UUID(book_id)).all()
        completed_count = sum(1 for s in all_sections if s.status == "SUCESSO")
        progress = 10 + int((completed_count / len(all_sections)) * 90)
        
        # Garante que a mensagem caiba nos 50 caracteres (prefixo/sufixo usam ~20-25 caracteres)
        display_title = section.title
        if len(display_title) > 20:
            display_title = display_title[:17] + "..."
            
        book.status = "PROCESSANDO"
        book.current_step = f"Gerando: {display_title} ({completed_count + 1}/{len(all_sections)})"
        book.processing_progress = progress
        db.commit()

        # Trigger section task
        process_section_content_task.delay(str(section.id), trigger_next=True)
        return {"status": "Processing section", "section_id": str(section.id)}

    except Exception as e:
        logger.exception(f"Error in sequential orchestrator for book {book_id}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def process_section_content_task(self, section_id: str, trigger_next: bool = True):
    """
    Individual Section Task:
    1. Calls Gemini Pro for the specific section content.
    2. Saves Markdown, assets, and bibliography.
    3. Re-triggers sequential orchestrator.
    """
    db = next(get_db())
    try:
        section = db.query(Sections).filter(Sections.id == UUID(section_id)).first()
        if not section:
            raise Exception(f"Section {section_id} not found")

        section.status = "PROCESSANDO"
        db.commit()

        chapter = section.chapter
        book = chapter.book
        
        # Get source paths
        transcript = db.query(Transcription).filter(Transcription.id == section.source_transcription_id).first()
        slide = db.query(Slide).filter(Slide.id == section.source_slide_id).first() if section.source_slide_id else None

        # Phase 2: Deep Analysis
        import asyncio
        content_result = asyncio.run(generate_section_content(
            section_title=section.title,
            chapter_title=chapter.title,
            transcript_path=transcript.storage_path,
            slide_path=slide.storage_path if slide else None
        ))

        # Update Section
        section.content_markdown = content_result["content_markdown"]
        section.bibliography = content_result.get("bibliography_found", [])
        section.status = "SUCESSO"
        
        # Save Assets
        for asset_data in content_result.get("section_assets", []):
            asset = SectionAssets(
                section_id=section.id,
                placeholder=asset_data["placeholder"],
                caption=asset_data["caption"],
                timestamp=0.0,
                slide_page=asset_data.get("slide_page"),
                storage_path=slide.storage_path if slide else "N/A",
                crop_info=asset_data["crop_info"]
            )
            db.add(asset)

        db.commit()
        
        # Trigger next section if requested
        if trigger_next:
            process_book_content_sequential_task.delay(str(book.id))

        return {"status": "Section complete", "section_id": section_id}

    except google_exceptions.ResourceExhausted as e:
        logger.warning(f"Quota exceeded for section {section_id}. Retrying with backoff...")
        # Use a longer delay for quota issues to avoid constant polling
        raise self.retry(exc=e, countdown=60)  # Wait at least 1 minute on quota error

    except Exception as e:
        logger.exception(f"Error in section task {section_id}")
        section = db.query(Sections).filter(Sections.id == UUID(section_id)).first()
        if section:
            section.status = "ERRO"
            db.commit()
            book = section.chapter.book
            book.status = "ERRO"
            db.commit()
        raise e
    finally:
        db.close()
