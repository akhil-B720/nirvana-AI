# -*- coding: utf-8 -*-
"""
Synthetic Document Generator.
Generates structured administrative document records (Sanction Orders,
Utilization Certificates, Inspection Stage Reports) with controlled consistency scores.
"""

from datetime import date, timedelta
from typing import List, Dict, Any

def generate_project_documents(
    project_id: str,
    sanction_amt: float,
    expenditure_amt: float,
    reported_progress: float,
    start_d: date,
    agency: str,
    anomaly_category: str = "NORMAL"
) -> List[Dict[str, Any]]:
    """
    Generates realistic administrative document entries for testing document consistency algorithms.
    """
    documents = []

    # 1. Sanction Order
    documents.append({
        "project_id": project_id,
        "doc_name": f"Administrative_Sanction_Order_{project_id}.pdf",
        "doc_type": "SANCTION_ORDER",
        "file_path": f"/synthetic_docs/sanction_{project_id}.pdf",
        "file_hash": f"syn_hash_so_{project_id[:12]}",
        "extracted_text": f"SANCTION ORDER: Project {project_id}. Total administrative approval of INR {sanction_amt:,.2f} sanctioned under MPLADS.",
        "extracted_data_json": f'{{"sanction_amount": {sanction_amt}, "sanction_date": "{start_d}", "agency": "{agency}"}}',
        "consistency_score": 100.0
    })

    # 2. Utilization Certificate (UC)
    uc_amount = expenditure_amt
    uc_consistency = 98.0

    if anomaly_category == "DOCUMENT_INCONSISTENCY":
        # Discrepancy: UC claims more than sanction or expenditure
        uc_amount = sanction_amt * 1.35
        uc_consistency = 42.0

    documents.append({
        "project_id": project_id,
        "doc_name": f"Form_GFR19A_Utilization_Certificate_{project_id}.pdf",
        "doc_type": "UTILIZATION_CERTIFICATE",
        "file_path": f"/synthetic_docs/uc_{project_id}.pdf",
        "file_hash": f"syn_hash_uc_{project_id[:12]}",
        "extracted_text": f"FORM GFR 19-A. Certified that out of Rs {sanction_amt:,.2f} sanctioned, Rs {uc_amount:,.2f} has been properly utilized.",
        "extracted_data_json": f'{{"claimed_utilization": {uc_amount}, "uc_certified": true, "consistency_gap": {abs(uc_amount - expenditure_amt)}}}',
        "consistency_score": uc_consistency
    })

    return documents
