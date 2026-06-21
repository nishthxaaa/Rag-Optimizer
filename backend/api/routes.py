import os
import uuid
import shutil
import aiofiles
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from backend.api.state import app_state, OptimizationStatus

router = APIRouter()

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Accepts a PDF upload, saves it to disk, and immediately
    kicks off the optimization pipeline in the background.
    Returns a doc_id the frontend uses to poll for status.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    if app_state.status == OptimizationStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Optimization already running.")

    # Save uploaded file with a unique ID
    doc_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Mark as running immediately so frontend can start polling
    app_state.set_running(doc_id, "PDF uploaded. Starting ingestion...")

    # Run the full pipeline in the background (non-blocking)
    background_tasks.add_task(run_optimization_task, save_path, doc_id)

    return {"doc_id": doc_id, "filename": file.filename, "status": "optimization_started"}


@router.get("/status")
async def get_status():
    """
    Polling endpoint — frontend calls this every 2 seconds
    to check optimization progress.
    """
    return app_state.to_dict()


@router.get("/results")
async def get_results():
    """Returns full scoreboard after optimization completes."""
    if app_state.status != OptimizationStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Optimization not complete yet.")
    return {
        "winner_config": app_state.winner_config,
        "scoreboard": app_state.scoreboard,
    }


def run_optimization_task(pdf_path: str, doc_id: str):
    """
    Background task — runs the full 3-phase pipeline.
    Updates app_state at each stage so /status reflects progress.
    """
    try:
        # Phase 1 — Ingest
        app_state.set_progress("Extracting and chunking document...")
        from backend.ingestion.ingestor import ingest_document
        ingest_document(pdf_path, doc_id)

        # Phase 2+3 — Optimize
        app_state.set_progress("Building variants and running evaluation...")
        from backend.evaluator.optimizer import run_optimization
        winner_variant = run_optimization(pdf_path, doc_id)

        # Done
        app_state.set_complete(winner_variant)

    except Exception as e:
        import traceback
        traceback.print_exc()
        app_state.set_failed(str(e))