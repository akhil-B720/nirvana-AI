import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.models import Project, RiskScore, ProjectAnomaly, VerificationCase
from backend.services.reality_gap import RealityGapEngine

class ContextualAssistant:
    """
    Zero-hallucination contextual assistant querying solely verified database records.
    Never speculates or fabricates answers.
    """

    DISCLAIMER = "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."

    @classmethod
    def answer_query(cls, query: str, project_id: Optional[str], db: Session) -> Dict[str, Any]:
        q = query.lower().strip()

        if not project_id:
            # System-level query
            total_projects = db.query(Project).count()
            high_risk = db.query(RiskScore).filter(RiskScore.risk_tier.in_(["HIGH", "CRITICAL"])).count()
            open_cases = db.query(VerificationCase).filter(VerificationCase.case_status == "OPEN").count()

            return {
                "answer": (
                    f"NIRVANA is currently monitoring {total_projects} sanctioned works across India. "
                    f"There are currently {high_risk} projects flagged with elevated risk indicators (HIGH or CRITICAL) "
                    f"and {open_cases} open human-in-the-loop verification cases awaiting field audit. "
                    f"Please select an individual project to inspect its reality gap, digital twin, or specific anomaly triggers."
                ),
                "citations": ["database.projects", "database.risk_scores", "database.verification_cases"],
                "disclaimer": cls.DISCLAIMER
            }

        project = db.query(Project).filter_by(project_id=project_id).first()
        if not project:
            return {
                "answer": f"Project with ID '{project_id}' was not found in the verified database registry.",
                "citations": [],
                "disclaimer": cls.DISCLAIMER
            }

        risk = db.query(RiskScore).filter_by(project_id=project_id).first()
        rg_data = RealityGapEngine.evaluate(project)

        # 1. "Why is this project high risk?" / "Which factors contributed?"
        if any(term in q for term in ["why", "risk", "flagged", "factors", "reason", "irregularity"]):
            score = risk.fused_risk_score if risk else 0.0
            tier = risk.risk_tier if risk else "NORMAL"
            factors = json.loads(risk.contributing_factors_json) if (risk and risk.contributing_factors_json) else rg_data.get("contributing_factors", [])

            if tier in ("HIGH", "CRITICAL"):
                factor_text = "\n".join(f"• {f}" for f in factors)
                answer = (
                    f"Project '{project.project_name}' ({project.project_id}) has an elevated risk score of {score:.1f}/100 ({tier}).\n\n"
                    f"Contributing analytical triggers:\n{factor_text}\n\n"
                    f"Financial Status: ₹{project.expenditure_amount:,.2f} spent out of ₹{project.released_amount:,.2f} released (Sanction: ₹{project.sanction_amount:,.2f}).\n"
                    f"Physical Status: Reported {project.reported_progress:.1f}%, Observed: {str(project.observed_progress) + '%' if project.observed_progress is not None else 'DATA NOT AVAILABLE'}."
                )
            else:
                answer = (
                    f"Project '{project.project_name}' has a normal risk score of {score:.1f}/100 ({tier}). "
                    f"Expenditures and physical milestones are tracking within normal parameters."
                )

            return {
                "answer": answer,
                "citations": [
                    f"projects.sanction_amount={project.sanction_amount}",
                    f"projects.expenditure_amount={project.expenditure_amount}",
                    f"projects.reported_progress={project.reported_progress}",
                    f"projects.observed_progress={project.observed_progress}",
                    f"risk_scores.fused_risk_score={score}"
                ],
                "disclaimer": cls.DISCLAIMER
            }

        # 2. "What should be verified?" / "Recommendations"
        if any(term in q for term in ["verify", "recommend", "action", "check", "inspect"]):
            from backend.services.recommendations import VerificationRecommendationEngine
            recs = VerificationRecommendationEngine.generate_recommendations(project, risk, rg_data, [])
            rec_text = "\n".join(f"• [{r['priority']}] {r['trigger']} -> Action: {r['recommended_action']}" for r in recs)
            return {
                "answer": f"Prescribed verification recommendations for {project.project_id}:\n\n{rec_text}",
                "citations": ["VerificationRecommendationEngine", f"projects.project_id={project.project_id}"],
                "disclaimer": cls.DISCLAIMER
            }

        # 3. "What data is missing?" / "Data gaps"
        if any(term in q for term in ["missing", "unavailable", "gap", "evidence"]):
            missing = []
            if project.observed_progress is None:
                missing.append("Observed physical ground evidence (no verified field photos or sensor feeds on record)")
            if project.latitude is None or project.longitude is None:
                missing.append("Geographic GPS coordinates (latitude/longitude null)")
            if not project.actual_completion_date and project.status == "COMPLETED":
                missing.append("Actual completion date missing for project marked as COMPLETED")
            if not project.agency:
                missing.append("Implementing executive agency not specified")

            if missing:
                answer = f"The following data fields are currently missing or unverified for {project.project_id}:\n" + "\n".join(f"• {m}" for m in missing)
            else:
                answer = f"All primary administrative, spatial, and financial fields are populated for {project.project_id}."

            return {
                "answer": answer,
                "citations": [f"projects.observed_progress={project.observed_progress}", f"projects.coords=({project.latitude},{project.longitude})"],
                "disclaimer": cls.DISCLAIMER
            }

        # 4. Fallback: Honest answer
        return {
            "answer": (
                f"I don't have sufficient verified data to answer that specific query for project {project.project_id}. "
                f"I can provide information regarding: risk factors, reality gap analysis, missing data, and prescribed verification actions."
            ),
            "citations": [f"projects.project_id={project.project_id}"],
            "disclaimer": cls.DISCLAIMER
        }
