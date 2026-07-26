"""
recommendation_services.py

AgroMind Precision Agriculture Decision Support Platform
---------------------------------------------------------

A deterministic, rule-based crop recommendation engine.

The engine consumes the structured JSON produced by the existing OCR / PDF /
soil-report parser and cross-references it against a master crop dataset to
produce a ranked list of the top matching crops.

Pipeline position
------------------
    PDF upload -> FastAPI -> images -> EasyOCR -> parser -> JSON
        -> recommendation_services.recommend_crops() -> top-5 crops -> API response

This module is a drop-in replacement for the existing recommendation
service. It exposes the same public function signature so it can be
integrated without touching the parser or the FastAPI routes.

Design principles
------------------
1. Parameter agnostic:
   The engine never assumes a soil report contains every supported
   parameter. Whatever subset of {nitrogen, phosphorus, potassium, ph}
   is present is used; missing parameters are simply skipped. A report
   containing only pH must still produce recommendations.

2. Dynamic weight normalization:
   The original weight distribution (N=35, P=25, K=20, pH=20) is
   renormalized to 100 across only the parameters that are actually
   present in a given report, so a report is never penalized for a
   parameter the laboratory did not measure.

3. Deterministic, rule-based scoring:
   No machine learning is used. Every crop's parameter values are
   compared against the crop's ideal range from the dataset, and a
   distance-based percentage score is computed.

4. Organic Matter is explicitly unsupported for scoring:
   The dataset does not contain organic matter ranges, so this
   parameter is recognized (in case the parser reports it) but never
   participates in crop ranking.

5. Environment fields are derived, not stored:
   The dataset stores temp_min/temp_max, humidity_min/humidity_max,
   and rain_min/rain_max rather than pre-formatted strings. This
   module formats them into the display strings the frontend expects
   (e.g. "20-30°C", "60-80%", "800-1200 mm/year").

Public API
----------
    recommend_crops(soil_report_json: dict, dataset_path: str) -> List[dict]

Everything else in this module is an internal implementation detail.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

# =====================================================================
# CONSTANTS
# =====================================================================

#: Parameters the scoring engine is able to evaluate. Order is not
#: significant; presence in this tuple is what defines "supported".
SUPPORTED_PARAMETERS: Tuple[str, ...] = ("nitrogen", "phosphorus", "potassium", "ph")

#: Parameters that may be reported by the parser but must never
#: participate in crop scoring (no dataset ranges exist for them).
UNSUPPORTED_PARAMETERS: Tuple[str, ...] = ("organic_matter",)

#: Original (pre-normalization) weight distribution. Must sum to 100.
ORIGINAL_WEIGHTS: Dict[str, float] = {
    "nitrogen": 35.0,
    "phosphorus": 25.0,
    "potassium": 20.0,
    "ph": 20.0,
}

#: Physical plausibility limits used purely for input validation.
#: Values outside these ranges are treated as invalid measurements
#: rather than legitimate agronomic extremes.
#: Aligned with SOIL_PARAMETERS valid_range to avoid silently dropping
#: legitimate readings.
PHYSICAL_LIMITS: Dict[str, Tuple[float, float]] = {
    "nitrogen": (0.0, 5000.0),
    "phosphorus": (0.0, 2000.0),
    "potassium": (0.0, 5000.0),
    "ph": (0.0, 14.0),
}

#: Rating thresholds shared by both per-parameter and overall crop scores.
RATING_THRESHOLDS: Tuple[Tuple[float, str], ...] = (
    (90.0, "Excellent"),
    (75.0, "Good"),
    (50.0, "Moderate"),
    (0.0, "Poor"),
)

#: Maps an overall match rating to a confidence label surfaced to the user.
CONFIDENCE_BY_MATCH: Dict[str, str] = {
    "Excellent": "Highly Recommended",
    "Good": "Recommended",
    "Moderate": "Consider with Caution",
    "Poor": "Not Recommended",
}

#: Dataset columns holding each supported soil parameter's ideal range.
_SOIL_RANGE_COLUMNS: Dict[str, Tuple[str, str]] = {
    "nitrogen": ("nitrogen_min", "nitrogen_max"),
    "phosphorus": ("phosphorus_min", "phosphorus_max"),
    "potassium": ("potassium_min", "potassium_max"),
    "ph": ("ph_min", "ph_max"),
}

#: Dataset columns holding each derived environment field's ideal range,
#: paired with the unit suffix used when formatting the display string.
_ENVIRONMENT_RANGE_COLUMNS: Dict[str, Tuple[str, str, str]] = {
    "temperature": ("temp_min", "temp_max", "\u00b0C"),
    "humidity": ("humidity_min", "humidity_max", "%"),
    "rainfall": ("rain_min", "rain_max", " mm/year"),
}

#: Dataset columns that are copied as plain strings into the environment block.
_ENVIRONMENT_DIRECT_COLUMNS: Tuple[str, ...] = ("soil_type", "season")

_TOP_N_RESULTS = 5


# =====================================================================
# DATA STRUCTURES
# =====================================================================

@dataclass(frozen=True)
class ParameterReading:
    """A single validated soil parameter reading extracted from a report."""

    name: str
    value: float


@dataclass(frozen=True)
class CropScore:
    """The scored result for one crop, prior to final JSON assembly."""

    crop_name: str
    overall_score: float
    parameter_scores: Dict[str, Dict[str, object]] = field(default_factory=dict)
    crop_row: pd.Series = field(repr=False, compare=False, default=None)


# =====================================================================
# DATASET LOADING
# =====================================================================

@lru_cache(maxsize=8)
def _load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load and cache the master crop dataset from disk.

    The dataset is small enough (~1200 rows) to keep fully in memory,
    and is cached by path so repeated calls to ``recommend_crops`` do
    not repeatedly hit disk.

    Args:
        dataset_path: Path to the CSV dataset.

    Returns:
        The dataset as a pandas DataFrame with normalized column names.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If required columns are missing from the dataset.
    """
    resolved_path = Path(dataset_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Crop dataset not found at '{resolved_path}'.")

    dataframe = pd.read_csv(resolved_path)
    dataframe.columns = [column.strip().lower() for column in dataframe.columns]
    _validate_dataset_columns(dataframe)
    return dataframe


def _validate_dataset_columns(dataframe: pd.DataFrame) -> None:
    """Ensure the dataset contains every column the engine depends on.

    Args:
        dataframe: The loaded crop dataset.

    Raises:
        ValueError: If any required column is missing.
    """
    required_columns = {"crop", *_ENVIRONMENT_DIRECT_COLUMNS}

    for min_col, max_col in _SOIL_RANGE_COLUMNS.values():
        required_columns.update((min_col, max_col))

    for min_col, max_col, _ in _ENVIRONMENT_RANGE_COLUMNS.values():
        required_columns.update((min_col, max_col))

    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"Crop dataset is missing required columns: {sorted(missing_columns)}"
        )


