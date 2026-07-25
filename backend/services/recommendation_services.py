"""
recommendation_services.py
===========================================================
AgroMind - Rule-Based Crop Recommendation Engine
===========================================================

This module is the core recommendation service for AgroMind. It ingests a
structured soil test report (already OCR-extracted and parsed upstream) and
compares it against a master crop dataset of ~1200 crops using a weighted,
rule-based scoring model. It returns the Top 5 most suitable crops with a
full breakdown of parameter-level scores, environmental requirements, and a
dynamically generated human-readable summary.

No machine learning is used. This is a deterministic, explainable expert
system, which is a deliberate design choice for an agricultural advisory
context where farmers and agronomists need to trust and audit every score.

-----------------------------------------------------------------------------
IMPORTANT DATA MAPPING NOTE (read before deploying)
-----------------------------------------------------------------------------
The soil report schema scores five parameters: nitrogen, phosphorus,
potassium, ph, and organic_matter. The master dataset schema supplied in the
project spec defines range columns for nitrogen, phosphorus, potassium, and
ph, but does NOT define an explicit `organic_matter_min` / `organic_matter_max`
column pair -- the only remaining unmapped soil-range columns in the dataset
are `moisture_min` / `moisture_max`.

Because organic matter is a required, weighted (10%) scoring dimension and
cannot be silently dropped, this module maps `organic_matter` to the
dataset's `moisture_min` / `moisture_max` columns as the closest available
proxy for organic content requirements. This mapping is isolated to a single
constant (`ORGANIC_MATTER_DATASET_COLUMNS`) so that if/when the dataset is
updated with true `organic_matter_min` / `organic_matter_max` columns, only
that one constant needs to change -- no scoring logic is affected.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import pandas as pd

logger = logging.getLogger("agromind.recommendation_services")
logger.addHandler(logging.NullHandler())

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_DATASET_PATH: str = "datasets/agromind_master_dataset_full.csv"

#: Weight assigned to each scored soil parameter. Must sum to 100.
PARAMETER_WEIGHTS: Dict[str, float] = {
    "nitrogen": 35.0,
    "phosphorus": 25.0,
    "potassium": 20.0,
    "ph": 20.0,
}

#: Maps a soil_data parameter name to the (min_column, max_column) pair in
#: the crop dataset used to evaluate it. See module docstring for the
#: organic_matter -> moisture mapping rationale.
PARAMETER_DATASET_COLUMNS: Dict[str, Tuple[str, str]] = {
    "nitrogen": ("nitrogen_min", "nitrogen_max"),
    "phosphorus": ("phosphorus_min", "phosphorus_max"),
    "potassium": ("potassium_min", "potassium_max"),
    "ph": ("ph_min", "ph_max"),
}

#: All columns required to be present in the dataset for the engine to run.
REQUIRED_DATASET_COLUMNS: List[str] = [
    "crop",
    "soil_type",
    "nitrogen_min", "nitrogen_max",
    "phosphorus_min", "phosphorus_max",
    "potassium_min", "potassium_max",
    "ph_min", "ph_max",
    "temp_min", "temp_max",
    "humidity_min", "humidity_max",
    "rain_min", "rain_max",
    "moisture_min", "moisture_max",
    "season",
]

#: Required keys in the incoming parsed soil_data payload.
REQUIRED_SOIL_KEYS: List[str] = [
    "nitrogen", "phosphorus", "potassium", "ph",
]

#: Sane physical bounds used purely for input sanity-checking (not scoring).
SOIL_VALUE_SANITY_BOUNDS = {
    "nitrogen": (0.0, 1000.0),
    "phosphorus": (0.0, 1000.0),
    "potassium": (0.0, 1000.0),
    "ph": (0.0, 14.0),
}

TOP_N_RESULTS: int = 5

# Distance-from-range tiers -> percentage credit awarded.
# Ordered as (upper_bound_of_distance_percentage, percentage_awarded).
DISTANCE_SCORING_TIERS: List[Tuple[float, float]] = [
    (0.0, 100.0),   # inside range
    (5.0, 90.0),    # 0-5% outside
    (10.0, 75.0),   # 5-10% outside
    (20.0, 50.0),   # 10-20% outside
    (math.inf, 0.0),  # more than 20% outside
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class ParameterScoreResult:
    """Container for a single parameter's scoring outcome."""

    score: float
    max_score: float
    percentage: float
    status: str

    current_value: float
    ideal_min: float
    ideal_max: float

    comparison: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 2) if self.score % 1 else int(self.score),
            "max_score": int(self.max_score) if self.max_score % 1 == 0 else self.max_score,
            "percentage": round(self.percentage, 2) if self.percentage % 1 else int(self.percentage),
            "status": self.status,
            "current_value": self.current_value,
            "ideal_min": self.ideal_min,
            "ideal_max": self.ideal_max,
            "comparison": self.comparison,
        }


