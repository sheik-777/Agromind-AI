"""
Smoke test for the A&L Laboratories parser.

Simulates OCR output that closely matches the real report layout
and runs it through parse_soil_report().
"""

import json
import sys
sys.path.insert(0, ".")

from backend.services.parser_service import parse_soil_report

# ------------------------------------------------------------------
# Simulated OCR text — mirrors a real A&L page 1 layout.
# ------------------------------------------------------------------

SIMULATED_OCR = """
Laboratory Name    A&L Laboratories
Client Name        John Doe
County             Shelby
Account Number     12345
Lab Number         67890
Date Received      01/10/2026
Date Processed     01/12/2026
Area Type          Garden
Area Designation   Raised Bed 1

LABORATORY ANALYSIS

pH
Organic Matter
Phosphorus
Potassium
Calcium
Magnesium
Sulphur
Zinc
Iron
Copper
Boron
Manganese
Sodium

Sample 1

6.8
3.5
45
210
1200
180
12
2.5
45
1.8
0.6
8.2
35

LABORATORY ANALYSIS INTERPRETATIONS

pH
Optimum
Organic Matter
Good
Phosphorus
High
Potassium
Optimum
Calcium
Adequate
Magnesium
Adequate
Sulphur
Adequate
Zinc
High
Iron
Optimum
Copper
Optimum
Boron
Optimum
Manganese
Optimum
Sodium
Low

RECOMMENDATIONS

Lime to Apply
No lime recommended at this time.

Fertilizer to Apply
Apply 2 lbs of 10-10-10 per 100 sq ft in early spring.

Cultural and Management Tips
Mulch beds with 2-3 inches of organic material.
Maintain consistent irrigation schedule.

References and Resources
UT Extension Publication PB1581.
Local cooperative extension office.
"""


def main() -> None:
    result = parse_soil_report(SIMULATED_OCR)

    print("=" * 60)
    print("PARSE RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))

    # Basic assertions
    assert "metadata" in result, "Missing 'metadata' key"
    assert "samples" in result, "Missing 'samples' key"
    assert "recommendations" in result, "Missing 'recommendations' key"
    assert "unknown_parameters" in result, "Missing 'unknown_parameters' key"
    assert "warnings" in result, "Missing 'warnings' key"
    assert "report_structure" in result, "Missing 'report_structure' key"

    meta = result["metadata"]
    assert meta.get("laboratory_name") == "A&L Laboratories", (
        f"Expected 'A&L Laboratories', got {meta.get('laboratory_name')}"
    )
    assert meta.get("client_name") == "John Doe", (
        f"Expected 'John Doe', got {meta.get('client_name')}"
    )
    assert meta.get("county") == "Shelby", (
        f"Expected 'Shelby', got {meta.get('county')}"
    )

    sample = result["samples"][0]
    soil_data = sample["soil_data"]

    # Check a few key parameters were extracted.
    assert "ph" in soil_data, "pH not found in soil_data"
    assert soil_data["ph"] == 6.8, f"Expected pH 6.8, got {soil_data['ph']}"

    assert "phosphorus" in soil_data, "Phosphorus not found"
    assert soil_data["phosphorus"] == 45.0, (
        f"Expected P 45, got {soil_data['phosphorus']}"
    )

    assert "potassium" in soil_data, "Potassium not found"
    assert soil_data["potassium"] == 210.0, (
        f"Expected K 210, got {soil_data['potassium']}"
    )

    # Interpretations
    interp = sample["interpretations"]
    assert "ph" in interp, "pH interpretation missing"
    assert interp["ph"] == "Optimum", (
        f"Expected 'Optimum', got {interp['ph']}"
    )

    # Recommendations
    recs = result["recommendations"]
    assert len(recs["lime_to_apply"]) > 0, "Lime recommendations empty"
    assert len(recs["fertilizer_to_apply"]) > 0, (
        "Fertilizer recommendations empty"
    )
    assert len(recs["cultural_and_management"]) > 0, (
        "Cultural tips empty"
    )
    assert len(recs["references_and_resources"]) > 0, (
        "References empty"
    )

    # Report structure
    assert result["report_structure"] == "table", (
        f"Expected 'table', got {result['report_structure']}"
    )

    print("\n" + "=" * 60)
    print("ALL ASSERTIONS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
