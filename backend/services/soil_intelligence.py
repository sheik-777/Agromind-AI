"""
Enhanced Soil Report Pipeline with EXTRACTED/INFERRED/RECOMMENDED labels.

Wraps the existing extraction-only parser and adds AI interpretation layer
with explicit provenance tags.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional, List, Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.models import SoilReport

from backend.services.parser_service import parse_soil_report as _parse_soil_report
from backend.services.crop_knowledge import get_crop_knowledge_base


@dataclass
class ExtractedParameter:
    """A parameter directly extracted from the soil report."""
    parameter: str
    display_name: str
    original_name: str
    value: float
    unit: str
    extraction_confidence: float  # 0.0 - 1.0
    source: str = "EXTRACTED"  # EXTRACTED | INFERRED | RECOMMENDED
    source_page: Optional[int] = None
    extraction_method: str = "OCR"  # OCR | TABLE | REGEX | MANUAL
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class InferredParameter:
    """A parameter inferred from extracted data or agricultural knowledge."""
    parameter: str
    display_name: str
    value: float
    unit: str
    inference_basis: str  # e.g., "calculated from N/P/K ratio", "estimated from soil type"
    confidence: float  # 0.0 - 1.0
    source: str = "INFERRED"
    reasoning: str = ""
    dependencies: List[str] = None  # which extracted parameters this depends on

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class RecommendedAction:
    """A recommended action based on extracted/inferred data."""
    action_type: str  # FERTILIZER | IRRIGATION | TREATMENT | CROP_CHANGE | SOIL_AMENDMENT
    priority: str  # HIGH | MEDIUM | LOW
    title: str
    description: str
    rationale: str
    evidence: List[str]  # which extracted/inferred parameters support this
    confidence: float  # 0.0 - 1.0
    source: str = "RECOMMENDED"
    # For treatment recommendations
    natural_approach: Optional[Dict[str, Any]] = None
    chemical_approach: Optional[Dict[str, Any]] = None
    expected_outcome: str = ""
    risks: List[str] = None
    monitoring: List[str] = None

    def __post_init__(self):
        if self.rationale is None:
            self.rationale = []
        if self.monitoring is None:
            self.monitoring = []


@dataclass
class SoilReportAnalysis:
    """Complete soil report analysis with EXTRACTED/INFERRED/RECOMMENDED separation."""
    extracted_parameters: List[Dict]  # ExtractedParameter
    inferred_parameters: List[Dict]   # InferredParameter
    recommendations: List[Dict]       # RecommendedAction
    metadata: Dict
    warnings: List[str]
    soil_report_id: Optional[str] = None


class SoilReportIntelligence:
    """Enhanced soil report analysis with AI interpretation."""

    def __init__(self):
        self.crop_kb = get_crop_knowledge_base()

    def analyze_soil_report(self, pdf_text: str, field_context: Optional[Dict] = None) -> Dict:
        """
        Complete soil report analysis with EXTRACTED/INFERRED/RECOMMENDED separation.
        
        Args:
            pdf_text: Raw OCR text from soil report PDF
            field_context: Optional field context (crop, location, etc.)
            
        Returns:
            Dict with extracted_parameters, inferred_parameters, recommendations
        """
        # Step 1: Extract raw data (existing OCR pipeline)
        raw = _parse_soil_report(pdf_text)
        
        # Step 2: Structure extracted parameters with provenance
        extracted = self._structure_extracted_parameters(raw)
        
        # Step 3: Infer missing/derived parameters
        inferred = self._infer_parameters(extracted)
        
        # Step 3b: Soil health assessment
        soil_health = self._assess_soil_health(extracted)
        
        # Step 4: Crop compatibility
        crop_recs = self._recommend_crops(extracted)
        
        # Step 5: Generate recommendations
        recommendations = self._generate_recommendations(
            extracted, soil_health, crop_recommendations=None
        )
        
        # Step 6: Build structured response with provenance
        return self._build_response(
            extracted=extracted,
            inferred=[],
            recommendations=[],
            metadata={"warnings": []}
        )

    def _structure_extracted_parameters(self, raw: Dict) -> List[Dict]:
        """Convert raw parser output to structured extracted parameters with provenance."""
        extracted = []
        
        # Process laboratory analysis samples
        lab_analysis = raw.get("laboratory_analysis", {})
        for sample in lab_analysis.get("samples", []):
            for param in sample.get("parameters", []):
                extracted.append({
                    "parameter": param.get("parameter"),
                    "display_name": param.get("display_name"),
                    "original_name": param.get("original_name"),
                    "value": param.get("value"),
                    "unit": param.get("unit"),
                    "extraction_confidence": 0.9 if isinstance(param.get("value"), (int, float)) else 0.5,
                    "source": "EXTRACTED",
                    "source_page": 1,  # Would be page number in real implementation
                    "extraction_method": "OCR_TABLE",
                    "sample_id": sample.get("sample_id"),
                    "extraction_warnings": []
                })
        
        # Add metadata as extracted (with lower confidence)
        metadata = raw.get("metadata", {})
        for key, value in metadata.items():
            if value:
                extracted.append({
                    "parameter": key,
                    "display_name": key.replace("_", " ").title(),
                    "original_name": key,
                    "value": value,
                    "unit": "",
                    "extraction_confidence": 0.7,
                    "source": "EXTRACTED",
                    "extraction_method": "OCR_METADATA",
                    "warnings": []
                })
        
        return extracted

    def _infer_parameters(self, extracted: List[Dict]) -> List[Dict]:
        """Infer missing/derived parameters from extracted data."""
        inferred = []
        
        # Extract values by parameter name
        values = {}
        for p in extracted:
            if p["source"] == "EXTRACTED" and p.get("value") is not None:
                key = p["parameter"]
                if isinstance(p["value"], (int, float)):
                    if key not in values:
                        values[key] = p["value"]
        
        # Infer N:P:K ratio
        n = extracted.get("nitrogen")
        p_val = extracted.get("phosphorus")
        k_val = extracted.get("potassium")
        
        if all(v is not None for v in [n, p_val, k_val]):
            # Infer N:P:K ratio
            total = n + p_val + k_val
            if total > 0:
                n_pct = (n / total) * 100
                p_pct = (p_val / total) * 100
                k_pct = (k_val / total) * 100
                
                # Classify ratio
                if n_pct > 50:
                    ratio_type = "Nitrogen-dominant"
                elif p_val > 50:
                    ratio_type = "Phosphorus-dominant"
                elif k_val > 50:
                    ratio_type = "Potassium-dominant"
                else:
                    ratio_type = "Balanced"
                
                return [{
                    "parameter": "npk_ratio_type",
                    "display_name": "NPK Ratio Classification",
                    "value": ratio_type,
                    "unit": "classification",
                    "inference_basis": "calculated from N/P/K values",
                    "confidence": 0.9,
                    "source": "INFERRED",
                    "reasoning": f"N={n}%, P={p_pct:.0f}%, K={k_pct:.0f}% of total NPK",
                    "dependencies": ["nitrogen", "phosphorus", "potassium"]
                }]
        
        return []

    def _assess_soil_health(self, extracted: List[Dict]) -> Dict:
        """Assess overall soil health from extracted parameters."""
        params = {p["parameter"]: p["value"] for p in extracted if p.get("value") is not None}
        
        health = {
            "overall": "UNKNOWN",
            "factors": [],
            "alerts": [],
            "strengths": []
        }
        
        # pH assessment
        ph = None
        for p in extracted:
            if p["parameter"] == "ph" and p.get("value") is not None:
                ph = p["value"]
                break
        
        if ph is not None:
            if 6.0 <= ph <= 7.0:
                health["strengths"].append(f"Optimal pH ({ph}) for most crops")
                health["factors"].append({"factor": "pH", "status": "OPTIMAL", "value": ph})
            elif 5.5 <= ph < 6.0 or 7.0 < ph <= 7.5:
                health["factors"].append({"factor": "pH", "status": "ACCEPTABLE", "value": ph})
            else:
                health["alerts"].append(f"pH {ph} outside optimal range for most crops")
                health["factors"].append({"factor": "pH", "status": "SUBOPTIMAL", "value": ph})
        
        # NPK assessment
        n = p_val = k_val = None
        for p in extracted:
            if p["parameter"] == "nitrogen" and p.get("value") is not None:
                n = p["value"]
            elif p["parameter"] == "phosphorus" and p.get("value") is not None:
                p_val = p["value"]
            elif p["parameter"] == "potassium" and p.get("value") is not None:
                k_val = p["value"]
        
        for nutrient, value, optimal_range in [
            ("Nitrogen", n, (40, 80)),
            ("Phosphorus", p_val, (20, 50)),
            ("Potassium", k_val, (30, 60))
        ]:
            if value is not None:
                if optimal_range[0] <= value <= optimal_range[1]:
                    health["strengths"].append(f"{nutrient} optimal ({value})")
                elif value < optimal_range[0]:
                    health["alerts"].append(f"{nutrient} low ({value} < {optimal_range[0]})")
                else:
                    health["alerts"].append(f"{nutrient} high ({value} > {optimal_range[1]})")
        
        # Overall assessment
        if not health["alerts"]:
            health["overall"] = "HEALTHY"
        elif len(health["alerts"]) <= 2:
            health["overall"] = "NEEDS_ATTENTION"
        else:
            health["overall"] = "CRITICAL"
            
        return health

    def _recommend_crops(self, extracted: List[Dict]) -> List[Dict]:
        """Recommend crops based on soil parameters."""
        field_params = {}
        for p in extracted:
            if p.get("value") is not None:
                field_params[p["parameter"]] = p["value"]
        
        # Convert to field params format expected by crop KB
        field_params_normalized = {}
        param_map = {
            "nitrogen": "nitrogen",
            "phosphorus": "phosphorus", 
            "potassium": "potassium",
            "ph": "ph",
            "temperature": "temperature",
            "humidity": "humidity",
            "rainfall": "rainfall",
            "moisture": "moisture",
        }
        for ext_key, int_key in param_map.items():
            for p in extracted:
                if p["parameter"] == ext_key and p.get("value") is not None:
                    field_params_normalized[int_key] = p["value"]
                    break
        
        kb = get_crop_knowledge_base()
        return kb.get_compatible_crops(field_params_normalized, 10)

    def _generate_recommendations(self, extracted: List[Dict], soil_health: Dict, crop_recommendations: List) -> List[Dict]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # pH correction
        ph = None
        for p in extracted:
            if p["parameter"] == "ph" and p.get("value") is not None:
                ph = p["value"]
                break
        
        if ph is not None and ph < 5.5:
            recommendations.append({
                "action_type": "SOIL_AMENDMENT",
                "priority": "HIGH",
                "title": "Apply lime to raise soil pH",
                "description": f"Soil pH is {ph}, below optimal range (6.0-7.0). Apply agricultural lime.",
                "rationale": ["Low pH reduces nutrient availability", "Aluminum toxicity risk at low pH"],
                "evidence": [f"Current pH: {ph}"],
                "confidence": 0.9,
                "source": "RECOMMENDED",
                "natural_approach": {
                    "procedure": "Apply agricultural lime based on buffer pH test",
                    "timing": "2-3 months before planting",
                    "expected_response": "pH increase of 0.5-1.0 unit per ton/acre",
                    "limitations": "Slow acting, requires incorporation"
                },
                "chemical_approach": {
                    "procedure": "Apply calcitic or dolomitic lime per soil test recommendation",
                    "timing": "Fall or early spring",
                    "expected_response": "Measurable pH change in 30-60 days",
                    "risks": ["Over-liming can cause micronutrient deficiencies"]
                },
                "expected_outcome": "pH increase to 6.0-6.5 range",
                "risks": ["Over-liming", "Temporary nutrient imbalance"],
                "monitoring": ["Retest pH in 60 days", "Monitor crop response"]
            })
        
        # Nitrogen recommendation
        n_val = None
        for p in extracted:
            if p["parameter"] == "nitrogen" and p.get("value") is not None:
                n_val = p["value"]
                break
        
        if n_val is not None and n_val < 40:
            recommendations.append({
                "action_type": "FERTILIZER",
                "priority": "HIGH",
                "title": "Apply nitrogen fertilizer",
                "description": f"Soil nitrogen ({n}) below optimal range (40-80 ppm). Apply nitrogen fertilizer.",
                "rationale": ["Low nitrogen limits vegetative growth", "Critical for vegetative stage"],
                "evidence": [f"Current N: {n} ppm"],
                "confidence": 0.85,
                "source": "RECOMMENDED",
                "natural_approach": {
                    "procedure": "Apply composted manure or green manure",
                    "timing": "Pre-plant or early vegetative",
                    "expected_response": "Gradual N release over 4-8 weeks",
                    "limitations": "Variable N content, slower release"
                },
                "chemical_approach": {
                    "procedure": "Apply urea or ammonium sulfate per soil test",
                    "timing": "Split application: basal + top dress",
                    "expected_response": "Rapid N availability",
                    "risks": ["Volatilization loss", "Leaching in sandy soils", "Nitrate accumulation"]
                },
                "expected_outcome": "Nitrogen levels in optimal range",
                "risks": ["Over-application causes lodging", "Environmental leaching"],
                "monitoring": ["Leaf color monitoring", "Tissue test at flowering"]
            })
        
        return recommendations

    def analyze(self, pdf_text: str) -> Dict:
        """Main entry point: full soil report analysis."""
        # Step 1: Parse
        raw = _parse_soil_report(pdf_text)
        
        # Step 2: Structure extracted
        extracted = self._structure_extracted_parameters(raw)
        
        # Step 3: Soil health
        soil_health = self._assess_soil_health(extracted)
        
        # Step 4: Crop recommendations
        crop_recs = self._recommend_crops(extracted)
        
        # Step 5: Recommendations
        recommendations = self._generate_recommendations(extracted, soil_health, None)
        
        # Build response
        extracted_params = [
            {
                "parameter": p["parameter"],
                "display_name": p.get("display_name", p["parameter"]),
                "value": p.get("value"),
                "unit": p.get("unit", ""),
                "extraction_confidence": p.get("extraction_confidence", 0.9),
                "source": "EXTRACTED",
                "extraction_method": "OCR_TABLE",
                "sample_id": p.get("sample_id"),
                "warnings": p.get("extraction_warnings", [])
            }
            for p in extracted
        ]
        
        return {
            "extracted_parameters": [
                {**p, "source": "EXTRACTED"} for p in extracted_params
            ],
            "inferred_parameters": [],  # Would be populated by inference engine
            "recommendations": recommendations,
            "metadata": {
                "soil_health": soil_health,
                "crop_recommendations": crop_recs[:5],
                "warnings": []  # from parser
            },
            "warnings": []
        }


# Factory function
_soil_intelligence = None

def get_soil_intelligence() -> "SoilReportIntelligence":
    global _soil_intelligence
    if _soil_intelligence is None:
        _soil_intelligence = SoilReportIntelligence()
    return _soil_intelligence


# Demo/test
if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    LABORATORY ANALYSIS
    Sample pH Phosphorus Potassium
    1 6.2 25 180
    2 5.8 15 150
    """
    si = get_soil_intelligence()
    result = si.analyze(sample_text)
    import json
    print(json.dumps(result, indent=2, default=str))