"""
DeadList Upload Router
Handles memory dump file upload with hash calculation and analysis triggering.
"""

import os
import uuid
import hashlib
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.database import Analysis, get_db, async_session
from models.schemas import AnalysisCreate
from routers.ws import ws_manager
from core.analysis_pipeline import run_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Upload"])

# Supported memory dump file extensions
ALLOWED_EXTENSIONS = {".raw", ".mem", ".dmp", ".vmem", ".img"}

# Magic bytes for common memory dump formats
MAGIC_BYTES = {
    b"MDMP": "Windows Minidump",
    b"PAGEDU64": "Windows Page Dump",
    b"EMF": "VMware Snapshot",
}


def _validate_file(filename: str) -> None:
    """Validate uploaded file by extension."""
    ext = os.path.splitext(filename)[1].lower()

    # In mock mode, accept any file for testing
    if settings.MOCK_MODE:
        return

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}",
        )


async def _calculate_hashes(filepath: str) -> dict:
    """Calculate MD5 and SHA256 hashes of a file (streaming, memory-efficient)."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    loop = asyncio.get_event_loop()

    def _hash_file():
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()

    return await loop.run_in_executor(None, _hash_file)


async def _run_analysis_background(analysis_id: str, dump_path: str):
    """Background task to run the analysis pipeline with its own DB session."""
    async with async_session() as db:
        await run_analysis(
            analysis_id=analysis_id,
            dump_path=dump_path,
            db=db,
            ws_broadcast=ws_manager.broadcast,
        )


@router.post("/upload", response_model=AnalysisCreate)
async def upload_memory_dump(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a memory dump file for analysis.

    - Validates file type
    - Saves with UUID-based naming (prevents path traversal)
    - Calculates MD5/SHA256 hashes for evidence integrity
    - Creates analysis record in database
    - Triggers analysis pipeline in background

    Returns analysis_id and file metadata.
    """
    # Validate file
    _validate_file(file.filename)

    # Generate unique filename
    file_uuid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ".raw"
    safe_filename = f"{file_uuid}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save file
    file_size = 0
    try:
        with open(filepath, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                f.write(chunk)
                file_size += len(chunk)

                # Check size limit
                if file_size > settings.max_upload_size_bytes:
                    os.remove(filepath)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum: {settings.MAX_UPLOAD_SIZE_GB}GB",
                    )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File save failed: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Calculate hashes
    md5_hash, sha256_hash = await _calculate_hashes(filepath)

    # Create analysis record
    analysis = Analysis(
        id=file_uuid,
        filename=file.filename or "unknown",
        filepath=filepath,
        md5_hash=md5_hash,
        sha256_hash=sha256_hash,
        file_size_bytes=file_size,
        status="pending",
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    logger.info(f"Upload complete: {file.filename} ({file_size} bytes) → {analysis.id}")

    # Trigger analysis pipeline in background
    asyncio.create_task(_run_analysis_background(analysis.id, filepath))

    return AnalysisCreate(
        analysis_id=analysis.id,
        filename=file.filename or "unknown",
        md5=md5_hash,
        sha256=sha256_hash,
        file_size_bytes=file_size,
        status="pending",
    )
