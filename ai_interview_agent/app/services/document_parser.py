from pypdf import PdfReader
from io import BytesIO
from pathlib import Path
import fitz
import shutil
import os

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
class ResumeParser:
    def __init__(self, resume_content: str|bytes):
        self.resume_content = resume_content
        self.file_path = UPLOAD_DIR / resume_content.filename

    def parse(self):
        with open(self.file_path, 'wb') as f:
            shutil.copyfileobj(self.resume_content.file, f)      
        try:
            text = extract_text_from_pdf(self.file_path)
            return text.strip()
        finally:
            # os.remove(self.file_path)
            pass
    
class JobPostParser:
    def __init__(self, job_post_content: str|bytes):
        self.job_post_content = job_post_content
        self.file_path = UPLOAD_DIR / job_post_content.filename
    def parse(self):
        with open(self.file_path, 'wb') as f:
            shutil.copyfileobj(self.job_post_content.file, f)
        try:
            text = extract_text_from_pdf(self.file_path)
            return text.strip()
        finally:
            # os.remove(self.file_path)
            pass

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text if text else "No text found in the PDF"