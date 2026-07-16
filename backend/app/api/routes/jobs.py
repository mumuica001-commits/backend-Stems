from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.schemas import AnalysisResponse, JobResponse, StemResponse
from app.domain.exceptions import JobNotFoundError
from app.infrastructure.storage.job_repository import JobRepository

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    try:
        job = JobRepository().get(job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    return JobResponse(
        id=job.id,
        original_filename=job.original_filename,
        engine=job.engine.value,
        status=job.status.value,
        progress_percent=job.progress_percent,
        stage_message=job.stage_message,
        error_message=job.error_message,
        stems=[
            StemResponse(
                kind=stem.kind.value,
                confidence=stem.confidence,
                duration_seconds=stem.duration_seconds,
                sample_rate=stem.sample_rate,
                channels=stem.channels,
                download_url=f"/api/v1/jobs/{job.id}/stems/{stem.kind.value}",
            )
            for stem in job.stems
        ],
        analysis=AnalysisResponse(**job.analysis.__dict__) if job.analysis else None,
    )


@router.get("/jobs/{job_id}/stems/{stem_kind}")
async def download_stem(job_id: str, stem_kind: str):
    try:
        job = JobRepository().get(job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    stem = next((s for s in job.stems if s.kind.value == stem_kind), None)
    if stem is None or not os.path.isfile(stem.file_path):
        raise HTTPException(status_code=404, detail="Stem não encontrado")

    return FileResponse(
        stem.file_path,
        media_type="audio/wav",
        filename=f"{job.original_filename}_{stem_kind}.wav",
    )
