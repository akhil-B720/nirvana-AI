from typing import Dict, Any, List

class DigitalTwinEngine:
    """
    Computes structural component assembly states for Three.js 3D Digital Twins
    based on engineering construction milestone sequences.
    """

    NOTICE = "Visualization derived from available project attributes; not a photographic reconstruction."

    COMPONENT_DEFINITIONS = {
        "BUILDING": [
            {"id": "foundation", "name": "Deep Foundation & Plinth", "min": 0, "max": 15, "color": "#78716c"},
            {"id": "columns", "name": "RCC Vertical Columns", "min": 10, "max": 35, "color": "#64748b"},
            {"id": "beams", "name": "Horizontal Support Beams", "min": 25, "max": 45, "color": "#94a3b8"},
            {"id": "walls", "name": "Masonry Walls & Partitions", "min": 40, "max": 70, "color": "#ea580c"},
            {"id": "roof", "name": "Roof Slab & Waterproofing", "min": 65, "max": 80, "color": "#0284c7"},
            {"id": "doors_windows", "name": "Doors, Windows & Glazing", "min": 75, "max": 88, "color": "#0d9488"},
            {"id": "finishing", "name": "Internal Plaster & Electrical", "min": 85, "max": 100, "color": "#16a34a"}
        ],
        "ROAD": [
            {"id": "earthwork", "name": "Site Clearing & Earthwork", "min": 0, "max": 25, "color": "#a16207"},
            {"id": "subbase", "name": "Granular Sub-Base (GSB)", "min": 20, "max": 50, "color": "#78716c"},
            {"id": "base", "name": "Wet Mix Macadam (WMM) Base", "min": 45, "max": 70, "color": "#64748b"},
            {"id": "asphalt", "name": "Dense Bituminous Asphalt (DBM)", "min": 65, "max": 90, "color": "#1e293b"},
            {"id": "markings", "name": "Road Thermoplastic Markings & Signage", "min": 88, "max": 100, "color": "#fbbf24"}
        ],
        "BRIDGE": [
            {"id": "foundation", "name": "Sub-surface Well/Pile Foundation", "min": 0, "max": 25, "color": "#78716c"},
            {"id": "pillars", "name": "RCC Pier Columns & Abutments", "min": 20, "max": 50, "color": "#64748b"},
            {"id": "deck", "name": "Prestressed Concrete Girder Deck", "min": 45, "max": 75, "color": "#0284c7"},
            {"id": "railings", "name": "Crash Barriers & Safety Railings", "min": 70, "max": 90, "color": "#ea580c"},
            {"id": "finishing", "name": "Expansion Joints & Road Surface", "min": 85, "max": 100, "color": "#16a34a"}
        ],
        "WATER_TANK": [
            {"id": "foundation", "name": "Reinforced Raft Foundation", "min": 0, "max": 20, "color": "#78716c"},
            {"id": "supports", "name": "Staging Columns & Bracing", "min": 15, "max": 45, "color": "#64748b"},
            {"id": "tank_body", "name": "Cylindrical Tank Container & Dome", "min": 40, "max": 75, "color": "#0284c7"},
            {"id": "pipelines", "name": "Inlet/Outlet Piping & Pump Set", "min": 70, "max": 90, "color": "#0d9488"},
            {"id": "finishing", "name": "Disinfection Test & Commissioning", "min": 85, "max": 100, "color": "#16a34a"}
        ]
    }

    @classmethod
    def calculate_component_states(cls, project_type: str, progress: float) -> List[Dict[str, Any]]:
        components_def = cls.COMPONENT_DEFINITIONS.get(project_type, cls.COMPONENT_DEFINITIONS["BUILDING"])
        states = []
        p = max(0.0, min(100.0, progress))

        for comp in components_def:
            c_min = comp["min"]
            c_max = comp["max"]
            if p <= c_min:
                completion_pct = 0.0
                status = "NOT_STARTED"
            elif p >= c_max:
                completion_pct = 100.0
                status = "COMPLETED"
            else:
                completion_pct = round(((p - c_min) / (c_max - c_min)) * 100.0, 1)
                status = "IN_PROGRESS"

            states.append({
                "component_id": comp["id"],
                "name": comp["name"],
                "completion_percentage": completion_pct,
                "status": status,
                "color": comp["color"]
            })

        return states

    @classmethod
    def generate_twin_scene(cls, project, simulated_progress: float = None) -> Dict[str, Any]:
        p_type = project.project_type if project.project_type in cls.COMPONENT_DEFINITIONS else "BUILDING"
        
        rep_prog = float(project.reported_progress or 0.0)
        obs_prog = float(project.observed_progress) if project.observed_progress is not None else None
        
        reported_components = cls.calculate_component_states(p_type, rep_prog)
        observed_components = cls.calculate_component_states(p_type, obs_prog) if obs_prog is not None else None
        simulated_components = cls.calculate_component_states(p_type, simulated_progress) if simulated_progress is not None else None

        db_components = []
        if hasattr(project, "components") and project.components:
            for c in project.components:
                db_components.append({
                    "component_id": str(c.id),
                    "name": c.component_name,
                    "completion_percentage": c.completion_pct,
                    "status": c.detected_status,
                    "weight_pct": c.weight_pct,
                    "data_status": c.data_status
                })

        return {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "project_type": p_type,
            "data_status": getattr(project, "data_status", "PUBLIC_VERIFIED"),
            "reported_state": {
                "progress": rep_prog,
                "components": reported_components
            },
            "observed_state": {
                "progress": obs_prog,
                "status": "AVAILABLE" if obs_prog is not None else "NOT_AVAILABLE",
                "message": "Physical ground evidence unavailable." if obs_prog is None else None,
                "components": observed_components
            },
            "granular_components": db_components,
            "simulation_state": {
                "progress": simulated_progress,
                "components": simulated_components
            } if simulated_progress is not None else None,
            "metadata_notice": cls.NOTICE
        }

