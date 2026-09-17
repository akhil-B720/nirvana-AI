import re
from pathlib import Path
from typing import Dict, Any, Optional
import pdfplumber
import PyPDF2

from data_pipeline.sources.base import BaseDataSource

class PDFDataSource(BaseDataSource):
    """
    Ingests administrative sanction orders, completion certificates,
    and utilization certificates from PDF documents.
    """

    def __init__(self, file_path: str, doc_type: str = "SANCTION_ORDER"):
        p = Path(file_path)
        super().__init__(
            source_name=f"Document: {p.name}",
            source_type="DOCUMENT_PDF",
            source_url=f"file://{p.resolve()}"
        )
        self.file_path = p
        self.doc_type = doc_type
        self.extracted_text: str = ""
        self.extracted_entities: Dict[str, Any] = {}

    def fetch(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.file_path}")

        raw_bytes = self.file_path.read_bytes()
        self.compute_sha256(raw_bytes)

        full_text = []
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
        except Exception:
            # Fallback to PyPDF2
            reader = PyPDF2.PdfReader(str(self.file_path))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    full_text.append(t)

        self.extracted_text = "\n".join(full_text)
        self.extract_entities(self.extracted_text)
        return self.extracted_text

    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {}

        # Project ID pattern (e.g. MP-2024-..., DL-..., PRJ-...)
        id_match = re.search(r"(?:Project\s*(?:ID|Code|No\.?)|Work\s*Code)\s*[:=\-]?\s*([A-Z0-9\-_/]{4,30})", text, re.I)
        if id_match:
            entities["project_id"] = id_match.group(1).strip()

        # Sanction / Release Amount pattern
        amt_match = re.search(r"(?:Sanction(?:ed)?|Estimated|Total)\s*(?:Cost|Amount|Fund)?\s*[:=\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)", text, re.I)
        if amt_match:
            raw_amt = amt_match.group(1).replace(",", "")
            try:
                entities["sanction_amount"] = float(raw_amt)
            except ValueError:
                pass

        # Progress pattern
        prog_match = re.search(r"(?:Physical\s*Progress|Completed)\s*[:=\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%", text, re.I)
        if prog_match:
            try:
                entities["progress_percentage"] = min(100.0, float(prog_match.group(1)))
            except ValueError:
                pass

        # Implementing Agency pattern
        agency_match = re.search(r"(?:Executing|Implementing)\s*Agency\s*[:=\-]?\s*([^\n\r,]+)", text, re.I)
        if agency_match:
            entities["agency"] = agency_match.group(1).strip()

        # Date pattern (DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY)
        date_match = re.search(r"(?:Date|Sanction\s*Date)\s*[:=\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}-\d{2}-\d{2})", text, re.I)
        if date_match:
            entities["date"] = date_match.group(1).strip()

        self.extracted_entities = entities
        return entities

    def compute_consistency(self, db_project) -> float:
        """
        Calculates consistency score between extracted PDF entities
        and database records.
        """
        if not self.extracted_entities or not db_project:
            return 100.0  # Cannot refute without extracted data

        checks = []
        # Check amount
        if "sanction_amount" in self.extracted_entities and db_project.sanction_amount > 0:
            doc_amt = self.extracted_entities["sanction_amount"]
            db_amt = db_project.sanction_amount
            # Allow 5% tolerance for rounding or tax
            diff_ratio = abs(doc_amt - db_amt) / max(db_amt, 1.0)
            checks.append(max(0.0, 1.0 - diff_ratio))

        # Check agency
        if "agency" in self.extracted_entities and db_project.agency:
            doc_ag = self.extracted_entities["agency"].lower()
            db_ag = db_project.agency.lower()
            checks.append(1.0 if (doc_ag in db_ag or db_ag in doc_ag) else 0.5)

        # Check progress
        if "progress_percentage" in self.extracted_entities and db_project.reported_progress is not None:
            doc_prog = self.extracted_entities["progress_percentage"]
            db_prog = db_project.reported_progress
            diff = abs(doc_prog - db_prog)
            checks.append(max(0.0, 1.0 - (diff / 100.0)))

        return round(float(sum(checks) / len(checks) * 100.0), 2) if checks else 100.0

    def validate(self, df):
        return []

    def normalize(self, df):
        return df

    def load(self, db_session):
        return 0