# =====================================================================
# SOIL REPORT PARSING
# =====================================================================

def _extract_raw_parameters(soil_report_json: dict) -> Dict[str, List[float]]:
    """Collect raw numeric readings per parameter across all samples.

    Multiple samples for the same parameter are gathered so their
    values can later be averaged, which keeps the engine robust to
    reports containing more than one lab sample.

    Args:
        soil_report_json: The parser's structured output.

    Returns:
        A mapping of parameter name to the list of raw values found
        for it across all samples.
    """
    readings_by_parameter: Dict[str, List[float]] = {}

    samples = soil_report_json.get("laboratory_analysis", {}).get("samples", [])
    for sample in samples:
        for parameter_entry in sample.get("parameters", []):
            parameter_name = str(parameter_entry.get("parameter", "")).strip().lower()
            if parameter_name not in SUPPORTED_PARAMETERS:
                continue

            raw_value = parameter_entry.get("value")
            readings_by_parameter.setdefault(parameter_name, []).append(raw_value)

    return readings_by_parameter


def _is_valid_numeric(value: object) -> bool:
    """Check whether a value is a real, finite number.

    Args:
        value: The raw value to check.

    Returns:
        True if the value is a finite int or float, False otherwise.
    """
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _validate_and_average(
    readings_by_parameter: Dict[str, List[float]]
) -> Dict[str, float]:
    """Validate raw readings and collapse repeated samples into one value.

    A reading is discarded if it is non-numeric, non-finite, negative,
    or outside its physically plausible range. Surviving readings for
    the same parameter are averaged.

    Args:
        readings_by_parameter: Raw values grouped by parameter name.

    Returns:
        A mapping of parameter name to a single validated value.

    Raises:
        ValueError: If no supported parameter has any valid reading.
    """
    validated_readings: List[ParameterReading] = []

    for parameter_name, raw_values in readings_by_parameter.items():
        lower_limit, upper_limit = PHYSICAL_LIMITS[parameter_name]
        valid_values = [
            float(value)
            for value in raw_values
            if _is_valid_numeric(value) and lower_limit <= value <= upper_limit
        ]

        if valid_values:
            averaged_value = sum(valid_values) / len(valid_values)
            validated_readings.append(ParameterReading(parameter_name, averaged_value))

    if not validated_readings:
        raise ValueError(
            "The soil report does not contain any valid, supported parameters "
            f"(supported parameters: {', '.join(SUPPORTED_PARAMETERS)})."
        )

    return {reading.name: reading.value for reading in validated_readings}


def _extract_available_parameters(soil_report_json: dict) -> Dict[str, float]:
    """Extract, validate, and average supported parameters from a report.

    Args:
        soil_report_json: The parser's structured output.

    Returns:
        A mapping of supported parameter name to its validated value.

    Raises:
        ValueError: If the report contains no valid supported parameters.
    """
    raw_readings = _extract_raw_parameters(soil_report_json)
    return _validate_and_average(raw_readings)


# =====================================================================
# DYNAMIC WEIGHT NORMALIZATION
# =====================================================================

def _normalize_weights(available_parameters: Iterable[str]) -> Dict[str, float]:
    """Redistribute the original weights across only the available parameters.

    Args:
        available_parameters: Parameter names present in the current report.

    Returns:
        A mapping of parameter name to its normalized weight, summing to 100.
    """
    available_parameters = list(available_parameters)
    total_available_weight = sum(
        ORIGINAL_WEIGHTS[parameter] for parameter in available_parameters
    )

    return {
        parameter: (ORIGINAL_WEIGHTS[parameter] / total_available_weight) * 100.0
        for parameter in available_parameters
    }


# =====================================================================
# PARAMETER SCORING
# =====================================================================

def _rating_for_score(score: float) -> str:
    """Map a 0-100 score to its qualitative rating label.

    Args:
        score: A percentage score between 0 and 100.

    Returns:
        One of "Excellent", "Good", "Moderate", or "Poor".
    """
    for threshold, label in RATING_THRESHOLDS:
        if score >= threshold:
            return label
    return "Poor"


def _score_against_range(value: float, minimum: float, maximum: float) -> float:
    """Score how well a value fits inside an ideal [minimum, maximum] range.

    A value inside the range scores 100. A value outside the range is
    penalized proportionally to its distance from the nearest boundary,
    relative to the width of the range, floored at 0.

    Args:
        value: The measured parameter value.
        minimum: The ideal range's lower bound.
        maximum: The ideal range's upper bound.

    Returns:
        A percentage score between 0.0 and 100.0.
    """
    if minimum <= value <= maximum:
        return 100.0

    range_width = maximum - minimum
    if range_width <= 0:
        range_width = maximum if maximum > 0 else 1.0

    distance = (minimum - value) if value < minimum else (value - maximum)
    score = 100.0 - (distance / range_width) * 100.0
    return max(0.0, score)


def _score_parameter(
    parameter_name: str, value: float, crop_row: pd.Series
) -> Dict[str, object]:
    """Score a single parameter reading against a crop's ideal range.

    Args:
        parameter_name: One of the supported parameter names.
        value: The validated soil reading for this parameter.
        crop_row: The dataset row for the crop being evaluated.

    Returns:
        A dictionary describing the value, ideal range, score, and rating.
    """
    min_column, max_column = _SOIL_RANGE_COLUMNS[parameter_name]
    ideal_min = float(crop_row[min_column])
    ideal_max = float(crop_row[max_column])

    score = _score_against_range(value, ideal_min, ideal_max)

    return {
        "value": round(value, 2),
        "ideal_range": [ideal_min, ideal_max],
        "score": round(score, 2),
        "rating": _rating_for_score(score),
    }


# =====================================================================
# CROP SCORING
# =====================================================================

def _score_crop(
    crop_row: pd.Series,
    soil_values: Dict[str, float],
    normalized_weights: Dict[str, float],
) -> CropScore:
    """Compute a crop's overall weighted score and per-parameter breakdown.

    Args:
        crop_row: The dataset row for the crop being evaluated.
        soil_values: Validated soil parameter values from the report.
        normalized_weights: Weight (summing to 100) for each available parameter.

    Returns:
        A CropScore holding the crop's name, overall score, per-parameter
        breakdown, and a reference to its dataset row.
    """
    parameter_scores: Dict[str, Dict[str, object]] = {}
    weighted_total = 0.0

    for parameter_name, value in soil_values.items():
        parameter_result = _score_parameter(parameter_name, value, crop_row)
        parameter_scores[parameter_name] = parameter_result

        weight = normalized_weights[parameter_name]
        weighted_total += (parameter_result["score"] * weight) / 100.0

    return CropScore(
        crop_name=str(crop_row["crop"]),
        overall_score=weighted_total,
        parameter_scores=parameter_scores,
        crop_row=crop_row,
    )


def _score_all_crops(
    dataset: pd.DataFrame,
    soil_values: Dict[str, float],
    normalized_weights: Dict[str, float],
) -> List[CropScore]:
    """Score every crop in the dataset against the report's soil values.

    Args:
        dataset: The full master crop dataset.
        soil_values: Validated soil parameter values from the report.
        normalized_weights: Weight (summing to 100) for each available parameter.

    Returns:
        A list of CropScore results, one per dataset row.
    """
    return [
        _score_crop(crop_row, soil_values, normalized_weights)
        for _, crop_row in dataset.iterrows()
    ]


def _deduplicate_and_rank(crop_scores: List[CropScore]) -> List[CropScore]:
    """Keep only each crop's best-scoring entry, ranked highest first.

    When the same crop name appears multiple times (e.g. across
    different soil types in the dataset), only its highest-scoring
    entry is retained.

    Args:
        crop_scores: Every scored crop, including duplicates.

    Returns:
        The deduplicated crop scores, sorted in descending order.
    """
    best_score_by_crop: Dict[str, CropScore] = {}

    for candidate in crop_scores:
        existing = best_score_by_crop.get(candidate.crop_name)
        if existing is None or candidate.overall_score > existing.overall_score:
            best_score_by_crop[candidate.crop_name] = candidate

    ranked_scores = list(best_score_by_crop.values())
    ranked_scores.sort(key=lambda item: item.overall_score, reverse=True)
    return ranked_scores


# =====================================================================
# SUMMARY GENERATION
# =====================================================================

_PARAMETER_LABELS: Dict[str, str] = {
    "nitrogen": "Nitrogen",
    "phosphorus": "Phosphorus",
    "potassium": "Potassium",
    "ph": "pH",
}

_STRONG_RATINGS = {"Excellent", "Good"}
_WEAK_RATINGS = {"Moderate", "Poor"}


def _generate_summary(
    parameter_scores: Dict[str, Dict[str, object]]
) -> Dict[str, List[str]]:
    """Build dynamic strengths and improvements for only the present parameters.

    Args:
        parameter_scores: Per-parameter scoring results for a crop.

    Returns:
        A dictionary with "strengths" and "improvements" string lists.
    """
    strengths: List[str] = []
    improvements: List[str] = []

    for parameter_name, result in parameter_scores.items():
        label = _PARAMETER_LABELS[parameter_name]
        rating = result["rating"]

        if rating in _STRONG_RATINGS:
            strengths.append(f"{label} level is well suited to this crop.")
        elif rating in _WEAK_RATINGS:
            improvements.append(f"{label} level should be adjusted for better results.")

    return {"strengths": strengths, "improvements": improvements}


# =====================================================================
# RECOMMENDATION ASSEMBLY
# =====================================================================

def _stars_for_score(score: float) -> int:
    """Convert a 0-100 score into a 1-5 star rating.

    Args:
        score: The crop's overall weighted score.

    Returns:
        An integer star rating between 1 and 5, inclusive.
    """
    stars = round(score / 20.0)
    return max(1, min(5, stars))


def _format_range_bound(value: float) -> str:
    """Format a numeric range bound, dropping a trailing ".0" when whole.

    Args:
        value: The numeric bound to format.

    Returns:
        A compact string representation, e.g. "20" instead of "20.0".
    """
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return str(round(numeric_value, 1))


def _format_environment_range(crop_row: pd.Series, field_name: str) -> str:
    """Format a derived environment field as a "min-max<unit>" string.

    Args:
        crop_row: The dataset row for the crop being evaluated.
        field_name: One of "temperature", "humidity", or "rainfall".

    Returns:
        A formatted range string, e.g. "20-30°C" or "800-1200 mm/year".
    """
    min_column, max_column, unit_suffix = _ENVIRONMENT_RANGE_COLUMNS[field_name]
    lower_bound = _format_range_bound(crop_row[min_column])
    upper_bound = _format_range_bound(crop_row[max_column])
    return f"{lower_bound}-{upper_bound}{unit_suffix}"


def _build_environment(crop_row: pd.Series) -> Dict[str, str]:
    """Derive a crop's recommended growing environment from dataset ranges.

    Temperature, humidity, and rainfall are computed from their
    respective min/max dataset columns; soil type and season are
    copied directly.

    Args:
        crop_row: The dataset row for the crop being evaluated.

    Returns:
        A dictionary of environment attributes as display-ready strings.
    """
    environment = {
        field_name: _format_environment_range(crop_row, field_name)
        for field_name in _ENVIRONMENT_RANGE_COLUMNS
    }
    environment.update(
        {column: str(crop_row[column]) for column in _ENVIRONMENT_DIRECT_COLUMNS}
    )
    return environment


def _assemble_crop_result(crop_score: CropScore) -> Dict[str, object]:
    """Assemble a single crop's result dictionary matching the required schema.

    Args:
        crop_score: The scored result for one crop.

    Returns:
        A dictionary following the exact required output schema.
    """
    rounded_score = round(crop_score.overall_score)
    match = _rating_for_score(crop_score.overall_score)

    return {
        "crop": crop_score.crop_name,
        "score": rounded_score,
        "stars": _stars_for_score(crop_score.overall_score),
        "match": match,
        "confidence": CONFIDENCE_BY_MATCH[match],
        "parameter_scores": crop_score.parameter_scores,
        "recommended_environment": _build_environment(crop_score.crop_row),
        "summary": _generate_summary(crop_score.parameter_scores),
    }


# =====================================================================
# PUBLIC ENTRYPOINT
# =====================================================================

def recommend_crops(soil_report_json: dict, dataset_path: str) -> List[Dict[str, object]]:
    """Recommend the top matching crops for a given soil report.

    This is the single public entrypoint of the recommendation engine
    and is a drop-in replacement for the existing service: the
    signature, parameter names, and return type are unchanged so the
    FastAPI routes require no modification.

    The engine is parameter agnostic: whatever subset of the supported
    parameters (nitrogen, phosphorus, potassium, ph) is present in the
    report is used, with weights dynamically renormalized so no report
    is penalized for a parameter its laboratory did not measure.
    Organic matter, while recognized by the parser, never participates
    in scoring.

    Args:
        soil_report_json: The structured JSON produced by the existing
            OCR / PDF / soil-report parser. This schema is not modified.
        dataset_path: Filesystem path to the master crop dataset CSV.

    Returns:
        A list of up to five crop recommendation dictionaries, sorted
        in descending order of match score, each following the schema:

            {
                "crop": str,
                "score": int,
                "stars": int,
                "match": str,
                "confidence": str,
                "parameter_scores": {...},
                "recommended_environment": {...},
                "summary": {"strengths": [...], "improvements": [...]},
            }

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the dataset is missing required columns, or if
            the soil report contains no valid supported parameters.
    """
    dataset = _load_dataset(dataset_path)

    soil_values = _extract_available_parameters(soil_report_json)
    normalized_weights = _normalize_weights(soil_values.keys())

    all_crop_scores = _score_all_crops(dataset, soil_values, normalized_weights)
    ranked_crop_scores = _deduplicate_and_rank(all_crop_scores)
    top_crop_scores = ranked_crop_scores[:_TOP_N_RESULTS]

    return [_assemble_crop_result(crop_score) for crop_score in top_crop_scores]