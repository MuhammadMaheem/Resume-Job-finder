import io
import logging
from typing import Optional

import pdfplumber

logger = logging.getLogger("jobmatcher")


class ResumeParser:
    """Extracts text and basic structure from PDF resumes."""

    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Extract all text from a PDF file."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip() if text else None
        except Exception as e:
            logger.warning("Error extracting text from PDF: %s", e)
            return None

    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes) -> Optional[str]:
        """Extract text from PDF bytes."""
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip() if text else None
        except Exception as e:
            logger.warning("Error extracting text from PDF bytes: %s", e)
            return None
