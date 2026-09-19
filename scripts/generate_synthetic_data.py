import os
import csv
from datetime import date, timedelta

def generate_synthetic_fixtures():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "dataset", "synthetic", "fixtures.csv")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    today = date.today()

    records = [
        {
            "project_id": "SYN-MP-001",
            "project_name": "Construction of 4-Room Community Primary Health Centre",
            "project_type": "BUILDING",
            "sector": "Health & Sanitation",
            "state": "Madhya Pradesh",
            "district": "Bhopal",
            "constituency": "Bhopal",
            "block": "Phanda",
            "village": "Karond",
            "latitude": 23.2599,
            "longitude": 77.4126,
            "sanction_amount": 2500000.0,
            "released_amount": 2500000.0,
            "expenditure_amount": 2200000.0,
            "start_date": (today - timedelta(days=240)).isoformat(),
            "expected_completion_date": (today + timedelta(days=60)).isoformat(),
            "actual_completion_date": "",
            "reported_progress": 78.0,
            "observed_progress": 75.0,
            "status": "IN_PROGRESS",
            "agency": "State PWD Bhopal",
            "notes": "Normal steady progress, ground-verified via field inspection photo"
        },
        {
            "project_id": "SYN-UP-002",
            "project_name": "Installation of Solar Dual-Pump Piped Water Supply System",
            "project_type": "WATER_TANK",
            "sector": "Drinking Water",
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "constituency": "Varanasi",
            "block": "Arajiline",
            "village": "Raja Talab",
            "latitude": 25.3176,
            "longitude": 82.9739,
            "sanction_amount": 1800000.0,
            "released_amount": 1800000.0,
            "expenditure_amount": 1750000.0,
            "start_date": (today - timedelta(days=180)).isoformat(),
            "expected_completion_date": (today - timedelta(days=20)).isoformat(),
            "actual_completion_date": "",
            "reported_progress": 95.0,
            "observed_progress": 15.0,  # CRITICAL REALITY GAP: Claimed 95%, observed only 15%
            "status": "IN_PROGRESS",
            "agency": "UP Jal Nigam",
            "notes": "High Reality Gap: 95% reported vs 15% observed on field visit"
        },
        {
            "project_id": "SYN-RJ-003",
            "project_name": "Bituminous Surface Road from Main NH to Village Mandi",
            "project_type": "ROAD",
            "sector": "Roads & Pathways",
            "state": "Rajasthan",
            "district": "Jaipur",
            "constituency": "Jaipur Rural",
            "block": "Amber",
            "village": "Kukas",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "sanction_amount": 3500000.0,
            "released_amount": 3500000.0,
            "expenditure_amount": 3400000.0,
            "start_date": (today - timedelta(days=365)).isoformat(),
            "expected_completion_date": (today - timedelta(days=120)).isoformat(),
            "actual_completion_date": "",
            "reported_progress": 25.0,  # CRITICAL PAYMENT-PROGRESS MISMATCH: 97% spent, 25% done
            "observed_progress": "",   # Observed evidence unavailable
            "status": "STALLED",
            "agency": "Rural Works Department Rajasthan",
            "notes": "Severe financial-progress mismatch: 97% fund expended with only 25% physical milestone"
        },
        {
            "project_id": "SYN-KA-004",
            "project_name": "High-Level Bridge across Nullah on Rural Road connecting Crossway",
            "project_type": "BRIDGE",
            "sector": "Roads & Pathways",
            "state": "Karnataka",
            "district": "Mysuru",
            "constituency": "Mysore",
            "block": "Nanjangud",
            "village": "Hullahalli",
            "latitude": 12.1189,
            "longitude": 76.6847,
            "sanction_amount": 7500000.0,
            "released_amount": 4000000.0,
            "expenditure_amount": 3800000.0,
            "start_date": (today - timedelta(days=500)).isoformat(),
            "expected_completion_date": (today - timedelta(days=200)).isoformat(),
            "actual_completion_date": "",
            "reported_progress": 45.0,
            "observed_progress": 42.0,
            "status": "STALLED",
            "agency": "Karnataka PWD",
            "notes": "Delay Risk: Past completion deadline by 200 days, work stalled at 45%"
        },
        {
            "project_id": "SYN-MH-005",
            "project_name": "Multi-Purpose Community Cultural Centre and Library Building",
            "project_type": "BUILDING",
            "sector": "Community Facilities",
            "state": "Maharashtra",
            "district": "Pune",
            "constituency": "Baramati",
            "block": "Haveli",
            "village": "Hadapsar",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "sanction_amount": 45000000.0,  # COST OUTLIER: 4.5 Cr (9x normal building)
            "released_amount": 20000000.0,
            "expenditure_amount": 19000000.0,
            "start_date": (today - timedelta(days=150)).isoformat(),
            "expected_completion_date": (today + timedelta(days=200)).isoformat(),
            "reported_progress": 50.0,
            "observed_progress": "",
            "status": "IN_PROGRESS",
            "agency": "Pune Municipal Corporation",
            "notes": "Cost Anomaly: Sanction amount is 900% above district median for community building"
        },
        {
            "project_id": "SYN-MH-006",
            "project_name": "Construction of Community Hall and Library Hall at Hadapsar",
            "project_type": "BUILDING",
            "sector": "Community Facilities",
            "state": "Maharashtra",
            "district": "Pune",
            "constituency": "Baramati",
            "block": "Haveli",
            "village": "Hadapsar",
            "latitude": 18.5210,  # Near SYN-MH-005 (~70 meters away, potential duplicate)
            "longitude": 73.8572,
            "sanction_amount": 4200000.0,
            "released_amount": 4200000.0,
            "expenditure_amount": 4000000.0,
            "start_date": (today - timedelta(days=140)).isoformat(),
            "expected_completion_date": (today + timedelta(days=180)).isoformat(),
            "reported_progress": 48.0,
            "observed_progress": "",
            "status": "IN_PROGRESS",
            "agency": "Pune Zilla Parishad",
            "notes": "Potential duplicate/overlap work sanctioned at the exact same location as SYN-MH-005"
        },
        {
            "project_id": "SYN-TN-007",
            "project_name": "Concrete Pathway and Covered Stormwater Drainage",
            "project_type": "ROAD",
            "sector": "Roads & Pathways",
            "state": "Tamil Nadu",
            "district": "Madurai",
            "constituency": "Madurai",
            "block": "Melur",
            "village": "Alagar Kovil",
            "latitude": "",  # MISSING COORDINATES
            "longitude": "",
            "sanction_amount": 1200000.0,
            "released_amount": 1200000.0,
            "expenditure_amount": 1150000.0,
            "start_date": (today - timedelta(days=90)).isoformat(),
            "expected_completion_date": (today + timedelta(days=90)).isoformat(),
            "reported_progress": 60.0,
            "observed_progress": "",
            "status": "IN_PROGRESS",
            "agency": "Rural Development Madurai",
            "notes": "Missing spatial coordinates, location flagged for verification"
        },
        {
            "project_id": "SYN-OD-008",
            "project_name": "Overhead Water Reservoir and Distribution Pipeline Network",
            "project_type": "WATER_TANK",
            "sector": "Drinking Water",
            "state": "Odisha",
            "district": "Ganjam",
            "constituency": "Berhampur",
            "block": "Chhatrapur",
            "village": "Aryapalli",
            "latitude": 19.3556,
            "longitude": 84.9928,
            "sanction_amount": 3200000.0,
            "released_amount": 3200000.0,
            "expenditure_amount": 3200000.0,
            "start_date": (today - timedelta(days=300)).isoformat(),
            "expected_completion_date": (today - timedelta(days=30)).isoformat(),
            "actual_completion_date": (today - timedelta(days=25)).isoformat(),
            "reported_progress": 100.0,
            "observed_progress": 100.0,
            "status": "COMPLETED",
            "agency": "RWSS Odisha",
            "notes": "Fully completed work with 100% verified physical and financial reconciliation"
        }
    ]

    fieldnames = [
        "project_id", "project_name", "project_type", "sector", "state", "district",
        "constituency", "block", "village", "latitude", "longitude",
        "sanction_amount", "released_amount", "expenditure_amount",
        "start_date", "expected_completion_date", "actual_completion_date",
        "reported_progress", "observed_progress", "status", "agency", "notes"
    ]

    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} synthetic test fixtures at: {target_path}")

if __name__ == "__main__":
    generate_synthetic_fixtures()
