from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ComplaintInput(BaseModel):
    text: str


class ComplaintFields(BaseModel):
    complaint_source: str = ""
    customer_name: str = ""
    product_name: str = ""
    product_strength: str = ""
    batch_number: str = ""
    affected_quantity: str = ""
    manufacturing_date: str = ""
    expiry_date: str = ""
    originating_site_block: str = ""
    impacted_npm: str = ""
    defect_summary: str = ""


class ComplaintSaveRequest(BaseModel):
    fields: ComplaintFields
    risk_level: Optional[str] = ""
    risk_justification: Optional[str] = ""
    capa_recommendation: Optional[str] = ""
    raw_text: Optional[str] = ""
    status: Optional[str] = "Pending Triage"


class ComplaintOut(ComplaintFields):
    """Flat shape matching the `Complaint` ORM model exactly (used for responses)."""

    id: int
    risk_level: Optional[str] = ""
    risk_justification: Optional[str] = ""
    capa_recommendation: Optional[str] = ""
    raw_text: Optional[str] = ""
    status: Optional[str] = "Pending Triage"
    created_at: datetime

    class Config:
        from_attributes = True