# =============================================================================
# EXCEPTIONS
# =============================================================================

class DatasetError(Exception):
    """Raised when the crop dataset cannot be loaded or is structurally invalid."""


class SoilDataValidationError(Exception):
    """Raised when the incoming parsed soil_data payload fails validation."""


# =============================================================================
# DATASET LOADING
# =============================================================================

@lru_cache(maxsize=4)
def load_crop_dataset(dataset_path: str = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """
    Load and validate the master crop dataset from disk.

    The result is cached per dataset_path so repeated recommendation calls
    within the same process do not re-read the CSV from disk each time.

    :param dataset_path: Filesystem path to the crop dataset CSV.
    :return: A validated, numeric-coerced pandas DataFrame.
    :raises DatasetError: If the file is missing, unreadable, empty, missing
        required columns, or contains no usable rows after cleaning.
    """
    try:
        df = pd.read_csv(dataset_path)
    except FileNotFoundError as exc:
        raise DatasetError(f"Crop dataset not found at path: {dataset_path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise DatasetError(f"Crop dataset at {dataset_path} is empty.") from exc
    except pd.errors.ParserError as exc:
        raise DatasetError(f"Crop dataset at {dataset_path} could not be parsed as CSV.") from exc

    if df.empty:
        raise DatasetError(f"Crop dataset at {dataset_path} contains no rows.")

    missing_columns = [col for col in REQUIRED_DATASET_COLUMNS if col not in df.columns]
    if missing_columns:
        raise DatasetError(
            f"Crop dataset is missing required columns: {missing_columns}"
        )

    numeric_columns = [
        col for col in REQUIRED_DATASET_COLUMNS
        if col not in ("crop", "soil_type", "season")
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["crop"] = df["crop"].astype(str).str.strip()

    before_count = len(df)
    df = df.dropna(subset=numeric_columns + ["crop"])
    df = df[df["crop"] != ""]
    dropped = before_count - len(df)
    if dropped > 0:
        logger.warning(
            "Dropped %d row(s) from crop dataset due to missing/invalid numeric "
            "values or missing crop name.",
            dropped,
        )

    invalid_range_mask = (
        (df["nitrogen_min"] > df["nitrogen_max"]) |
        (df["phosphorus_min"] > df["phosphorus_max"]) |
        (df["potassium_min"] > df["potassium_max"]) |
        (df["ph_min"] > df["ph_max"]) |
        (df["moisture_min"] > df["moisture_max"])
    )
    if invalid_range_mask.any():
        logger.warning(
            "Dropped %d row(s) from crop dataset due to inverted min/max ranges.",
            int(invalid_range_mask.sum()),
        )
        df = df[~invalid_range_mask]

    if df.empty:
        raise DatasetError(
            f"Crop dataset at {dataset_path} had no valid rows after cleaning."
        )

    return df.reset_index(drop=True)


# =============================================================================
# SOIL DATA VALIDATION
# =============================================================================

def validate_soil_data(soil_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Validate and normalize the parsed soil_data payload.

    :param soil_data: Raw dict, expected to contain a "soil_parameters" key
        (per the parser's documented output) OR the flat parameter keys
        directly. Both shapes are accepted for robustness.
    :return: A dict of the five soil parameters as clean floats.
    :raises SoilDataValidationError: If required keys are missing, values are
        non-numeric, negative, or outside sane physical bounds.
    """
    if not isinstance(soil_data, dict):
        raise SoilDataValidationError(
            f"soil_data must be a dict, got {type(soil_data).__name__}."
        )

    parameters = soil_data.get("soil_parameters", soil_data)
    if not isinstance(parameters, dict):
        raise SoilDataValidationError(
            "soil_data['soil_parameters'] must be a dict of soil parameter values."
        )

    missing_keys = [key for key in REQUIRED_SOIL_KEYS if key not in parameters]
    if missing_keys:
        raise SoilDataValidationError(
            f"soil_data is missing required parameter(s): {missing_keys}"
        )

    validated: Dict[str, float] = {}
    for key in REQUIRED_SOIL_KEYS:
        raw_value = parameters[key]

        if raw_value is None:
            raise SoilDataValidationError(f"soil parameter '{key}' is missing (null).")

        if isinstance(raw_value, bool):
            raise SoilDataValidationError(
                f"soil parameter '{key}' must be numeric, got boolean."
            )

        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise SoilDataValidationError(
                f"soil parameter '{key}' must be numeric, got: {raw_value!r}"
            ) from exc

        if math.isnan(value) or math.isinf(value):
            raise SoilDataValidationError(
                f"soil parameter '{key}' has an invalid numeric value: {raw_value!r}"
            )

        if value < 0:
            raise SoilDataValidationError(
                f"soil parameter '{key}' cannot be negative, got: {value}"
            )

        lower_bound, upper_bound = SOIL_VALUE_SANITY_BOUNDS[key]
        if not (lower_bound <= value <= upper_bound):
            raise SoilDataValidationError(
                f"soil parameter '{key}' value {value} is outside plausible "
                f"bounds [{lower_bound}, {upper_bound}]."
            )

        validated[key] = value

    return validated


# =============================================================================
# SCORING PRIMITIVES
# =============================================================================

def calculate_distance_percentage(value: float, min_val: float, max_val: float) -> float:
    """
    Calculate how far a value lies outside an acceptable [min_val, max_val]
    range, expressed as a percentage of the range's span.

    Returns 0.0 if the value lies inside the range (inclusive).

    :param value: The measured soil value.
    :param min_val: Lower bound of the crop's acceptable range.
    :param max_val: Upper bound of the crop's acceptable range.
    :return: Non-negative percentage distance from the nearest boundary.
    """
    if min_val <= value <= max_val:
        return 0.0

    range_span = max_val - min_val
    if range_span <= 0:
        # Degenerate range (min == max, or invalid). Fall back to comparing
        # the absolute distance against the boundary value itself so we
        # never divide by zero and still produce a meaningful signal.
        reference = max_val if max_val != 0 else 1.0
        distance = abs(value - max_val)
        return (distance / abs(reference)) * 100.0

    distance = (min_val - value) if value < min_val else (value - max_val)
    return (distance / range_span) * 100.0


def _distance_to_percentage_score(distance_percentage: float) -> float:
    """Map a distance-from-range percentage to its awarded percentage score."""
    for upper_bound, awarded_percentage in DISTANCE_SCORING_TIERS:
        if distance_percentage <= upper_bound:
            return awarded_percentage
    return 0.0  # unreachable given math.inf sentinel, kept for safety


def score_parameter(
    value: float, min_val: float, max_val: float, weight: float
) -> ParameterScoreResult:
    """
    Score a single soil parameter against a crop's acceptable range.

    :param value: The farmer's measured soil value for this parameter.
    :param min_val: Crop's minimum acceptable value.
    :param max_val: Crop's maximum acceptable value.
    :param weight: Maximum score (weight) allotted to this parameter.
    :return: A ParameterScoreResult with score, max_score, percentage, status.
    """
    distance_percentage = calculate_distance_percentage(value, min_val, max_val)
    awarded_percentage = _distance_to_percentage_score(distance_percentage)
    score = weight * (awarded_percentage / 100.0)
    status = parameter_status(awarded_percentage)

# Determine whether the value is below, within, or above the ideal range
    if value < min_val:
      comparison = "below"
    elif value > max_val:
      comparison = "above"
    else:
       comparison = "within"

    return ParameterScoreResult(
    score=score,
    max_score=weight,
    percentage=awarded_percentage,
    status=status,
    current_value=value,
    ideal_min=min_val,
    ideal_max=max_val,
    comparison=comparison,
)


def parameter_status(percentage: float) -> str:
    """
    Convert a parameter's awarded percentage score into a status label.

    :param percentage: Awarded percentage score (0-100).
    :return: One of "Excellent", "Good", "Moderate", "Poor".
    """
    if percentage >= 100:
        return "Excellent"
    if percentage >= 90:
        return "Good"
    if percentage >= 50:
        return "Moderate"
    return "Poor"


# =============================================================================
# SCORE -> LABEL CONVERTERS
# =============================================================================

def score_to_stars(score: float) -> int:
    """Convert an overall suitability score (0-100) into a 1-5 star rating."""
    if score >= 90:
        return 5
    if score >= 80:
        return 4
    if score >= 70:
        return 3
    if score >= 60:
        return 2
    return 1


def score_to_match(score: float) -> str:
    """Convert an overall suitability score (0-100) into a match label."""
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Very Good"
    if score >= 70:
        return "Good"
    if score >= 60:
        return "Fair"
    return "Poor"


def score_to_confidence(score: float) -> str:
    """Convert an overall suitability score (0-100) into a confidence label."""
    if score >= 90:
        return "Highly Recommended"
    if score >= 80:
        return "Recommended"
    if score >= 70:
        return "Suitable"
    if score >= 60:
        return "Moderately Suitable"
    return "Low Suitability"


# =============================================================================
# SUMMARY GENERATION
# =============================================================================

_STRENGTH_TEMPLATES: Dict[str, Dict[str, str]] = {
    "nitrogen": {
        "Excellent": "Nitrogen is within the ideal range.",
        "Good": "Nitrogen is close to the ideal range for this crop.",
    },
    "phosphorus": {
        "Excellent": "Phosphorus levels are perfectly suited for this crop.",
        "Good": "Phosphorus levels are close to suitable for this crop.",
    },
    "potassium": {
        "Excellent": "Potassium is within the ideal range.",
        "Good": "Potassium is suitable for optimal growth.",
    },
    "ph": {
        "Excellent": "Soil pH perfectly matches crop requirements.",
        "Good": "Soil pH is close to the crop's preferred range.",
    },
    
}

_IMPROVEMENT_TEMPLATES: Dict[str, Dict[str, Dict[str, str]]] = {
    "nitrogen": {
        "below": {
            "Moderate": "Increase nitrogen slightly using organic manure or urea.",
            "Poor": "Nitrogen is critically low. Apply nitrogen-rich fertilizers such as urea or compost."
        },
        "above": {
            "Moderate": "Nitrogen is slightly higher than recommended. Reduce nitrogen fertilizer application.",
            "Poor": "Nitrogen is excessively high. Avoid applying additional nitrogen fertilizers."
        }
    },

    "phosphorus": {
        "below": {
            "Moderate": "Increase phosphorus slightly using SSP or DAP fertilizer.",
            "Poor": "Phosphorus is critically low. Apply phosphorus-rich fertilizers before cultivation."
        },
        "above": {
            "Moderate": "Phosphorus is slightly above the ideal range. Avoid adding phosphorus fertilizer.",
            "Poor": "Phosphorus is excessively high. Stop phosphate fertilizer application until levels normalize."
        }
    },

    "potassium": {
        "below": {
            "Moderate": "Increase potassium slightly using MOP or wood ash.",
            "Poor": "Potassium is critically low. Apply potassium-rich fertilizers before cultivation."
        },
        "above": {
            "Moderate": "Potassium is slightly above the ideal range. Reduce potassium fertilizer application.",
            "Poor": "Potassium is excessively high. Avoid additional potassium fertilizers."
        }
    },

    "ph": {
        "below": {
            "Moderate": "The soil is slightly acidic. Apply agricultural lime to raise the pH.",
            "Poor": "The soil is highly acidic. Correct the pH using agricultural lime before planting."
        },
        "above": {
            "Moderate": "The soil is slightly alkaline. Apply elemental sulfur to lower the pH.",
            "Poor": "The soil is highly alkaline. Reduce the soil pH before cultivation using suitable amendments."
        }
    }
}

_PARAMETER_DISPLAY_NAMES: Dict[str, str] = {
    "nitrogen": "Nitrogen",
    "phosphorus": "Phosphorus",
    "potassium": "Potassium",
    "ph": "Soil pH",
    
}


def generate_summary(parameter_scores: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Dynamically generate a human-readable strengths/improvements summary
    from actual parameter scoring results. No statements are hardcoded per
    crop -- every sentence is derived from the real status of each parameter.

    :param parameter_scores: Mapping of parameter name -> its scored dict
        (must contain "status").
    :return: Dict with "strengths" and "improvements" string lists.
    """
    strengths: List[str] = []
    improvements: List[str] = []

    for param_name, result in parameter_scores.items():
        status = result["status"]
        display_name = _PARAMETER_DISPLAY_NAMES.get(param_name, param_name.title())

        if status in ("Excellent", "Good"):
            template = _STRENGTH_TEMPLATES.get(param_name, {}).get(status)
            strengths.append(template or f"{display_name} is suitable for this crop.")
        else:
         comparison = result.get("comparison", "below")

    template = (
        _IMPROVEMENT_TEMPLATES
        .get(param_name, {})
        .get(comparison, {})
        .get(status)
    )

    improvements.append(
        template or f"Improve {display_name} to better match this crop's needs."
    )

    return {"strengths": strengths, "improvements": improvements}


# =============================================================================
# CROP SCORING
# =============================================================================

def calculate_crop_score(
    soil_data: Dict[str, float], crop_row: "pd.Series"
) -> Tuple[Dict[str, Dict[str, Any]], float]:
    """
    Compute the full parameter-level scoring breakdown and total suitability
    score for a single crop row.

    :param soil_data: Validated soil parameter values.
    :param crop_row: A single row (pandas Series) from the crop dataset.
    :return: Tuple of (parameter_scores dict keyed by parameter name, total
        overall score out of 100).
    """
    parameter_scores: Dict[str, Dict[str, Any]] = {}
    total_score = 0.0

    for param_name, weight in PARAMETER_WEIGHTS.items():
        min_col, max_col = PARAMETER_DATASET_COLUMNS[param_name]
        min_val = float(crop_row[min_col])
        max_val = float(crop_row[max_col])
        value = soil_data[param_name]

        result = score_parameter(value, min_val, max_val, weight)
        parameter_scores[param_name] = result.to_dict()
        total_score += result.score

    return parameter_scores, total_score


# =============================================================================
# RECOMMENDATION OBJECT ASSEMBLY
# =============================================================================

def build_recommendation(
    crop_row: "pd.Series",
    parameter_scores: Dict[str, Dict[str, Any]],
    total_score: float,
) -> Dict[str, Any]:
    """
    Assemble the final recommendation object for a single crop, matching the
    exact JSON schema required by the frontend.

    :param crop_row: The crop dataset row this recommendation is built from.
    :param parameter_scores: Output of calculate_crop_score's first element.
    :param total_score: Output of calculate_crop_score's second element.
    :return: A fully populated recommendation dict.
    """
    rounded_score = int(round(total_score))
    rounded_score = max(0, min(100, rounded_score))

    return {
        "crop": str(crop_row["crop"]),
        "score": rounded_score,
        "stars": score_to_stars(rounded_score),
        "match": score_to_match(rounded_score),
        "confidence": score_to_confidence(rounded_score),
        "parameter_scores": parameter_scores,
        "recommended_environment": {
            "soil_type": str(crop_row["soil_type"]),
            "temperature": f"{_fmt_num(crop_row['temp_min'])}-{_fmt_num(crop_row['temp_max'])}°C",
            "humidity": f"{_fmt_num(crop_row['humidity_min'])}-{_fmt_num(crop_row['humidity_max'])}%",
            "rainfall": f"{_fmt_num(crop_row['rain_min'])}-{_fmt_num(crop_row['rain_max'])} mm/year",
            "season": str(crop_row["season"]),
        },
        "summary": generate_summary(parameter_scores),
    }


def _fmt_num(value: Any) -> str:
    """Format a numeric dataset value for display, dropping unneeded decimals."""
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return f"{numeric_value:.1f}"


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def recommend_crops(
    soil_data: Dict[str, Any], dataset_path: str = DEFAULT_DATASET_PATH
) -> List[Dict[str, Any]]:
    """
    Compute the Top 5 most suitable crops for a given parsed soil report.

    This is the single public entry point intended to be called by the
    Flask route layer. It performs validation, scoring, deduplication
    (a crop may appear under multiple soil_type rows -- only its
    highest-scoring variant is returned), ranking, and truncation to the
    top N results.

    :param soil_data: The parser's output, expected to contain a
        "soil_parameters" dict (or the flat parameter keys directly).
    :param dataset_path: Path to the master crop dataset CSV.
    :return: List of up to TOP_N_RESULTS recommendation dicts, sorted by
        score descending.
    :raises SoilDataValidationError: If soil_data fails validation.
    :raises DatasetError: If the crop dataset cannot be loaded or is invalid.
    """
    validated_soil_data = validate_soil_data(soil_data)
    dataset = load_crop_dataset(dataset_path)

    best_recommendation_by_crop: Dict[str, Dict[str, Any]] = {}

    for _, crop_row in dataset.iterrows():
        try:
            parameter_scores, total_score = calculate_crop_score(validated_soil_data, crop_row)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Skipping crop row '%s' (soil_type=%s) due to scoring error: %s",
                crop_row.get("crop", "<unknown>"),
                crop_row.get("soil_type", "<unknown>"),
                exc,
            )
            continue

        recommendation = build_recommendation(crop_row, parameter_scores, total_score)
        crop_name = recommendation["crop"]

        existing = best_recommendation_by_crop.get(crop_name)
        if existing is None or recommendation["score"] > existing["score"]:
            best_recommendation_by_crop[crop_name] = recommendation

    ranked_recommendations = sorted(
        best_recommendation_by_crop.values(),
        key=lambda rec: rec["score"],
        reverse=True,
    )

    return ranked_recommendations[:TOP_N_RESULTS]


# =============================================================================
# LOCAL TESTING / MANUAL VERIFICATION
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_soil_data = {
    "soil_parameters": {
        "nitrogen": 20,
        "phosphorus": 10,
        "potassium": 15,
        "ph": 4.8,
    
    }
}

    try:
        top_recommendations = recommend_crops(
            sample_soil_data, dataset_path=DEFAULT_DATASET_PATH
        )
        print(json.dumps(top_recommendations, indent=2, ensure_ascii=False))
    except (SoilDataValidationError, DatasetError) as exc:
        logger.error("Recommendation engine failed: %s", exc)