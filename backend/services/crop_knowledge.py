"""
Crop Knowledge Model — transparent compatibility scoring.

Converts the raw dataset into a clean internal representation for:
- crop compatibility scoring
- field matching
- crop ranking
- agricultural RAG
- explainable recommendations

Does NOT use arbitrary weighted averages. Uses transparent per-parameter
scoring with explicit match/constraint reporting.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import csv
import re

DATASET_PATH = "backend/datasets/agromind_master_dataset_full (1).csv"

@dataclass(unsafe_hash=True)
class CropRequirement:
    """Normalized crop requirement from dataset."""
    crop: str
    category: str
    soil_type: str
    nitrogen_min: float
    nitrogen_max: float
    phosphorus_min: float
    phosphorus_max: float
    potassium_min: float
    potassium_max: float
    ph_min: float
    ph_max: float
    temp_min: float
    temp_max: float
    humidity_min: float
    humidity_max: float
    rain_min: float
    rain_max: float
    moisture_min: float
    moisture_max: float
    season: str

    def __post_init__(self):
        # Normalize season
        self.season = self.season.strip().lower().replace("___", "/").replace("__", "/")

    @property
    def nitrogen_range(self) -> Tuple[float, float]:
        return (self.nitrogen_min, self.nitrogen_max)

    @property
    def phosphorus_range(self) -> Tuple[float, float]:
        return (self.phosphorus_min, self.phosphorus_max)

    @property
    def potassium_range(self) -> Tuple[float, float]:
        return (self.potassium_min, self.potassium_max)

    @property
    def ph_range(self) -> Tuple[float, float]:
        return (self.ph_min, self.ph_max)

    @property
    def temp_range(self) -> Tuple[float, float]:
        return (self.temp_min, self.temp_max)

    @property
    def humidity_range(self) -> Tuple[float, float]:
        return (self.humidity_min, self.humidity_max)

    @property
    def rain_range(self) -> Tuple[float, float]:
        return (self.rain_min, self.rain_max)

    @property
    def moisture_range(self) -> Tuple[float, float]:
        return (self.moisture_min, self.moisture_max)

    def in_range(self, value: Optional[float], lo: float, hi: float) -> bool:
        if value is None:
            return False
        return lo <= value <= hi

    def parameter_score(self, field_value: Optional[float], lo: float, hi: float, weight: float = 1.0) -> float:
        """Score 0-1 for how well field value fits crop range."""
        if field_value is None:
            return 0.5 * weight  # unknown = neutral, weighted
        lo, hi = float(lo), float(hi)
        if lo <= field_value <= hi:
            return 1.0 * weight
        # Penalty proportional to distance from range
        if field_value < lo:
            dist = (lo - field_value) / max(lo, 1)
        else:
            dist = (field_value - hi) / max(hi, 1)
        return max(0.0, 1.0 - dist * 2) * weight


class CropKnowledgeBase:
    """Crop knowledge base loaded from dataset with transparent scoring."""

    def __init__(self):
        self.crops: List[CropRequirement] = []
        self._load_dataset()

    def _load_dataset(self):
        path = Path(DATASET_PATH)
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    crop = CropRequirement(
                        crop=row['crop'].strip(),
                        category=row.get('category', 'Unknown').strip(),
                        soil_type=row['soil_type'].strip(),
                        nitrogen_min=float(row['nitrogen_min']),
                        nitrogen_max=float(row['nitrogen_max']),
                        phosphorus_min=float(row['phosphorus_min']),
                        phosphorus_max=float(row['phosphorus_max']),
                        potassium_min=float(row['potassium_min']),
                        potassium_max=float(row['potassium_max']),
                        ph_min=float(row['ph_min']),
                        ph_max=float(row['ph_max']),
                        temp_min=float(row['temp_min']),
                        temp_max=float(row['temp_max']),
                        humidity_min=float(row['humidity_min']),
                        humidity_max=float(row['humidity_max']),
                        rain_min=float(row['rain_min']),
                        rain_max=float(row['rain_max']),
                        moisture_min=float(row['moisture_min']),
                        moisture_max=float(row['moisture_max']),
                        season=row['season'].strip(),
                    )
                    self.crops.append(crop)
                except Exception as e:
                    print(f"Skipping row {row.get('crop', 'unknown')}: {e}")

    def score_crop(self, field_params: Dict[str, Optional[float]]) -> List[Dict]:
        """
        Score all crops against field parameters.
        Returns sorted list with transparent scoring breakdown.
        """
        results = []
        weights = {
            'nitrogen': 0.20,
            'phosphorus': 0.15,
            'potassium': 0.15,
            'ph': 0.20,
            'temperature': 0.10,
            'humidity': 0.05,
            'rainfall': 0.10,
            'moisture': 0.05,
        }

        for crop in self.crops:
            scores = {}
            matched = []
            constraints = []

            # Nitrogen
            n_val = field_params.get('nitrogen')
            n_score = crop.parameter_score(field_params.get('nitrogen'), crop.nitrogen_min, crop.nitrogen_max, weights['nitrogen'])
            if field_params.get('nitrogen') is not None:
                if crop.nitrogen_min <= field_params['nitrogen'] <= crop.nitrogen_max:
                    matched.append(f"Nitrogen {field_params['nitrogen']} in range [{crop.nitrogen_min}, {crop.nitrogen_max}]")
                elif field_params['nitrogen'] < crop.nitrogen_min:
                    constraints.append(f"Nitrogen {field_params['nitrogen']} below minimum {crop.nitrogen_min}")
                else:
                    constraints.append(f"Nitrogen {field_params['nitrogen']} above maximum {crop.nitrogen_max}")

            # Phosphorus
            p_score = crop.parameter_score(field_params.get('phosphorus'), crop.phosphorus_min, crop.phosphorus_max, weights['phosphorus'])

            # Potassium
            k_score = crop.parameter_score(field_params.get('potassium'), crop.potassium_min, crop.potassium_max, weights['potassium'])

            # pH
            ph_score = crop.parameter_score(field_params.get('ph'), crop.ph_min, crop.ph_max, weights['ph'])

            # Temperature
            t_score = crop.parameter_score(field_params.get('temperature'), crop.temp_min, crop.temp_max, weights['temperature'])

            # Humidity
            h_score = crop.parameter_score(field_params.get('humidity'), crop.humidity_min, crop.humidity_max, weights['humidity'])

            # Rainfall
            r_score = crop.parameter_score(field_params.get('rainfall'), crop.rain_min, crop.rain_max, weights['rainfall'])

            # Moisture
            m_score = crop.parameter_score(field_params.get('moisture'), crop.moisture_min, crop.moisture_max, weights['moisture'])

            total = n_score + p_score + k_score + ph_score + t_score + h_score + r_score + m_score
            confidence = total / sum(weights.values())

            results.append({
                'crop': crop.crop,
                'category': crop.category,
                'season': crop.season,
                'soil_type': crop.soil_type,
                'compatibility': round(confidence * 100, 1),
                'matched': matched,
                'constraints': constraints,
                'scores': {
                    'nitrogen': round(n_score/weights['nitrogen']*100, 1) if field_params.get('nitrogen') else None,
                    'phosphorus': round(p_score/weights['phosphorus']*100, 1) if field_params.get('phosphorus') else None,
                    'potassium': round(k_score/weights['potassium']*100, 1) if field_params.get('potassium') else None,
                    'ph': round(ph_score/weights['ph']*100, 1) if field_params.get('ph') else None,
                    'temperature': round(t_score/weights['temperature']*100, 1) if field_params.get('temperature') else None,
                    'humidity': round(h_score/weights['humidity']*100, 1) if field_params.get('humidity') else None,
                    'rainfall': round(r_score/weights['rainfall']*100, 1) if field_params.get('rainfall') else None,
                    'moisture': round(m_score/weights['moisture']*100, 1) if field_params.get('moisture') else None,
                }
            })

        results.sort(key=lambda x: x['compatibility'], reverse=True)
        return results

    def get_crop_detail(self, crop_name: str) -> Optional[CropRequirement]:
        for c in self.crops:
            if c.crop.lower() == crop_name.lower():
                return c
        return None

    def get_compatible_crops(self, field_params: Dict[str, Optional[float]], top_n: int = 5) -> List[Dict]:
        return self.score_crop(field_params)[:top_n]


# Singleton instance
_crop_kb = None

def get_crop_knowledge_base() -> CropKnowledgeBase:
    global _crop_kb
    if _crop_kb is None:
        _crop_kb = CropKnowledgeBase()
    return _crop_kb


# Example usage for testing
if __name__ == "__main__":
    kb = get_crop_knowledge_base()
    print(f"Loaded {len(kb.crops)} crops")

    # Test with sample field data
    field = {
        'nitrogen': 60,
        'phosphorus': 30,
        'potassium': 40,
        'ph': 6.5,
        'temperature': 28,
        'humidity': 70,
        'rainfall': 1200,
        'moisture': 50,
    }
    top = kb.get_compatible_crops(field, 5)
    for r in top:
        print(f"{r['crop']}: {r['compatibility']}% - Matched: {r['matched']} | Constraints: {r['constraints']}")