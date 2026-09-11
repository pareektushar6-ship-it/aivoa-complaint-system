from typing import List

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from file_utils import extract_text_from_upload
from langgraph_agent import run_complaint_pipeline
import models
from schemas import ComplaintInput, ComplaintOut, ComplaintSaveRequest

# Create tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AIVOA Complaint Management API")

# Allow the React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "AIVOA backend running"}


@app.post("/api/complaint/parse")
def parse_complaint(payload: ComplaintInput):
    """
    Takes raw complaint text (pasted email, or extracted PDF/OCR text)
    and returns structured fields + AI risk assessment + CAPA recommendation.
    """
    result = run_complaint_pipeline(payload.text)
    return result


@app.post("/api/complaint/upload")
async def upload_complaint(file: UploadFile = File(...)):
    """
    Accepts a PDF, .eml email, or .txt file, extracts its text,
    then runs it through the same AI pipeline as /parse.
    """
    file_bytes = await file.read()
    try:
        raw_text = extract_text_from_upload(file.filename, file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

    result = run_complaint_pipeline(raw_text)
    result["raw_text"] = raw_text
    return result


@app.post("/api/complaint/save", response_model=ComplaintOut)
def save_complaint(payload: ComplaintSaveRequest, db: Session = Depends(get_db)):
    """Persists the reviewed/edited complaint form to the database."""
    record = models.Complaint(
        **payload.fields.model_dump(),
        risk_level=payload.risk_level,
        risk_justification=payload.risk_justification,
        capa_recommendation=payload.capa_recommendation,
        raw_text=payload.raw_text,
        status=payload.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/api/complaint", response_model=List[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    """Lists all saved complaints, most recent first — for a dashboard view."""
    return db.query(models.Complaint).order_by(models.Complaint.id.desc()).all()


@app.get("/api/complaint/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    record = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return record


# TODO (further bonus ideas, optional):
# - Duplicate Complaint Detection: before /save, query existing complaints with
#   matching product_name + batch_number and flag as a possible duplicate.
