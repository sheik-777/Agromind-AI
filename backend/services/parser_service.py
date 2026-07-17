"""
=========================================================
AgroMind Parser Service
=========================================================

This service converts raw OCR text into structured soil data.

Pipeline

OCR Text
    ↓
normalize_text()
    ↓
extract_parameters()
    ↓
validate_parameters()
    ↓
Structured JSON
=========================================================
"""

import re

from backend.config.soil_parameters import (
    SOIL_PARAMETERS,
    UNKNOWN_PARAMETERS
)


# =====================================================
# STEP 1
# NORMALIZE OCR TEXT
# =====================================================

def normalize_text(text: str) -> str:
    """
    Cleans OCR output before parsing.

    Tasks:
    - Remove extra spaces
    - Remove duplicate blank lines
    - Standardize line endings
    - Convert strange OCR symbols
    - Normalize aliases
    """

    text = text.replace("\r", "\n")

    text = re.sub(r"\n+", "\n", text)

    text = re.sub(r"[ ]+", " ", text)

    text = text.strip()

    return text


# =====================================================
# STEP 2
# EXTRACT SOIL PARAMETERS
# =====================================================

def extract_parameters(text: str) -> dict:
    """
    Reads normalized OCR text and extracts
    all known soil parameters.

    Unknown parameters will be stored separately.
    """

    extracted = {}

    unknown = {}

    for parameter_key, parameter in SOIL_PARAMETERS.items():

        found = False

        for alias in parameter["aliases"]:

            pattern = rf"{re.escape(alias)}.*?([0-9]+(?:\.[0-9]+)?)"

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                extracted[parameter_key] = float(match.group(1))

                found = True

                break

        if not found:

            continue

    return {
        "known_parameters": extracted,
        "unknown_parameters": unknown
    }


# =====================================================
# STEP 3
# VALIDATE VALUES
# =====================================================

def validate_parameters(parsed_data: dict) -> dict:
    """
    Validates extracted soil values.

    Checks:

    • Missing values
    • Invalid ranges
    • Wrong data type

    Returns cleaned data.
    """

    validated = {}

    warnings = []

    for key, value in parsed_data["known_parameters"].items():

        parameter = SOIL_PARAMETERS[key]

        minimum, maximum = parameter["valid_range"]

        if value < minimum or value > maximum:

            warnings.append(
                f"{parameter['display_name']} value ({value}) "
                f"is outside expected range."
            )

        validated[key] = value

    return {

        "soil_data": validated,

        "unknown_parameters":
        parsed_data["unknown_parameters"],

        "warnings": warnings

    }