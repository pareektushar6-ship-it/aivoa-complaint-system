"""
Extract plain text from an uploaded complaint file (PDF, .eml email, or .txt).
This is intentionally simple — assignment says production-grade OCR is NOT required.
"""

import io
from email import policy
from email.parser import BytesParser

from pypdf import PdfReader


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    name = filename.lower()

    if name.endswith(".pdf"):
        return _extract_pdf(file_bytes)
    elif name.endswith(".eml"):
        return _extract_email(file_bytes)
    else:
        # .txt or anything else -> just decode as plain text
        return file_bytes.decode("utf-8", errors="ignore")


def _extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text).strip()


def _extract_email(file_bytes: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
    subject = msg.get("subject", "")
    sender = msg.get("from", "")

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    return f"From: {sender}\nSubject: {subject}\n\n{body}".strip()
