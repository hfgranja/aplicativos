import uuid
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import MediaFile
from schemas import MediaFileOut
import aiofiles

router = APIRouter(prefix="/api/media", tags=["media"])

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "video/mp4", "video/webm", "video/quicktime",
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/x-wav",
    "audio/mp4", "audio/aac",
}


@router.post("/upload", response_model=MediaFileOut)
async def upload_media(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Tipo de arquivo não suportado: {file.content_type}")

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOADS_DIR, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    media = MediaFile(
        id=str(uuid.uuid4()),
        original_name=file.filename,
        stored_name=stored_name,
        mime_type=file.content_type,
        file_size_bytes=len(content),
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.get("/{file_id}/download")
def download_media(file_id: str, db: Session = Depends(get_db)):
    media = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    if not media:
        raise HTTPException(404, "Arquivo não encontrado")
    file_path = os.path.join(UPLOADS_DIR, media.stored_name)
    if not os.path.exists(file_path):
        raise HTTPException(404, "Arquivo físico não encontrado")
    return FileResponse(file_path, media_type=media.mime_type, filename=media.original_name)


@router.post("/{file_id}/transcribe", response_model=MediaFileOut)
def transcribe_media(file_id: str, db: Session = Depends(get_db)):
    media = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    if not media:
        raise HTTPException(404, "Arquivo não encontrado")
    if media.transcript:
        return media  # already transcribed

    file_path = os.path.join(UPLOADS_DIR, media.stored_name)
    if not os.path.exists(file_path):
        raise HTTPException(404, "Arquivo físico não encontrado")

    try:
        from services.transcription_service import transcribe_audio
        transcript = transcribe_audio(file_path)
        if transcript is None:
            raise HTTPException(500, "faster-whisper não está instalado")
        media.transcript = transcript
        media.transcribed_at = datetime.utcnow()
        db.commit()
        db.refresh(media)
        return media
    except Exception as e:
        raise HTTPException(500, f"Erro na transcrição: {str(e)}")


@router.delete("/{file_id}")
def delete_media(file_id: str, db: Session = Depends(get_db)):
    media = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    if not media:
        raise HTTPException(404, "Arquivo não encontrado")
    file_path = os.path.join(UPLOADS_DIR, media.stored_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(media)
    db.commit()
    return {"ok": True}
