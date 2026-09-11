"""
SQLAlchemy ORM model for the `complaints` table.
Mirrors the fields in frontend/src/slices/complaintSlice.js so the form
maps 1:1 onto what gets persisted.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    # --- extracted / form fields ---
    complaint_source = Column(String(255), default="")
    customer_name = Column(String(255), default="")
    product_name = Column(String(255), default="")
    product_strength = Column(String(100), default="")
    batch_number = Column(String(100), default="")
    affected_quantity = Column(String(100), default="")
    manufacturing_date = Column(String(50), default="")
    expiry_date = Column(String(50), default="")
    originating_site_block = Column(String(255), default="")
    impacted_npm = Column(String(255), default="")
    defect_summary = Column(Text, default="")

    # --- AI outputs ---
    risk_level = Column(String(20), default="")
    risk_justification = Column(Text, default="")
    capa_recommendation = Column(Text, default="")

    # --- raw source text (kept for duplicate-detection / audit trail) ---
    raw_text = Column(Text, default="")

    # --- workflow status, e.g. "Pending Triage" / "Under Review" / "Closed" ---
    status = Column(String(50), default="Pending Triage")

    created_at = Column(DateTime, default=datetime.utcnow)
