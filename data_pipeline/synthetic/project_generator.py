# -*- coding: utf-8 -*-
"""
Synthetic Project Dataset Generator.
Generates structurally realistic MPLADS-style infrastructure projects
with deterministic seeds and controlled anomaly patterns.
"""

import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np

# Empirical state centroids across India
STATE_CENTROIDS = {
    "Andhra Pradesh": (15.9129, 79.7400, ["Visakhapatnam", "Guntur", "Krishna", "Chittoor", "Anantapur"]),
    "Arunachal Pradesh": (28.2180, 94.7278, ["Papum Pare", "Changlang", "West Kameng", "Tirap"]),
    "Assam": (26.2006, 92.9376, ["Kamrup", "Dibrugarh", "Silchar", "Nagaon", "Jorhat"]),
    "Bihar": (25.0961, 85.3131, ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"]),
    "Chhattisgarh": (21.2787, 81.8661, ["Raipur", "Bilaspur", "Durg", "Bastar", "Korba"]),
    "Goa": (15.2993, 74.1240, ["North Goa", "South Goa"]),
    "Gujarat": (22.2587, 71.1924, ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"]),
    "Haryana": (29.0588, 76.0856, ["Gurugram", "Faridabad", "Ambala", "Hisar", "Rohtak"]),
    "Himachal Pradesh": (31.1048, 77.1734, ["Shimla", "Kangra", "Mandi", "Solan", "Kullu"]),
    "Jharkhand": (23.6102, 85.2799, ["Ranchi", "Dhanbad", "Jamshedpur", "Bokaro", "Deoghar"]),
    "Karnataka": (15.3173, 75.7139, ["Bengaluru", "Mysuru", "Belagavi", "Dharwad", "Mangaluru"]),
    "Kerala": (10.8505, 76.2711, ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam"]),
    "Madhya Pradesh": (22.9734, 78.6569, ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"]),
    "Maharashtra": (19.7515, 75.7139, ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"]),
    "Manipur": (24.6637, 93.9063, ["Imphal West", "Imphal East", "Thoubal", "Churachandpur"]),
    "Meghalaya": (25.4670, 91.3662, ["East Khasi Hills", "West Garo Hills", "Ri Bhoi"]),
    "Mizoram": (23.1645, 92.9376, ["Aizawl", "Lunglei", "Champhai"]),
    "Nagaland": (26.1584, 94.5624, ["Kohima", "Dimapur", "Mokokchung"]),
    "Odisha": (20.9517, 85.0985, ["Bhubaneswar", "Cuttack", "Ganjam", "Sambalpur", "Balasore"]),
    "Punjab": (31.1471, 75.3412, ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda"]),
    "Rajasthan": (27.0238, 74.2179, ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner"]),
    "Sikkim": (27.5330, 88.5122, ["East Sikkim", "West Sikkim", "South Sikkim", "North Sikkim"]),
    "Tamil Nadu": (11.1271, 78.6569, ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"]),
    "Telangana": (18.1124, 79.0193, ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"]),
    "Tripura": (23.9408, 91.9882, ["West Tripura", "South Tripura", "Dhalai"]),
    "Uttar Pradesh": (26.8467, 80.9462, ["Lucknow", "Kanpur", "Varanasi", "Agra", "Prayagraj", "Meerut"]),
    "Uttarakhand": (30.0668, 79.0193, ["Dehradun", "Haridwar", "Nainital", "Udham Singh Nagar"]),
    "West Bengal": (22.9868, 87.8550, ["Kolkata", "Howrah", "North 24 Parganas", "Darjeeling", "Murshidabad"]),
    "Delhi": (28.7041, 77.1025, ["Central Delhi", "South Delhi", "North Delhi", "East Delhi"]),
    "Jammu and Kashmir": (33.7782, 76.5762, ["Srinagar", "Jammu", "Anantnag", "Baramulla"]),
    "Ladakh": (34.1526, 77.5771, ["Leh", "Kargil"]),
    "Puducherry": (11.9416, 79.8083, ["Puducherry", "Karaikal"]),
    "Chandigarh": (30.7333, 76.7794, ["Chandigarh"]),
    "Andaman and Nicobar Islands": (11.7401, 92.6586, ["South Andaman", "North and Middle Andaman"]),
    "Dadra and Nagar Haveli and Daman and Diu": (20.1809, 73.0169, ["Daman", "Diu", "Dadra and Nagar Haveli"]),
    "Lakshadweep": (10.5667, 72.6417, ["Kavaratti"]),
}

PROJECT_TYPE_TEMPLATES = {
    "BUILDING": {
        "sector": "Education & Community",
        "min_cost": 250000,
        "max_cost": 4500000,
        "duration_days": (180, 540),
        "titles": [
            "Construction of Additional Classrooms at Govt High School",
            "Erection of Multi-Purpose Community Hall",
            "Establishment of Primary Health Sub-Centre Building",
            "Construction of Gram Panchayat Citizen Service Center",
            "Development of Anganwadi Center and Nutrition Hub",
            "Construction of Public Library and Reading Room"
        ]
    },
    "ROAD": {
        "sector": "Rural Connectivity & Transport",
        "min_cost": 300000,
        "max_cost": 3500000,
        "duration_days": (90, 365),
        "titles": [
            "Construction of Cement Concrete Road with Paver Blocks",
            "Bituminous Road from Main Highway to Scheduled Village",
            "Upgradation of Rural Link Road with Side Drains",
            "Laying of Interlocking Tile Pavement in Resettlement Colony",
            "Widening and Strengthening of Approach Road to Primary Health Centre"
        ]
    },
    "BRIDGE": {
        "sector": "Bridges & Culverts",
        "min_cost": 500000,
        "max_cost": 5000000,
        "duration_days": (240, 720),
        "titles": [
            "Construction of High-Level Submersible Bridge across Nullah",
            "R.C.C. Box Culvert for Agricultural Drainage and Crossing",
            "Construction of Foot Overbridge for School Commuters",
            "Major Causeway Reconstruction across Seasonal Stream"
        ]
    },
    "WATER_TANK": {
        "sector": "Drinking Water & Sanitation",
        "min_cost": 150000,
        "max_cost": 2000000,
        "duration_days": (60, 270),
        "titles": [
            "Installation of Solar Dual-Pump Piped Drinking Water System",
            "Construction of 50,000 Litre Overhead R.C.C. Water Storage Tank",
            "Deep Borewell with Submersible Motor and Public Distribution Cistern",
            "Installation of Community Water Purification RO Plant"
        ]
    }
}

AGENCIES = [
    "Public Works Department (PWD)",
    "Rural Engineering Services (RES)",
    "Panchayati Raj Engineering Division",
    "Zila Parishad Engineering Wing",
    "Irrigation & Flood Control Department",
    "Municipal Engineering Corporation",
    "State Bridge Construction Corporation",
    "Water Supply & Sanitation Board"
]

ANOMALY_CATEGORIES = [
    "UNUSUAL_FINANCIAL_PATTERN",
    "PAYMENT_PROGRESS_MISMATCH",
    "DELAY_PATTERN",
    "LOCATION_INCONSISTENCY",
    "POTENTIAL_SIMILARITY",
    "DOCUMENT_INCONSISTENCY",
    "REALITY_GAP"
]

def generate_synthetic_projects(
    count: int = 5000,
    seed: int = 42,
    anomaly_rate: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generates a deterministic synthetic dataset of MPLADS projects.
    Enforces structural financial and scheduling coherence for normal records,
    and deliberately injects controlled anomaly patterns for ML testing.
    """
    random.seed(seed)
    np.random.seed(seed)

    projects = []
    start_base = date(2021, 1, 15)
    today = date(2026, 9, 19)

    state_names = list(STATE_CENTROIDS.keys())
    project_types = list(PROJECT_TYPE_TEMPLATES.keys())

    # Pre-determine which project indices will be anomalies
    num_anomalies = int(count * anomaly_rate)
    anomaly_indices = set(random.sample(range(count), num_anomalies))

    for idx in range(count):
        proj_id = f"SYN-PRJ-{idx+1:05d}"
        is_anomaly = idx in anomaly_indices

        # Geographic assignment
        state_name = random.choice(state_names)
        lat_base, lng_base, districts = STATE_CENTROIDS[state_name]
        district = random.choice(districts)
        constituency = f"{district} Parliamentary Constituency"
        block = f"{district} Block-{random.randint(1, 5)}"
        village = f"Village {random.choice(['Rampur', 'Sundarpur', 'Shivnagar', 'Kalyanpur', 'Mohanpur', 'Adarsh Nagar', 'Gandhi Gram'])}"

        # Deterministic coordinate jitter (within ~15-20km)
        lat = round(lat_base + np.random.normal(0, 0.12), 6)
        lng = round(lng_base + np.random.normal(0, 0.12), 6)

        # Type & Template
        ptype = random.choice(project_types)
        tmpl = PROJECT_TYPE_TEMPLATES[ptype]
        work_title = f"{random.choice(tmpl['titles'])} at {village}"
        sector = tmpl["sector"]
        agency = random.choice(AGENCIES)

        # Dates & Timeline
        planned_duration = random.randint(tmpl["duration_days"][0], tmpl["duration_days"][1])
        start_offset_days = random.randint(0, 1400)
        start_d = start_base + timedelta(days=start_offset_days)
        exp_completion_d = start_d + timedelta(days=planned_duration)

        # Financials (Base)
        sanction = round(random.uniform(tmpl["min_cost"], tmpl["max_cost"]) / 5000.0) * 5000.0
        
        # Determine status and progress
        if exp_completion_d < today:
            # Should have completed
            is_delayed = random.random() < 0.35
            if is_delayed:
                status = "DELAYED"
                reported_progress = round(random.uniform(35.0, 85.0), 1)
                actual_completion_d = None
            else:
                status = "COMPLETED"
                reported_progress = 100.0
                delay_days = random.randint(-30, 45)
                actual_completion_d = exp_completion_d + timedelta(days=delay_days)
        else:
            # Ongoing
            status = "IN_PROGRESS"
            elapsed = max(1, (today - start_d).days)
            expected_ratio = min(1.0, elapsed / planned_duration)
            reported_progress = round(min(98.0, max(5.0, expected_ratio * 100.0 + random.uniform(-10, 10))), 1)
            actual_completion_d = None

        # Coherent Financial Relationships in Normal Cases
        # sanction >= released >= expenditure
        released_ratio = min(1.0, (reported_progress / 100.0) + random.uniform(0.1, 0.25))
        released = round(min(sanction, max(sanction * 0.4, sanction * released_ratio)) / 1000.0) * 1000.0
        
        exp_ratio = min(1.0, (reported_progress / 100.0) * random.uniform(0.85, 1.0))
        expenditure = round(min(released, released * exp_ratio) / 1000.0) * 1000.0

        # Physical Observation (null in normal cases if no field evidence)
        observed_progress = None
        observed_status = "NOT_AVAILABLE"

        # Default normal anomaly label
        anomaly_label = 0
        anomaly_cat = "NORMAL"

        # -------------------------------------------------------------
        # INJECT CONTROLLED ANOMALY IF SELECTED
        # -------------------------------------------------------------
        if is_anomaly:
            anomaly_label = 1
            anomaly_cat = random.choice(ANOMALY_CATEGORIES)

            if anomaly_cat == "PAYMENT_PROGRESS_MISMATCH":
                # High expenditure, low progress
                expenditure = round(released * random.uniform(0.88, 1.0) / 1000.0) * 1000.0
                reported_progress = round(random.uniform(10.0, 28.0), 1)
                status = "IN_PROGRESS"
            elif anomaly_cat == "UNUSUAL_FINANCIAL_PATTERN":
                # Expenditure exceeds released or extreme unspent surge
                if random.random() < 0.5:
                    expenditure = round(released * 1.15 / 1000.0) * 1000.0  # Overdraft
                else:
                    released = sanction
                    expenditure = round(sanction * 0.05)  # 95% unspent after 2 years
            elif anomaly_cat == "DELAY_PATTERN":
                # Severe overrun (>18 months overdue)
                start_d = date(2021, 3, 1)
                exp_completion_d = date(2022, 6, 1)
                status = "STALLED"
                reported_progress = round(random.uniform(20.0, 45.0), 1)
                actual_completion_d = None
            elif anomaly_cat == "LOCATION_INCONSISTENCY":
                # Coordinates far outside state
                lat = round(lat + random.choice([-8.5, 8.5]), 6)
                lng = round(lng + random.choice([-8.5, 8.5]), 6)
            elif anomaly_cat == "REALITY_GAP":
                # Agency claims 100% complete, ground observation shows 30%
                reported_progress = 100.0
                status = "COMPLETED"
                observed_progress = round(random.uniform(25.0, 40.0), 1)
                observed_status = "OFFICER_VERIFIED"
            elif anomaly_cat == "POTENTIAL_SIMILARITY":
                # Repeated title in same village
                work_title = f"Construction of Community Hall and Center at {village} (Phase-{random.randint(1, 2)})"
            elif anomaly_cat == "DOCUMENT_INCONSISTENCY":
                # Expenditure reported high but sanction released low
                sanction = 1500000.0
                released = 500000.0
                expenditure = 1200000.0

        project_record = {
            "project_id": proj_id,
            "project_name": work_title,
            "project_type": ptype,
            "sector": sector,
            "state": state_name,
            "district": district,
            "constituency": constituency,
            "block": block,
            "village": village,
            "latitude": lat,
            "longitude": lng,
            "sanction_amount": sanction,
            "released_amount": released,
            "expenditure_amount": expenditure,
            "start_date": start_d,
            "expected_completion_date": exp_completion_d,
            "actual_completion_date": actual_completion_d,
            "reported_progress": reported_progress,
            "observed_progress": observed_progress,
            "observed_progress_status": observed_status,
            "status": status,
            "agency": agency,
            "data_status": "SYNTHETIC",
            "source_type": "SYNTHETIC_TEST_DATA",
            "data_availability_status": "SYNTHETIC",
            "anomaly_label": anomaly_label,
            "anomaly_category": anomaly_cat,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        projects.append(project_record)

    return projects
