import os
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


def validate_file_extension(filename: str) -> bool:
    """Validate file extension against allowed extensions."""
    file_ext = Path(filename).suffix.lower()
    return file_ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """Validate file size against maximum allowed size."""
    return file_size <= MAX_FILE_SIZE


def create_session_directory(session_id: str) -> Path:
    """Create directory for session if it doesn't exist."""
    session_dir = Path(settings.storage_path) / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


@router.post("", response_class=JSONResponse)
async def upload_resume(
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Upload a resume file (PDF or DOCX).
    
    Args:
        file: The uploaded file
        
    Returns:
        Dict containing session_id and filename
        
    Raises:
        HTTPException: For validation errors or file processing issues
    """
    try:
        # Validate file extension
        if not validate_file_extension(file.filename or ""):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
            )
        
        # Validate file size
        if not validate_file_size(file.size or 0):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size allowed is {MAX_FILE_SIZE // (1024 * 1024)}MB."
            )
        
        # Generate session ID and create session directory
        session_id = str(uuid.uuid4())
        session_dir = create_session_directory(session_id)
        
        # Save file to session directory
        file_path = session_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "file_size": len(content),
            "message": "File uploaded successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )