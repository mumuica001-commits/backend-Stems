from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.application.use_cases.upload_audio import UploadAudioUseCase
from app.domain.entities import SeparationEngineName
from app.domain.exceptions import AudioTooLargeError, UnsupportedAudioFormatError
from app.infrastructure.separation.engine_factory import SeparationEngineFactory

router = APIRouter(prefix="/api/v1", tags=["upload"])


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    engine: str = Form(default=SeparationEngineName.DEMUCS_HTDEMUCS_6S.value),
):
    try:
        engine_enum = SeparationEngineName(engine)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Engine inválido: '{engine}'")

    contents = await file.read()

    use_case = UploadAudioUseCase()
    try:
        import io

        job = use_case.execute(
            filename=file.filename,
            file_stream=io.BytesIO(contents),
            content_length_bytes=len(contents),
            engine=engine_enum,
        )
    except UnsupportedAudioFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except AudioTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))

    return {"job_id": job.id, "status": job.status.value}


@router.get("/engines")
async def list_engines():
    return SeparationEngineFactory.list_available()
