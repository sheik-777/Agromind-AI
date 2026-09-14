"""
Agricultural RAG (Retrieval-Augmented Generation) System.

Retrieves relevant agricultural knowledge from authoritative sources
and combines with field context for grounded AI responses.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import csv
import json
import os
from datetime import datetime
from pathlib import Path

# Authoritative knowledge sources configuration
KNOWLEDGE_SOURCES = {
    "icar": {
        "name": "ICAR - Indian Council of Agricultural Research",
        "authority": "HIGH",
        "topics": ["crop production", "soil health", "pest management", "irrigation", "fertilizer"],
        "path": "knowledge/icar/",
    },
    "fao": {
        "name": "FAO - Food and Agriculture Organization",
        "authority": "HIGH",
        "topics": ["crop production", "soil management", "irrigation", "pest management"],
        "path": "knowledge/fao/",
    },
    "extension": {
        "name": "Agricultural Extension Publications",
        "authority": "HIGH",
        "topics": ["crop management", "pest management", "fertilizer", "irrigation"],
        "path": "knowledge/extension/",
    },
    "soil_science": {
        "name": "Soil Science References",
        "authority": "HIGH",
        "topics": ["soil chemistry", "nutrient management", "pH management", "soil health"],
        "path": "knowledge/soil_science/",
    },
    "crop_science": {
        "name": "Crop Science Literature",
        "authority": "MEDIUM",
        "topics": ["crop physiology", "growth stages", "nutrient requirements", "water requirements"],
        "path": "knowledge/crop_science/",
    },
    "pest_management": {
        "name": "Integrated Pest Management",
        "authority": "HIGH",
        "topics": ["pest identification", "biological control", "chemical control", "IPM"],
        "path": "knowledge/pest_management/",
    },
}

@dataclass
class KnowledgeItem:
    """A piece of agricultural knowledge with provenance."""
    id: str
    source_id: str
    title: str
    topic: str
    crop: Optional[str] = None
    disease: Optional[str] = None
    content: str = ""
    source_metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)


class AgriculturalRAG:
    """Agricultural Retrieval-Augmented Generation system."""

    def __init__(self, knowledge_dir: str = "backend/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_items: List[KnowledgeItem] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        self._load_curated_knowledge()
        if self.knowledge_dir.exists():
            for source_id, source_info in KNOWLEDGE_SOURCES.items():
                source_path = self.knowledge_dir / source_info["path"]
                if source_path.exists():
                    self._load_from_directory(source_id, source_path)
        print(f"Loaded {len(self.knowledge_items)} knowledge items")

    def _load_curated_knowledge(self):
        curated = [
            KnowledgeItem(
                id="soil_ph_optimal",
                source_id="soil_science",
                title="Optimal Soil pH Ranges for Major Crops",
                topic="soil",
                content=(
                    "Most crops grow best in slightly acidic to neutral soil (pH 6.0-7.0). "
                    "Below pH 5.5, aluminum toxicity increases and phosphorus availability decreases. "
                    "Above pH 7.5, micronutrient availability (Fe, Mn, Zn, Cu) decreases significantly. "
                    "Liming raises pH; sulfur/gypsum lowers pH. Target pH depends on crop: "
                    "rice 5.5-6.5, wheat 6.0-7.5, tomato 6.0-6.8, potato 5.0-6.0."
                ),
                source_metadata={
                    "title": "Soil pH Management Guide",
                    "organization": "ICAR-Indian Institute of Soil Science",
                    "source_type": "extension_publication",
                    "topic": "soil chemistry",
                    "geographic_relevance": "tropical_subtropical",
                },
                tags=["pH", "nutrient_availability", "liming", "crop_suitability"],
            ),
            KnowledgeItem(
                id="npk_ratio_crop",
                source_id="icar",
                title="NPK Ratio Requirements by Crop Type",
                topic="fertilizer",
                content=(
                    "NPK requirements vary by crop and growth stage. General guidelines: "
                    "Rice: N:P:K = 4:2:1 (basal 50% N, 100% P, 50% K; top-dress 25% N at tillering, 25% N at panicle initiation). "
                    "Wheat: N:P:K = 4:2:1 (basal 50% N, 100% P, 100% K; top-dress 50% N at CRI). "
                    "Cotton: N:P:K = 2:1:1 (basal 25% N, 50% P, 50% K; 3 splits of N). "
                    "Tomato: N:P:K = 3:1:2 (basal 50% N, 100% P, 50% K; regular N top-dressing). "
                    "Sugarcane: N:P:K = 3:1:2 (basal 30% N, 100% P, 100% K; 4 splits of N)."
                ),
                source_metadata={
                    "title": "Fertilizer Recommendations for Major Crops",
                    "organization": "ICAR-Indian Agricultural Research Institute",
                    "source_type": "extension_publication",
                    "topic": "fertilizer management",
                    "geographic_relevance": "india",
                },
                tags=["NPK", "fertilizer_schedule", "crop_nutrition", "basal_topdress"],
            ),
            KnowledgeItem(
                id="irrigation_scheduling",
                source_id="icar",
                title="Irrigation Scheduling Based on Soil Moisture and Crop Stage",
                topic="irrigation",
                content=(
                    "Irrigation scheduling should consider: crop water requirement (ETc), "
                    "soil moisture depletion, growth stage, soil type, and weather forecast. "
                    "Critical stages for irrigation: "
                    "Rice - tillering, panicle initiation, flowering; "
                    "Wheat - CRI (21 DAS), tillering, jointing, flowering, grain fill; "
                    "Cotton - squaring, flowering, boll development; "
                    "Tomato - transplanting, flowering, fruit set, fruit enlargement. "
                    "Use soil moisture sensors or feel method. Irrigate when soil moisture "
                    "depletes to 50% of available water capacity in root zone. "
                    "Avoid irrigation before expected rainfall (>70% probability)."
                ),
                source_metadata={
                    "title": "Irrigation Management in Field Crops",
                    "organization": "ICAR-Indian Institute of Water Management",
                    "source_type": "technical_bulletin",
                    "topic": "irrigation management",
                    "geographic_relevance": "india",
                },
                tags=["irrigation_scheduling", "crop_water_requirement", "soil_moisture", "critical_stages"],
            ),
            KnowledgeItem(
                id="tomato_early_blight",
                source_id="pest_management",
                title="Tomato Early Blight (Alternaria solani) Management",
                topic="disease",
                crop="tomato",
                disease="early_blight",
                content=(
                    "Early blight causes concentric rings on older leaves, stem lesions, "
                    "and fruit rot. Favored by warm (24-29°C), humid conditions (>85% RH), "
                    "and prolonged leaf wetness. Spread by wind, rain splash, and contaminated tools. "
                    "Management: crop rotation (3-year), resistant varieties, stake/prune for airflow, "
                    "mulch to reduce splash, remove infected debris, fungicide rotation (chlorothalonil, "
                    "mancozeb, azoxystrobin) at 7-10 day intervals starting at first sign. "
                    "Avoid overhead irrigation."
                ),
                source_metadata={
                    "title": "Tomato Early Blight Management",
                    "organization": "ICAR-Indian Institute of Horticultural Research",
                    "source_type": "disease_management_guide",
                    "topic": "plant_pathology",
                    "geographic_relevance": "tropical_subtropical",
                },
                tags=["tomato", "early_blight", "fungal_disease", "fungicide_rotation", "cultural_control"],
            ),
            KnowledgeItem(
                id="nitrogen_deficiency",
                source_id="soil_science",
                title="Nitrogen Deficiency Symptoms and Management",
                topic="nutrient_deficiency",
                content=(
                    "Nitrogen deficiency shows as uniform yellowing of older/lower leaves first, "
                    "stunted growth, reduced tillering/branching, delayed flowering. "
                    "Confirm with soil test (available N < 280 kg/ha or < 20 ppm nitrate-N). "
                    "Management: split N application - basal + top dress at critical stages. "
                    "Sources: urea (46% N), ammonium sulfate (21% N + 24% S), "
                    "calcium ammonium nitrate (26% N). Avoid excess N - causes lodging, "
                    "pest susceptibility, nitrate leaching."
                ),
                source_metadata={
                    "title": "Nutrient Deficiency Symptoms and Management",
                    "organization": "ICAR-Indian Institute of Soil Science",
                    "source_type": "technical_bulletin",
                    "topic": "nutrient management",
                    "geographic_relevance": "india",
                },
                tags=["nitrogen", "deficiency_symptoms", "fertilizer_management", "soil_testing"],
            ),
            KnowledgeItem(
                id="water_stress_identification",
                source_id="crop_science",
                title="Crop Water Stress Identification and Management",
                topic="water_stress",
                content=(
                    "Water stress symptoms: leaf rolling/curling, wilting at midday, "
                    "reduced leaf area, premature senescence, reduced yield. "
                    "Soil moisture depletion to <50% available water in root zone triggers stress. "
                    "Critical stages: flowering, grain fill, fruit set. "
                    "Mitigation: mulching, deficit irrigation, antitranspirants, "
                    "drought-tolerant varieties, adjusted planting dates."
                ),
                source_metadata={
                    "title": "Drought Management in Crops",
                    "organization": "ICAR-Central Research Institute for Dryland Agriculture",
                    "source_type": "technical_bulletin",
                    "topic": "abiotic stress",
                    "geographic_relevance": "semi_arid_tropical",
                },
                tags=["water_stress", "drought", "irrigation_management", "abiotic_stress"],
            ),
            KnowledgeItem(
                id="fertilizer_split_application",
                source_id="fertilizer",
                title="Split Fertilizer Application for Nutrient Efficiency",
                topic="fertilizer",
                content=(
                    "Split application improves nutrient use efficiency and reduces losses. "
                    "Nitrogen: 2-4 splits depending on crop (basal + 2-3 top dressings). "
                    "Phosphorus: mostly basal (80-100%), some starter at planting. "
                    "Potassium: split for long-duration crops (basal + 1-2 top dressings). "
                    "Sulfur: with first N split. Micronutrients: foliar at critical stages. "
                    "Always base rates on soil test and crop requirement."
                ),
                source_metadata={
                    "title": "Efficient Fertilizer Use",
                    "organization": "ICAR-Indian Institute of Soil Science",
                    "source_type": "extension_folder",
                    "topic": "nutrient management",
                    "geographic_relevance": "india",
                },
                tags=["split_application", "nutrient_efficiency", "fertilizer_schedule", "4R_nutrient_stewardship"],
            ),
        ]

        for item in curated:
            self.knowledge_items.append(item)

    def _load_from_directory(self, source_id: str, path: Path):
        for json_file in path.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item_data in data:
                            self.knowledge_items.append(KnowledgeItem(**item_data))
                    else:
                        self.knowledge_items.append(KnowledgeItem(**data))
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

    def retrieve(self, query: str, intent: str, field_context: Optional[Dict] = None, top_k: int = 5) -> List[KnowledgeItem]:
        query_lower = query.lower()
        scored_items = []

        for item in self.knowledge_items:
            score = 0

            if intent and intent in item.topic:
                score += 3
            elif intent and any(t in item.topic for t in item.tags):
                score += 2

            query_words = set(query_lower.split())
            content_words = set(item.content.lower().split())
            overlap = query_words & content_words
            score += len(overlap) * 0.5

            for w in query_lower.split():
                if w in item.title.lower():
                    score += 1

            if field_context and field_context.get("crop"):
                if field_context["crop"].lower() in item.content.lower():
                    score += 2
                if field_context["crop"].lower() == (item.crop or "").lower():
                    score += 3

            if field_context:
                if "soil_ph" in field_context and "ph" in item.content.lower():
                    score += 1
                if "soil_moisture" in field_context and any(w in item.content.lower() for w in ["moisture", "irrigation", "water"]):
                    score += 1
                if "temperature" in field_context and "temperature" in item.content.lower():
                    score += 1

            if score > 0:
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: -x[0])
        return [item for _, item in scored_items[:top_k]]


_rag = None

def get_rag() -> AgriculturalRAG:
    global _rag
    if _rag is None:
        _rag = AgriculturalRAG()
    return _rag


if __name__ == "__main__":
    rag = get_rag()
    print(f"Total knowledge items: {len(rag.knowledge_items)}")

    results = rag.retrieve("Why are my tomato leaves turning yellow?", "disease", {"crop": "tomato"})
    print(f"\nQuery: 'Why are my tomato leaves turning yellow?' (intent: disease, crop: tomato)")
    for item in results:
        print(f"  - {item.id}: {item.title} (topic: {item.topic}, crop: {item.crop})")
        print(f"    Tags: {item.tags}")
        print(f"    Source: {item.source_metadata.get('organization', 'Unknown')}")

    print("\n---")
    results2 = rag.retrieve("Should I irrigate now?", "irrigation", {"soil_moisture": 30, "crop": "wheat"})
    print(f"\nQuery: 'Should I irrigate now?' (intent: irrigation, field: moisture=30%, crop=wheat)")
    for item in results2:
        print(f"  - {item.id}: {item.title} (topic: {item.topic})")

    print("\n---")
    results3 = rag.retrieve("What fertilizer for tomato?", "fertilizer", {"crop": "tomato", "soil_ph": 6.5})
    print(f"\nQuery: 'What fertilizer for tomato?' (intent: fertilizer, crop: tomato)")
    for item in results3:
        print(f"  - {item.id}: {item.title} (topic: {item.topic})")