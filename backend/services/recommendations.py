from typing import List, Dict, Any

class VerificationRecommendationEngine:
    """
    Generates traceable, deterministic verification actions for nodal officers
    grounded directly in observed data anomalies and reality gaps.
    """

    @classmethod
    def generate_recommendations(cls, project, risk_score_obj, reality_gap_data: Dict[str, Any], similarity_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        recommendations = []

        # 1. Reality Gap Trigger
        rg_score = reality_gap_data.get("reality_gap_score", 0.0)
        rep_prog = reality_gap_data.get("reported_progress", 0.0)
        obs_prog = reality_gap_data.get("observed_progress")

        if obs_prog is not None and (rep_prog - obs_prog) > 20.0:
            recommendations.append({
                "action_id": "ACT_REALITY_GAP_AUDIT",
                "priority": "CRITICAL",
                "trigger": f"Ground-observed progress ({obs_prog:.1f}%) is {rep_prog - obs_prog:.1f}% below reported progress ({rep_prog:.1f}%)",
                "recommended_action": "Conduct immediate joint physical inspection with executive engineer and geotagged timestamped photo survey.",
                "action_type": "FIELD_AUDIT"
            })

        # 2. Missing Ground Evidence Trigger
        if obs_prog is None:
            recommendations.append({
                "action_id": "ACT_MISSING_EVIDENCE",
                "priority": "MEDIUM",
                "trigger": "No verified field photograph or ground milestone sensor on administrative record.",
                "recommended_action": "Order field inspection officer to upload geotagged high-resolution site photographs via mobile evidence capture.",
                "action_type": "EVIDENCE_COLLECTION"
            })

        # 3. Payment-to-Progress Mismatch Trigger
        sanction = float(project.sanction_amount or 0.0)
        released = float(project.released_amount or 0.0)
        expenditure = float(project.expenditure_amount or 0.0)
        utilization = (expenditure / released) if released > 0 else 0.0

        if utilization > 0.85 and rep_prog < 40.0:
            recommendations.append({
                "action_id": "ACT_FINANCIAL_MISMATCH",
                "priority": "HIGH",
                "trigger": f"High financial expenditure ({utilization*100:.1f}%) contrasted with low physical progress ({rep_prog:.1f}%)",
                "recommended_action": "Verify contractor measurement books (MB), vendor vouchers, and intermediate utilization certificates (UC).",
                "action_type": "FINANCIAL_AUDIT"
            })

        # 4. Timeline Slippage / Delay Trigger
        if reality_gap_data.get("time_progress_gap") and reality_gap_data["time_progress_gap"] > 25.0:
            recommendations.append({
                "action_id": "ACT_SCHEDULE_SLIPPAGE",
                "priority": "HIGH",
                "trigger": f"Physical execution lags behind expected timeline curve by {reality_gap_data['time_progress_gap']:.1f}%",
                "recommended_action": "Issue formal show-cause query to implementing agency regarding resource mobilization and milestone slippage.",
                "action_type": "ADMINISTRATIVE_NOTICE"
            })

        # 5. Potential Duplicate / Overlap Trigger
        if similarity_matches:
            top_match = similarity_matches[0]
            if top_match.get("status_label") == "potentially_similar":
                recommendations.append({
                    "action_id": "ACT_SIMILARITY_CHECK",
                    "priority": "HIGH",
                    "trigger": f"High similarity (score: {top_match['combined_similarity']:.2f}) with nearby project {top_match['compared_project_id']}: '{top_match['compared_project_name']}'",
                    "recommended_action": "Cross-verify site demarcation and land revenue records to prevent duplicate sanction on identical asset.",
                    "action_type": "RECORD_AUDIT"
                })

        # 6. Missing Coordinates Trigger
        if project.latitude is None or project.longitude is None:
            recommendations.append({
                "action_id": "ACT_GEO_VERIFICATION",
                "priority": "MEDIUM",
                "trigger": "Missing GPS coordinates in administrative project sanction record.",
                "recommended_action": "Obtain certified GIS latitude and longitude coordinates from the block development officer.",
                "action_type": "GIS_RECTIFICATION"
            })

        # Default fallback if everything is normal
        if not recommendations:
            recommendations.append({
                "action_id": "ACT_ROUTINE_MONITORING",
                "priority": "LOW",
                "trigger": "All financial and physical metrics within normal historical parameters.",
                "recommended_action": "Maintain routine administrative progress tracking.",
                "action_type": "ROUTINE"
            })

        return recommendations
