import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFReportGenerator:
    """
    Generates formal verification audit dossiers for vigilance and nodal officers.
    Strictly differentiates between Reported, Observed, Inferred, and Missing values.
    """

    @classmethod
    def generate_project_dossier(cls, project, reality_gap_data, risk_data, recommendations, output_path: str) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b")
        )
        advisory_style = ParagraphStyle(
            "LegalAdvisory",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#b91c1c"),
            backColor=colors.HexColor("#fef2f2"),
            borderPadding=6,
            spaceAfter=12
        )

        elements = []

        # Header
        elements.append(Paragraph("NIRVANA — National Infrastructure Reality & Verification Network using AI", title_style))
        elements.append(Paragraph(f"CONFIDENTIAL DECISION-SUPPORT DOSSIER | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

        # Legal Advisory
        disclaimer_text = (
            "<b>STATUTORY ADVISORY:</b> AI-generated risk indicators are decision-support signals "
            "and do not constitute proof of fraud, corruption, or wrongdoing. Nodal vigilance officers "
            "must independently authenticate all primary physical records before initiating formal proceedings."
        )
        elements.append(Paragraph(disclaimer_text, advisory_style))

        # 1. Project Identification Table
        elements.append(Paragraph("1. Project Identification & Provenance", section_style))
        proj_data = [
            [Paragraph("<b>Project ID</b>", body_style), Paragraph(str(project.project_id), body_style),
             Paragraph("<b>Status</b>", body_style), Paragraph(str(project.status), body_style)],
            [Paragraph("<b>Project Name</b>", body_style), Paragraph(str(project.project_name), body_style),
             Paragraph("<b>Type / Sector</b>", body_style), Paragraph(f"{project.project_type} / {project.sector or 'N/A'}", body_style)],
            [Paragraph("<b>Location</b>", body_style), Paragraph(f"{project.district}, {project.state}", body_style),
             Paragraph("<b>Coordinates</b>", body_style), Paragraph(f"{project.latitude}, {project.longitude}" if project.latitude else "COORDINATES MISSING", body_style)],
            [Paragraph("<b>Data Status</b>", body_style), Paragraph(str(project.data_availability_status), body_style),
             Paragraph("<b>Executing Agency</b>", body_style), Paragraph(str(project.agency or 'Unspecified'), body_style)]
        ]
        t1 = Table(proj_data, colWidths=[90, 180, 90, 180])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 10))

        # 2. Reality Planes Matrix (Expected vs Reported vs Observed)
        elements.append(Paragraph("2. Reality Planes Comparison", section_style))
        exp_p = f"{reality_gap_data.get('expected_progress'):.1f}%" if reality_gap_data.get('expected_progress') is not None else "DATA NOT AVAILABLE"
        rep_p = f"{project.reported_progress:.1f}%"
        obs_p = f"{project.observed_progress:.1f}%" if project.observed_progress is not None else "DATA NOT AVAILABLE (No Photo on Record)"
        
        planes_data = [
            [Paragraph("<b>Plane</b>", body_style), Paragraph("<b>Progress Metric</b>", body_style), Paragraph("<b>Data Source & Nature</b>", body_style)],
            [Paragraph("<b>EXPECTED REALITY</b>", body_style), Paragraph(exp_p, body_style), Paragraph("Algorithmic S-Curve from Sanctioned Milestone Dates", body_style)],
            [Paragraph("<b>REPORTED REALITY</b>", body_style), Paragraph(rep_p, body_style), Paragraph("Self-certified Administrative Return by Agency", body_style)],
            [Paragraph("<b>OBSERVED REALITY</b>", body_style), Paragraph(obs_p, body_style), Paragraph("Field Inspection Photo / Sensor / Geotagged Survey", body_style)],
        ]
        t2 = Table(planes_data, colWidths=[140, 140, 260])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 10))

        # 3. Risk & Reality Gap Analytics
        elements.append(Paragraph("3. Analytical Indicators & Anomaly Synthesis", section_style))
        fused_score = risk_data.get("fused_risk_score", 0.0) if risk_data else 0.0
        tier = risk_data.get("risk_tier", "NORMAL") if risk_data else "NORMAL"
        rg_score = reality_gap_data.get("reality_gap_score", 0.0)
        
        risk_table_data = [
            [Paragraph("<b>Fused Risk Score</b>", body_style), Paragraph(f"<b>{fused_score:.1f} / 100 ({tier})</b>", body_style)],
            [Paragraph("<b>Reality Gap Score</b>", body_style), Paragraph(f"{rg_score:.1f} / 100", body_style)],
            [Paragraph("<b>Financial Utilization</b>", body_style), Paragraph(f"₹{project.expenditure_amount:,.2f} spent of ₹{project.released_amount:,.2f} released", body_style)],
            [Paragraph("<b>Contributing Factors</b>", body_style), Paragraph("; ".join(reality_gap_data.get("contributing_factors", [])) or "None", body_style)]
        ]
        t3 = Table(risk_table_data, colWidths=[150, 390])
        t3.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t3)
        elements.append(Spacer(1, 10))

        # 4. Traceable Verification Recommendations
        elements.append(Paragraph("4. Traceable Field Verification Recommendations", section_style))
        rec_data = [[Paragraph("<b>Priority</b>", body_style), Paragraph("<b>Trigger</b>", body_style), Paragraph("<b>Prescribed Action</b>", body_style)]]
        for rec in recommendations:
            rec_data.append([
                Paragraph(f"<b>{rec['priority']}</b>", body_style),
                Paragraph(rec["trigger"], body_style),
                Paragraph(rec["recommended_action"], body_style)
            ])
        t4 = Table(rec_data, colWidths=[70, 210, 260])
        t4.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t4)
        elements.append(Spacer(1, 12))

        # Footer Notice
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=6))
        elements.append(Paragraph("NIRVANA Platform | Model Suite v1.0.0 | End of Audit Brief", subtitle_style))

        doc.build(elements)
        return output_path
