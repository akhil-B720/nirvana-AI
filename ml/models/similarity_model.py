import math
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

class SimilarityEngine:
    """
    Evaluates project duplicate candidates and overlap risks using
    TF-IDF textual cosine similarity combined with geodesic Haversine spatial proximity.
    """

    def __init__(self, geo_distance_threshold_km: float = 0.5, combined_threshold: float = 0.70):
        self.geo_distance_threshold_km = geo_distance_threshold_km
        self.combined_threshold = combined_threshold
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.is_fitted = False
        self.project_ids: List[str] = []
        self.tfidf_matrix = None
        self.projects_meta: List[Dict[str, Any]] = []

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        if any(v is None for v in (lat1, lon1, lat2, lon2)):
            return None
        try:
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return 6371.0 * c
        except Exception:
            return None

    def fit(self, projects: List[Any]) -> Dict[str, Any]:
        if not projects:
            return {"status": "INSUFFICIENT_DATA", "num_projects": 0}

        corpus = []
        self.project_ids = []
        self.projects_meta = []

        for p in projects:
            self.project_ids.append(p.project_id)
            text_tokens = f"{p.project_name} {p.sector or ''} {p.project_type} {p.district} {p.block or ''} {p.village or ''}"
            corpus.append(text_tokens)
            self.projects_meta.append({
                "project_id": p.project_id,
                "project_name": p.project_name,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "sanction_amount": p.sanction_amount,
                "village": p.village,
                "block": p.block
            })

        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True
        return {"status": "ACTIVE", "num_projects": len(projects)}

    def find_similar(self, target_project, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.is_fitted or self.tfidf_matrix is None:
            return []

        target_text = f"{target_project.project_name} {target_project.sector or ''} {target_project.project_type} {target_project.district} {target_project.block or ''} {target_project.village or ''}"
        target_vec = self.vectorizer.transform([target_text])
        text_sims = cosine_similarity(target_vec, self.tfidf_matrix)[0]

        matches = []
        for i, other_meta in enumerate(self.projects_meta):
            if other_meta["project_id"] == target_project.project_id:
                continue

            text_sim = float(text_sims[i])

            # Geodesic proximity
            dist_km = self.haversine_km(
                target_project.latitude, target_project.longitude,
                other_meta["latitude"], other_meta["longitude"]
            )

            if dist_km is not None:
                # 0 km = 1.0, 5 km = 0.0
                geo_sim = max(0.0, 1.0 - (dist_km / 5.0))
                # Weighted combination: 60% text, 40% geographic
                combined = round(0.6 * text_sim + 0.4 * geo_sim, 3)
            else:
                geo_sim = None
                combined = round(text_sim, 3)

            is_potentially_similar = combined >= self.combined_threshold or (text_sim > 0.85)

            if is_potentially_similar or text_sim > 0.4:
                matches.append({
                    "compared_project_id": other_meta["project_id"],
                    "compared_project_name": other_meta["project_name"],
                    "text_similarity": round(text_sim, 3),
                    "geo_similarity": round(geo_sim, 3) if geo_sim is not None else None,
                    "distance_km": round(dist_km, 3) if dist_km is not None else None,
                    "combined_similarity": combined,
                    "status_label": "potentially_similar" if is_potentially_similar else "low_similarity"
                })

        matches.sort(key=lambda x: x["combined_similarity"], reverse=True)
        return matches[:top_k]

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)
