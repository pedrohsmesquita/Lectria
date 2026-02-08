"""
FFmpeg Utilities - Audio extraction from video files
"""
import subprocess
import os
from typing import Optional


def extract_audio_from_video(video_path: str, output_audio_path: str) -> bool:
    """
    Extrai áudio de um vídeo usando ffmpeg.
    
    Args:
        video_path: Caminho completo do arquivo de vídeo
        output_audio_path: Caminho onde o áudio será salvo (.mp3)
    
    Returns:
        True se sucesso, False se falha
    """
    try:
        # Verificar se o vídeo existe
        if not os.path.exists(video_path):
            print(f"Erro: Vídeo não encontrado em {video_path}")
            return False
        
        # Comando ffmpeg para extrair áudio
        command = [
            "ffmpeg",
            "-i", video_path,           # Input file
            "-vn",                       # Sem vídeo
            "-acodec", "libmp3lame",    # Codec MP3
            "-ab", "128k",              # Bitrate de áudio
            "-ar", "44100",             # Sample rate
            "-y",                        # Sobrescrever se existir
            output_audio_path
        ]
        
        # Executar comando
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Verificar se o arquivo foi criado
        if os.path.exists(output_audio_path):
            print(f"Áudio extraído com sucesso: {output_audio_path}")
            return True
        else:
            print(f"Erro: Arquivo de áudio não foi criado")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar ffmpeg: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao extrair áudio: {str(e)}")
        return False


def get_video_duration(video_path: str) -> Optional[float]:
    """
    Obtém a duração de um vídeo em segundos usando ffprobe.
    
    Args:
        video_path: Caminho completo do arquivo de vídeo
    
    Returns:
        Duração em segundos ou None se falhar
    """
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        duration = float(result.stdout.decode().strip())
        return duration
        
    except Exception as e:
        print(f"Erro ao obter duração do vídeo: {str(e)}")
        return None
