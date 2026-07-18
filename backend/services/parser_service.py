"""OCR-tolerant parser for soil test report pages.

This module converts raw OCR text for a single soil-report page into
structured JSON. It performs extraction only: no interpretation, scoring,
deficiency prediction, dataset comparison, or recommendation logic lives
here. That belongs to a separate `recommendation_service.py`.

The public entry point is :func:`parse_soil_report`.

Design notes
------------
* OCR text is assumed to be imperfect: dropped leading characters
  ("ab Number" for "Lab Number"), merged/broken lines, inconsistent
  whitespace, and split words are all expected and tolerated.
* Parsing is line-based and state-machine driven rather than relying on
  fixed table layouts or brittle regular expressions.
* Every laboratory parameter is identified by fuzzy-matching against
  :data:`soil_parameters.SOIL_PARAMETERS`, which is the single source of
  truth for parameter names, aliases, and units. Adding a new parameter to
  that file requires no changes here.
* The parser never raises for malformed input. Any section that cannot be
  extracted is left empty and a warning is recorded, so callers always get
  a well-formed (if partial) result.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Any, Optional

from backend.config.soil_parameters import SOIL_PARAMETERS, UNKNOWN_PARAMETERS

logger = logging.getLogger("parser_service")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Metadata fields are report bookkeeping, not chemical parameters, so their
# aliases are not part of SOIL_PARAMETERS. They are declared here instead.
METADATA_FIELDS: dict[str, list[str]] = {
    "lab_number": ["lab number", "lab no", "lab #"],
    "account": ["account"],
    "client": ["client"],
    "county": ["county"],
    "date_received": ["date received"],
    "date_processed": ["date processed"],
    "send_to": ["send to"],
    "area_type": ["area type"],
    "area_designation": ["area designation"],
}

# Recommendation blocks are free-text sections bounded by these headings.
RECOMMENDATION_HEADINGS: dict[str, str] = {
    "lime_to_apply": "lime to apply",
    "fertilizer_to_apply": "fertilizer to apply",
    "cultural_and_management_tips": "cultural and management tips",
    "references_and_resources": "references and resources",
}

# Top-level report sections, used as parsing state boundaries. Order matters:
# more specific headings must be checked before shorter ones they contain.
SECTION_HEADINGS: dict[str, str] = {
    "laboratory_analysis_interpretations": "laboratory analysis interpretations",
    "laboratory_analysis": "laboratory analysis",
    "recommendations": "recommendations",
}

# All phrases that can act as a "stop" boundary when capturing free-text
# recommendation blocks.
_ALL_BOUNDARY_PHRASES: list[str] = list(RECOMMENDATION_HEADINGS.values()) + list(
    SECTION_HEADINGS.values()
)

_FUZZY_LINE_THRESHOLD = 0.82
_FUZZY_TOKEN_THRESHOLD = 0.78

_NUMBER_RE = re.compile(r"-?\d+\.?\d*")
_PURE_NUMBER_RE = re.compile(r"^-?\d+\.?\d*$")
_SAMPLE_LABEL = "sample"


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Normalize text for fuzzy comparison."""

    text = text.lower().strip()

    # Remove square bracket content like [P], [K], [Zn]
    text = re.sub(r"\[[^\]]*\]", "", text)

    # Remove parentheses like (ppm), (mg/kg), (%)
    text = re.sub(r"\([^)]*\)", "", text)

    # Remove standalone percent symbols
    text = text.replace("%", "")

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _similarity(a: str, b: str) -> float:
    """Return a 0-1 similarity ratio between two strings."""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _ocr_tolerant_similarity(candidate: str, target: str) -> float:
    """Similarity that also tolerates a dropped leading character.

    OCR frequently drops the first character of a line (e.g. "Lab Number"
    becomes "ab Number"). This checks the direct similarity as well as the
    similarity with either string's leading character stripped, and returns
    the best score.

    Args:
        candidate: Text extracted from OCR.
        target: Known reference phrase (already normalized).

    Returns:
        Best-effort similarity ratio.
    """
    candidate_n = _normalize(candidate)
    target_n = _normalize(target)
    scores = [_similarity(candidate_n, target_n)]
    if len(candidate_n) > 1:
        scores.append(_similarity(candidate_n[1:], target_n))
    if len(target_n) > 1:
        scores.append(_similarity(candidate_n, target_n[1:]))
    return max(scores)


def _split_lines(page_text: str) -> list[str]:
    """Split raw OCR page text into cleaned, non-empty lines."""
    raw_lines = page_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return [line.strip() for line in raw_lines if line.strip()]


def _classify_heading(line: str) -> Optional[str]:
    """Check whether a line is one of the known section/recommendation headings.

    Longer, more specific headings are checked first so that, for example,
    "Laboratory Analysis Interpretations" is not misclassified as
    "Laboratory Analysis".

    Args:
        line: A single cleaned line of OCR text.

    Returns:
        The heading key (from SECTION_HEADINGS or RECOMMENDATION_HEADINGS) if
        matched, otherwise None.
    """
    combined = {**SECTION_HEADINGS, **RECOMMENDATION_HEADINGS}
    ordered_keys = sorted(combined, key=lambda k: len(combined[k]), reverse=True)
    for key in ordered_keys:
        phrase = combined[key]
        if _ocr_tolerant_similarity(line, phrase) >= _FUZZY_LINE_THRESHOLD:
            return key
    return None


def _fuzzy_match_metadata_field(line: str) -> Optional[tuple[str, str]]:
    """Match a line against known metadata field labels, allowing inline values.

    Handles both "Label: value" and "Label value" forms, as well as the
    OCR-dropped-leading-character case.

    Args:
        line: A cleaned OCR line.

    Returns:
        Tuple of (field_key, remaining_value_text) if a label is found at the
        start of the line, else None. remaining_value_text may be empty if
        the value is expected on a following line.
    """
    for field_key, aliases in METADATA_FIELDS.items():
        for alias in sorted(aliases, key=len, reverse=True):
            # Try to find the alias near the start of the line (tolerant of a
            # missing leading character) and split off whatever follows it.
            for probe_len in (len(alias), len(alias) - 1):
                if probe_len <= 0:
                    continue
                prefix = line[:probe_len]
                if _ocr_tolerant_similarity(prefix, alias) >= _FUZZY_LINE_THRESHOLD:
                    remainder = line[probe_len:].lstrip(" :\t")
                    return field_key, remainder
    return None


def _fuzzy_match_parameter(token: str) -> Optional[str]:
    """Fuzzy-match a short token/phrase against SOIL_PARAMETERS aliases.

    Args:
        token: A candidate parameter name extracted from OCR text.

    Returns:
        The normalized parameter key from SOIL_PARAMETERS if a confident
        match is found, else None.
    """
    token_n = _normalize(token)
    if not token_n:
        return None

    best_key: Optional[str] = None
    best_score = 0.0
    for key, definition in SOIL_PARAMETERS.items():
        candidates = {key.replace("_", " ")} | set(definition["aliases"])
        for alias in candidates:
            score = _ocr_tolerant_similarity(token_n, alias)
            if score > best_score:
                best_score = score
                best_key = key
    threshold = _FUZZY_TOKEN_THRESHOLD if len(token_n) > 2 else 0.99
    if best_score >= threshold:
        return best_key
    return None


def _extract_numbers(line: str) -> list[float]:
    """Extract all numeric values from a line, as floats.

    Args:
        line: A line of text expected to contain numbers.

    Returns:
        List of floats found, in order of appearance.
    """
    values: list[float] = []
    for match in _NUMBER_RE.findall(line):
        try:
            values.append(float(match))
        except ValueError:
            continue
    return values


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------


def _extract_metadata(lines: list[str], warnings: list[str]) -> dict[str, Any]:
    """Extract report metadata (lab number, client, dates, etc.).

    Args:
        lines: Cleaned OCR lines for the page.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        Dictionary of metadata field -> extracted value (empty string if a
        field's label was found but no value could be located).
    """
    metadata: dict[str, str] = {key: "" for key in METADATA_FIELDS}

    for idx, line in enumerate(lines):
        match = _fuzzy_match_metadata_field(line)
        if not match:
            continue
        field_key, remainder = match
        if remainder:
            metadata[field_key] = remainder.strip()
        elif idx + 1 < len(lines):
            # Value likely sits on the following line (e.g. "Area Type" then
            # "Lawn/Established" on the next line).
            next_line = lines[idx + 1]
            if _classify_heading(next_line) is None and not _fuzzy_match_metadata_field(
                next_line
            ):
                metadata[field_key] = next_line.strip()

    for field_key, value in metadata.items():
        if not value:
            warnings.append(f"metadata field '{field_key}' not found")

    return metadata


# ---------------------------------------------------------------------------
# Laboratory analysis (measured values) extraction
# ---------------------------------------------------------------------------


def _find_parameter_columns(header_line: str) -> list[tuple[int, int, str, str]]:
    """Locate SOIL_PARAMETERS mentions within a table header line.

    Args:
        header_line: The line believed to contain column headers such as
            "Sample pH Phosphorus [P] (ppm) Potassium [K] (ppm)".

    Returns:
        List of (start, end, parameter_key, matched_text) tuples sorted by
        position in the header, with overlapping matches resolved by
        preferring the longest match at each position.
    """
    candidates: list[tuple[int, int, str, str]] = []
    for key, definition in SOIL_PARAMETERS.items():
        aliases = sorted(
            {key.replace("_", " ")} | set(definition["aliases"]), key=len, reverse=True
        )
        for alias in aliases:
            if not alias:
                continue
            for match in re.finditer(re.escape(alias), header_line, re.IGNORECASE):
                start, end = match.span()
                if len(alias) <= 2:
                    before = header_line[start - 1 : start]
                    after = header_line[end : end + 1]
                    if before.isalpha() or after.isalpha():
                        continue
                candidates.append((start, end, key, match.group()))

    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    selected: list[tuple[int, int, str, str]] = []
    last_end = -1
    for start, end, key, text in candidates:
        if start >= last_end:
            selected.append((start, end, key, text))
            last_end = end
    return selected


def _extend_span_with_units(header_line: str, end: int) -> int:
    """Extend a matched column span to include trailing [..]/(..) unit hints."""
    cursor = end
    while True:
        match = re.match(r"\s*(\[[^\]]*\]|\([^)]*\))", header_line[cursor:])
        if not match:
            break
        cursor += match.end()
    return cursor


def _unit_from_original_name(original_name: str, fallback_unit: Optional[str]) -> Optional[str]:
    """Pull a unit out of a parenthesized suffix if present, else use fallback."""
    paren_match = re.search(r"\(([^)]+)\)", original_name)
    if paren_match:
        candidate = paren_match.group(1).strip()
        # Guard against a bare element symbol in parentheses, e.g. "(P)".
        if candidate.lower() not in {"p", "k", "n"}:
            return candidate
    return fallback_unit


def _looks_like_data_row(line: str, expected_columns: int) -> bool:
    """Heuristic check for whether a line is a measurement data row."""
    tokens = line.split()
    if not tokens:
        return False
    if not re.match(r"^-?\d+\.?\d*$", tokens[0]):
        return False
    return len(tokens) >= min(2, expected_columns)

def _looks_like_pure_number(line: str) -> bool:
    """Return True if a line consists of nothing but a number.

    Used only during header-phase scanning to detect where the header
    tokens end and the first data value (the sample ID) begins, since a
    header token (a parameter name, unit, or "Sample") is never a bare
    number on its own line.
    """
    return bool(_PURE_NUMBER_RE.match(line.strip()))


def _split_vertical_header_and_data(
    block_lines: list[str], warnings: list[str]
) -> tuple[list[dict[str, Any]], int]:
    """Walk a table block one line at a time and classify each header token.

    OCR output for this table layout places one header token per line
    (e.g. "Sample", "pH", "Phosphorus [P] (ppm)", ...) followed by one
    value per line, repeating per sample row. This scans forward from the
    top of the block, classifying each line as the "Sample" column, a
    recognized SOIL_PARAMETERS column, or an unrecognized header token,
    and stops as soon as it hits a line that is a bare number -- which can
    only be the first data value (a sample ID), never a header.

    Args:
        block_lines: Lines belonging to a single Laboratory Analysis table.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        Tuple of (columns, data_start_idx). `columns` is an ordered list of
        {"role": "sample"|"parameter"|"unknown", "key": Optional[str],
        "original_name": str} dicts, one per detected header token.
        `data_start_idx` is the index into block_lines where the first data
        value lives (i.e. where header scanning stopped).
    """
    columns: list[dict[str, Any]] = []

    for idx, line in enumerate(block_lines):
        if _looks_like_pure_number(line):
            return columns, idx

        if _classify_heading(line) is not None:
            # Hit the next section heading before any data row appeared:
            # this block has headers but no measurements.
            return columns, idx

        if _ocr_tolerant_similarity(line, _SAMPLE_LABEL) >= _FUZZY_LINE_THRESHOLD:
            columns.append({"role": "sample", "key": None, "original_name": line})
            continue

        param_key = _fuzzy_match_parameter(line)
        if param_key is not None:
            columns.append(
                {"role": "parameter", "key": param_key, "original_name": line}
            )
        else:
            columns.append({"role": "unknown", "key": None, "original_name": line})
            warnings.append(
                f"laboratory analysis header token '{line}' did not match any "
                "known parameter"
            )

    # Reached the end of the block while still reading headers: no data rows.
    return columns, len(block_lines)



def _parse_laboratory_analysis_block(
    block_lines: list[str], warnings: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse one "Laboratory Analysis" table block into per-sample results.

    Handles the vertically split layout produced by this OCR pipeline: each
    header token (including "Sample") occupies its own line, followed by
    each sample's values one per line, in the same column order as the
    detected headers, repeating for every subsequent sample row.

    Args:
        block_lines: Lines belonging to a single Laboratory Analysis table,
            headers first, one token per line, followed by data values.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        Tuple of (samples, unknown_parameters). `samples` is a list of
        {"sample_id": ..., "parameters": [...]}; `unknown_parameters` holds
        one entry per header token that could not be matched to
        SOIL_PARAMETERS or the "Sample" label.
    """
    if not block_lines:
        return [], []

    columns, data_start_idx = _split_vertical_header_and_data(block_lines, warnings)

    unknown_parameters = [
        {"header": col["original_name"]} for col in columns if col["role"] == "unknown"
    ]

    n_cols = len(columns)
    if n_cols == 0:
        warnings.append("laboratory analysis block contained no header tokens")
        return [], unknown_parameters

    if not any(col["role"] == "parameter" for col in columns):
        warnings.append("laboratory analysis header contained no recognizable parameters")

    data_lines: list[str] = []
    for line in block_lines[data_start_idx:]:
        if _classify_heading(line) is not None:
            break
        data_lines.append(line)

    samples: list[dict[str, Any]] = []
    for row_start in range(0, len(data_lines), n_cols):
        row_tokens = data_lines[row_start : row_start + n_cols]

        if len(row_tokens) < n_cols:
            if row_tokens:
                warnings.append(
                    "laboratory analysis data ended mid-row "
                    f"({len(row_tokens)} of {n_cols} values found); "
                    "discarding incomplete row"
                )
            break

        sample_id: Optional[str] = None
        parameters: list[dict[str, Any]] = []
        for col, token in zip(columns, row_tokens):
            if col["role"] == "sample":
                sample_id = token
                continue
            if col["role"] == "unknown":
                continue

            key = col["key"]
            definition = SOIL_PARAMETERS[key]
            value: Any
            try:
                value = float(token)
            except ValueError:
                value = token
                warnings.append(
                    f"could not parse numeric value for '{key}' (got '{token}')"
                )
            parameters.append(
                {
                    "parameter": key,
                    "display_name": definition["display_name"],
                    "original_name": col["original_name"],
                    "value": value,
                    "unit": _unit_from_original_name(
                        col["original_name"], definition["unit"]
                    ),
                }
            )

        samples.append({"sample_id": sample_id, "parameters": parameters})

    return samples, unknown_parameters


def _extract_laboratory_analysis(
    lines: list[str], warnings: list[str]
) -> dict[str, Any]:
    """Extract all "Laboratory Analysis" measurement tables from the page.

    Args:
        lines: Cleaned OCR lines for the page.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        Dictionary with "samples" (list of extracted samples across all
        tables found on the page) and "unknown_parameters".
    """
    all_samples: list[dict[str, Any]] = []
    all_unknown: list[dict[str, Any]] = []

    idx = 0
    found_any = False
    while idx < len(lines):
        heading = _classify_heading(lines[idx])
        if heading == "laboratory_analysis":
            found_any = True
            # Collect lines until the next heading.
            block: list[str] = []
            cursor = idx + 1
            while cursor < len(lines) and _classify_heading(lines[cursor]) is None:
                block.append(lines[cursor])
                cursor += 1
            samples, unknown = _parse_laboratory_analysis_block(block, warnings)
            all_samples.extend(samples)
            all_unknown.extend(unknown)
            idx = cursor
            continue
        idx += 1

    if not found_any:
        warnings.append("no 'Laboratory Analysis' section found on this page")

    return {"samples": all_samples, "unknown_parameters": all_unknown}


# ---------------------------------------------------------------------------
# Interpretation ranges extraction (extracted verbatim, never classified)
# ---------------------------------------------------------------------------


def _looks_like_category_header(line: str) -> bool:
    """Heuristic: does this line look like a row of qualitative category labels?"""
    vocab = {
        "very",
        "low",
        "medium",
        "sufficient",
        "optimum",
        "high",
        "excessive",
    }
    tokens = {t.lower() for t in re.findall(r"[a-zA-Z]+", line)}
    return bool(tokens) and tokens.issubset(vocab) and len(tokens) >= 2


def _parse_interpretation_block(
    block_lines: list[str], warnings: list[str]
) -> Optional[dict[str, Any]]:
    """Parse one "Laboratory Analysis Interpretations" table verbatim.

    Args:
        block_lines: Lines following an interpretations heading, up to the
            next section heading.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        Dict with "categories_header" (raw text) and "parameters" (mapping of
        matched parameter key to its display name, original label, and raw
        breakpoint values), or None if nothing usable was found.
    """
    categories_header: Optional[str] = None
    parameters: dict[str, Any] = {}

    idx = 0
    while idx < len(block_lines):
        line = block_lines[idx]

        if _looks_like_category_header(line):
            categories_header = line
            idx += 1
            continue

        param_key = _fuzzy_match_parameter(line)
        if param_key is not None and idx + 1 < len(block_lines):
            next_line = block_lines[idx + 1]
            breakpoints = _extract_numbers(next_line)
            if breakpoints:
                definition = SOIL_PARAMETERS[param_key]
                parameters[param_key] = {
                    "display_name": definition["display_name"],
                    "original_name": line,
                    "breakpoints": breakpoints,
                }
                idx += 2
                continue

        idx += 1

    if categories_header is None and not parameters:
        warnings.append("interpretation block found but no usable content extracted")
        return None

    return {"categories_header": categories_header, "parameters": parameters}


def _extract_interpretations(lines: list[str], warnings: list[str]) -> list[dict[str, Any]]:
    """Extract all "Laboratory Analysis Interpretations" blocks from the page.

    Duplicate blocks (identical categories_header and parameters) are
    collapsed, since OCR sometimes repeats a table due to layout artifacts.

    Args:
        lines: Cleaned OCR lines for the page.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        List of interpretation block dicts, in order of appearance.
    """
    blocks: list[dict[str, Any]] = []
    idx = 0
    while idx < len(lines):
        heading = _classify_heading(lines[idx])
        if heading == "laboratory_analysis_interpretations":
            cursor = idx + 1
            block_lines: list[str] = []
            while cursor < len(lines) and _classify_heading(lines[cursor]) is None:
                block_lines.append(lines[cursor])
                cursor += 1
            parsed = _parse_interpretation_block(block_lines, warnings)
            if parsed is not None and parsed not in blocks:
                blocks.append(parsed)
            idx = cursor
            continue
        idx += 1

    if not blocks:
        warnings.append("no 'Laboratory Analysis Interpretations' section found on this page")

    return blocks


# ---------------------------------------------------------------------------
# Recommendations extraction (verbatim free text, never summarized)
# ---------------------------------------------------------------------------


def _extract_recommendations(lines: list[str], warnings: list[str]) -> dict[str, Any]:
    """Extract free-text recommendation sections verbatim.

    Args:
        lines: Cleaned OCR lines for the page.
        warnings: Mutable list to append extraction warnings to.

    Returns:
        Dictionary keyed by recommendation section (lime_to_apply,
        fertilizer_to_apply, cultural_and_management_tips,
        references_and_resources), each holding the verbatim joined text
        found under that heading.
    """
    recommendations: dict[str, str] = {key: "" for key in RECOMMENDATION_HEADINGS}

    heading_positions: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        heading = _classify_heading(line)
        if heading is not None:
            heading_positions.append((idx, heading))

    for pos, (idx, heading) in enumerate(heading_positions):
        if heading not in RECOMMENDATION_HEADINGS:
            continue
        end_idx = (
            heading_positions[pos + 1][0]
            if pos + 1 < len(heading_positions)
            else len(lines)
        )
        body_lines = lines[idx + 1 : end_idx]
        if body_lines:
            recommendations[heading] = "\n".join(body_lines).strip()

    for key, value in recommendations.items():
        if not value:
            warnings.append(f"recommendation section '{key}' not found")

    return recommendations


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def parse_soil_report(page_text: str) -> dict[str, Any]:
    """Parse OCR text from a single soil-report page into structured JSON.

    This function performs extraction ONLY. It does not analyze soil, infer
    missing values, compare against reference datasets, or generate any
    fertilizer/crop recommendations -- it reports exactly what is present in
    the OCR text, tolerating common OCR errors along the way.

    Args:
        page_text: Raw OCR text for exactly one page of a soil test report.

    Returns:
        A dictionary with keys "metadata", "laboratory_analysis",
        "interpretation", "recommendations", and "warnings". Any section
        that could not be extracted is left empty (or an empty list/dict)
        and a corresponding entry is added to "warnings". This function
        never raises for malformed input.
    """
    warnings: list[str] = []

    if not page_text or not page_text.strip():
        warnings.append("empty page_text supplied")
        return {
            "metadata": {key: "" for key in METADATA_FIELDS},
            "laboratory_analysis": {"samples": [], "unknown_parameters": []},
            "interpretation": [],
            "recommendations": {key: "" for key in RECOMMENDATION_HEADINGS},
            "warnings": warnings,
        }

    lines = _split_lines(page_text)

    try:
        metadata = _extract_metadata(lines, warnings)
    except Exception as exc:  # noqa: BLE001 - parser must never crash
        logger.exception("metadata extraction failed")
        warnings.append(f"metadata extraction failed: {exc}")
        metadata = {key: "" for key in METADATA_FIELDS}

    try:
        laboratory_analysis = _extract_laboratory_analysis(lines, warnings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("laboratory analysis extraction failed")
        warnings.append(f"laboratory analysis extraction failed: {exc}")
        laboratory_analysis = {"samples": [], "unknown_parameters": []}

    try:
        interpretation = _extract_interpretations(lines, warnings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("interpretation extraction failed")
        warnings.append(f"interpretation extraction failed: {exc}")
        interpretation = []

    try:
        recommendations = _extract_recommendations(lines, warnings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("recommendations extraction failed")
        warnings.append(f"recommendations extraction failed: {exc}")
        recommendations = {key: "" for key in RECOMMENDATION_HEADINGS}

    return {
        "metadata": metadata,
        "laboratory_analysis": laboratory_analysis,
        "interpretation": interpretation,
        "recommendations": recommendations,
        "warnings": warnings,
    }