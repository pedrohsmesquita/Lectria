"""
Gemini API Service - Integration with Google Gemini File API
"""
import os
import time
import tempfile
from typing import Tuple, Optional, Any
import google.generativeai as genai
from fastapi import UploadFile, HTTPException, status

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY não encontrada no ambiente")

genai.configure(api_key=GOOGLE_API_KEY)


def upload_video_to_gemini(file: UploadFile, display_name: str) -> Any:
    """
    Upload video file to Gemini File API.
    
    Args:
        file: UploadFile object from FastAPI
        display_name: Display name for the file (use video UUID)
        
    Returns:
        Uploaded file object with upload information
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Save file temporarily - works on both Windows and Linux
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, display_name)
        
        # Write uploaded file to temp location
        with open(temp_path, "wb") as temp_file:
            content = file.file.read()
            temp_file.write(content)
        
        # Upload to Gemini
        uploaded_file = genai.upload_file(
            path=temp_path,
            display_name=display_name
        )
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except Exception as e:
            print(f"Warning: Failed to remove temp file {temp_path}: {e}")
        
        return uploaded_file
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao fazer upload para Gemini API: {str(e)}"
        )


def wait_for_file_active(file_name: str, timeout_seconds: int = 300) -> str:
    """
    Poll Gemini File API until file status is ACTIVE.
    
    Args:
        file_name: Name of the file in Gemini (e.g., 'files/abc123')
        timeout_seconds: Maximum time to wait (default 5 minutes)
        
    Returns:
        Final status of the file ('ACTIVE' on success)
        
    Raises:
        HTTPException: If timeout or file processing fails
    """
    start_time = time.time()
    poll_interval = 2  # seconds
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > timeout_seconds:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Timeout aguardando processamento do vídeo (máx {timeout_seconds}s)"
            )
        
        try:
            file = genai.get_file(file_name)
            
            if file.state.name == "ACTIVE":
                return "ACTIVE"
            elif file.state.name == "FAILED":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Processamento do vídeo falhou na Gemini API"
                )
            
            # Still processing, wait before next poll
            time.sleep(poll_interval)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao verificar status do arquivo: {str(e)}"
            )


def get_video_duration(file: Any) -> float:
    """
    Extract video duration from Gemini file metadata.
    
    Args:
        file: Gemini file object
        
    Returns:
        Duration in seconds (0 if unavailable)
    """
    try:
        # Try to get video metadata
        if hasattr(file, 'video_metadata') and file.video_metadata:
            if hasattr(file.video_metadata, 'duration'):
                # Duration comes as string like "1234s", extract the number
                duration_str = file.video_metadata.duration
                if isinstance(duration_str, str) and duration_str.endswith('s'):
                    return float(duration_str[:-1])
                elif isinstance(duration_str, (int, float)):
                    return float(duration_str)
        
        # Fallback: return 0 if metadata not available
        return 0.0
        
    except Exception as e:
        print(f"Warning: Could not extract video duration: {e}")
        return 0.0


def upload_and_process_video(file: UploadFile, video_id: str) -> Tuple[str, str, float]:
    """
    Complete workflow: upload video, wait for processing, return metadata.
    
    Args:
        file: UploadFile from FastAPI
        video_id: UUID of the video record (used as display_name)
        
    Returns:
        Tuple of (file_uri, status, duration)
        
    Raises:
        HTTPException: If any step fails
    """
    # Step 1: Upload to Gemini
    uploaded_file = upload_video_to_gemini(file, display_name=video_id)
    
    # Step 2: Wait for ACTIVE status
    final_status = wait_for_file_active(uploaded_file.name)
    
    # Step 3: Get updated file info with metadata
    file_info = genai.get_file(uploaded_file.name)
    
    # Step 4: Extract duration
    duration = get_video_duration(file_info)
    
    # Return file URI, status, and duration
    return file_info.uri, final_status, duration

