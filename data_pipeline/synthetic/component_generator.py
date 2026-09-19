# -*- coding: utf-8 -*-
"""
Synthetic Physical Component Generator.
Generates civil milestone stages (Foundation, Columns, Beams, Walls, Roof, etc.)
that logically correspond to overall project completion percentage.
"""

from typing import List, Dict, Any

SECTOR_COMPONENTS = {
    "BUILDING": [
        ("Foundation & Substructure", "foundation", 20.0),
        ("RCC Columns", "columns", 15.0),
        ("Beams & Framing", "beams", 15.0),
        ("Brickwork & Walls", "walls", 15.0),
        ("RCC Roof Slab", "roof", 15.0),
        ("Windows & Joinery", "windows", 5.0),
        ("Doors & Shutters", "doors", 5.0),
        ("Internal Services (Electrical & Plumbing)", "services", 5.0),
        ("Surface Finishing & Painting", "finishing", 5.0),
    ],
    "ROAD": [
        ("Land Preparation & Clearing", "land_preparation", 15.0),
        ("Earthwork & Subgrade Compaction", "earthwork", 20.0),
        ("Granular Subbase (GSB)", "subbase", 20.0),
        ("Wet Mix Macadam (WBM) Base", "base", 20.0),
        ("Dense Bituminous Macadam (Asphalt)", "asphalt", 15.0),
        ("Road Markings, Signs & Berms", "markings", 10.0),
    ],
    "BRIDGE": [
        ("Substructure Foundation & Piling", "foundation", 30.0),
        ("Pillars, Piers & Abutments", "pillars", 25.0),
        ("Girders & Deck Slab", "deck", 25.0),
        ("Crash Barriers & Railings", "railings", 10.0),
        ("Wearing Coat & Approach Finishing", "finishing", 10.0),
    ],
    "WATER_TANK": [
        ("Foundation Raft & Footing", "foundation", 25.0),
        ("Staging & RCC Support Columns", "supports", 25.0),
        ("Tank Body Container & Dome", "tank_body", 30.0),
        ("Inlet/Outlet Pipelines & Valves", "pipes", 10.0),
        ("Surface Finishing & Waterproofing", "finishing", 10.0),
    ]
}

def generate_project_components(
    project_id: str,
    project_type: str,
    overall_progress: float
) -> List[Dict[str, Any]]:
    """
    Generates component states matching the overall civil completion percentage.
    Early stages complete first before later stages commence.
    """
    comps_def = SECTOR_COMPONENTS.get(project_type, SECTOR_COMPONENTS["BUILDING"])
    components = []
    
    # Cumulative distribution of progress
    # e.g., if progress is 50%, foundation (20%) is 100%, columns (15%) is 100%, beams (15%) is 100%, etc.
    accumulated_progress = overall_progress

    for title, code, weight in comps_def:
        if accumulated_progress >= weight:
            completion = 100.0
            status = "COMPLETED"
            accumulated_progress -= weight
        elif accumulated_progress > 0:
            completion = round((accumulated_progress / weight) * 100.0, 1)
            status = "IN_PROGRESS"
            accumulated_progress = 0.0
        else:
            completion = 0.0
            status = "NOT_STARTED"

        components.append({
            "project_id": project_id,
            "sector": project_type,
            "component_name": title,
            "weight_pct": weight,
            "completion_pct": completion,
            "detected_status": status,
            "data_status": "SYNTHETIC"
        })

    return components
