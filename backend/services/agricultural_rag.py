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
            KnowledgeItem(
                id="crop_rotation_principles",
                source_id="icar",
                title="Crop Rotation Principles for Soil Health and Pest Management",
                topic="crop_rotation",
                content=(
                    "Crop rotation is the planned sequencing of different crops on the same land "
                    "to break pest and disease cycles, improve soil fertility, and reduce weed pressure. "
                    "Key principles: (1) rotate between plant families—do not follow a crop with another "
                    "of the same family; (2) alternate deep-rooted with shallow-rooted crops to use "
                    "different soil layers; (3) include legumes to fix atmospheric nitrogen; "
                    "(4) include a cover crop or green manure to protect and enrich soil; "
                    "(5) avoid planting susceptible crops after crops that host the same diseases. "
                    "Example 3-year rotation: legume (groundnut) -> cereal (wheat/maize) -> vegetable/tuber. "
                    "Benefits: reduces soil-borne disease (e.g., fusarium, sclerotinia), "
                    "improves soil structure, balances nutrient extraction across the root zone."
                ),
                source_metadata={
                    "title": "Crop Rotation and Its Role in Modern Agriculture",
                    "organization": "FAO",
                    "source_type": "technical_paper",
                    "topic": "sustainable agriculture",
                    "geographic_relevance": "global",
                },
                tags=["crop_rotation", "soil_health", "pest_break_cycle", "legumes", "cover_crops", "sustainable_agriculture"],
            ),
            KnowledgeItem(
                id="organic_farming_principles",
                source_id="icar",
                title="Organic Farming Principles and Practices",
                topic="organic_farming",
                content=(
                    "Organic farming works with natural systems rather than synthetic inputs. "
                    "Core practices: (1) maintain and build soil organic matter with compost, "
                    "green manures, and crop residues; (2) use biological nitrogen fixation "
                    "(legumes, Azolla in rice) instead of synthetic urea; "
                    "(3) manage pests through crop rotation, biocontrol agents, "
                    "trap crops, botanicals (neem), and by encouraging natural enemies; "
                    "(4) control weeds through mulching, stale seedbed, hand weeding, and "
                    "mechanical cultivation; (5) avoid synthetic pesticides and fertilizers. "
                    "Certification under NPOP (India) or NOP (US) requires a transition period "
                    "of typically 3 years with documented practices. Organic soils hold more "
                    "water, support higher microbial diversity, and are more resilient to drought."
                ),
                source_metadata={
                    "title": "Organic Farming Handbook",
                    "organization": "ICAR-Indian Institute of Farming Systems Research",
                    "source_type": "extension_publication",
                    "topic": "organic agriculture",
                    "geographic_relevance": "india",
                },
                tags=["organic_farming", "compost", "biofertilizer", "pest_management", "soil_organic_matter", "certification"],
            ),
            KnowledgeItem(
                id="ure_vs_dap_comparison",
                source_id="icar",
                title="Urea vs DAP: Nutrient Composition and Use",
                topic="fertilizer",
                content=(
                    "Urea is the most concentrated nitrogen fertilizer—46% nitrogen (N), "
                    "applied mainly for vegetative growth. It hydrolyzes quickly in soil to ammonium; "
                    "apply to moist soil and incorporate promptly to reduce ammonia volatilization loss; "
                    "never broadcast on dry surface in strong sunlight. "
                    "DAP (Di-Ammonium Phosphate) is 18% nitrogen and 46% phosphorus (P2O5), "
                    "used primarily as a basal/placement fertilizer at planting for root development "
                    "and early energy transfer. Both provide N; DAP also delivers P, which is "
                    "immobile in soil and must be placed near the developing root. "
                    "Choose urea when the need is only nitrogen (top-dressing); choose DAP/SSP "
                    "when soil test shows low available phosphorus. Double cropping with only these "
                    "two can raise soil P while leaving potassium unaddressed—always balance with "
                    "potash (MOP) based on soil test."
                ),
                source_metadata={
                    "title": "Fertilizer Selection Guide: Urea and DAP",
                    "organization": "ICAR-Indian Agricultural Research Institute",
                    "source_type": "extension_folder",
                    "topic": "fertilizer management",
                    "geographic_relevance": "india",
                },
                tags=["urea", "dap", "nitrogen", "phosphorus", "basal_dressing", "fertilizer_comparison"],
            ),
            KnowledgeItem(
                id="aphid_control_ipm",
                source_id="pest_management",
                title="Aphid Management through Integrated Pest Management (IPM)",
                topic="pest",
                content=(
                    "Aphids are small, soft-bodied sap-feeders causing leaf curling, "
                    "yellowing, sticky honeydew (leading to sooty mold), and virus transmission. "
                    "Early detection: inspect undersides of young leaves and growing tips weekly. "
                    "Cultural control: avoid excess nitrogen (which promotes soft growth aphids prefer), "
                    "conserve natural enemies (ladybird beetles, lacewings, syrphid flies, parasitic wasps), "
                    "remove heavily infested shoots, and use reflective mulch. "
                    "Biological control: release Chrysoperla, Aphidius, or apply entomopathogenic fungi "
                    "(Beauveria bassiana); tolerate low populations when natural enemies are present. "
                    "Chemical control (only when thresholds are exceeded): insecticidal soap, "
                    "neem-based products, or registered systemic insecticides; rotate chemistries "
                    "to avoid resistance; always follow label rates. Most commercial crops "
                    "tolerate some aphid pressure, so treat only when infestation threatens yield."
                ),
                source_metadata={
                    "title": "Integrated Aphid Management",
                    "organization": "ICAR-National Bureau of Agricultural Insect Resources",
                    "source_type": "IPM_manual",
                    "topic": "pest management",
                    "geographic_relevance": "tropical_subtropical",
                },
                tags=["aphids", "ipm", "biological_control", "natural_enemies", "sooty_mold", "insecticidal_soap"],
            ),
            KnowledgeItem(
                id="acidic_soil_crop_selection",
                source_id="soil_science",
                title="Crops Suited to Acidic Soils (pH below 5.8)",
                topic="soil",
                content=(
                    "Acidic soils (pH below 5.8) limit availability of phosphorus, calcium, magnesium, "
                    "and molybdenum while increasing aluminum and manganese toxicity. "
                    "Tolerant crops include: rice (5.5-6.5), potato (5.0-6.0), pineapple (4.5-5.5), "
                    "tea (4.5-5.5), blueberry (4.5-5.0), cashew, rubber, cassava, and most grasses. "
                    "Cover crops adapted to low pH: lupins, serradella, and some clovers. "
                    "Management for acid soils: apply lime (CaCO3) at rates based on lime requirement "
                    "test; incorporate 2-3 months before planting; use dolomite where magnesium is low; "
                    "prefer aluminum-tolerant varieties; maintain pH in the crop's preferred band "
                    "rather than pushing all soils to neutral."
                ),
                source_metadata={
                    "title": "Managing Acidic Soils",
                    "organization": "ICAR-Indian Institute of Soil Science",
                    "source_type": "technical_bulletin",
                    "topic": "soil chemistry",
                    "geographic_relevance": "tropical_subtropical",
                },
                tags=["acidic_soil", "low_ph", "liming", "aluminum_toxicity", "crop_tolerance"],
            ),
            KnowledgeItem(
                id="sandy_soil_crops",
                source_id="soil_science",
                title="Crop Selection and Management for Sandy Soils",
                topic="soil",
                content=(
                    "Sandy soils drain quickly, warm early, and are easy to work, but hold little "
                    "water and few nutrients. Suited crops include groundnut, pearl millet (bajra), "
                    "sorghum, watermelon, peppers, tomato (with drip + fertigation), carrot, "
                    "cassava, sweet potato, and many vegetables under irrigation. "
                    "Management: add organic matter (compost/FYM) to build water-holding capacity; "
                    "use drip irrigation with high-frequency, low-volume applications; "
                    "apply fertilizers in split doses because leaching is high; "
                    "mulch the soil surface to reduce evaporation. "
                    "Average field capacity of sandy loam is roughly 12-20% volumetric; "
                    "irrigate when moisture approaches 50% of available water."
                ),
                source_metadata={
                    "title": "Management of Sandy Soils",
                    "organization": "FAO",
                    "source_type": "technical_report",
                    "topic": "soil management",
                    "geographic_relevance": "semi_arid_tropical",
                },
                tags=["sandy_soil", "drainage", "mulching", "drip_irrigation", "organic_matter"],
            ),
            KnowledgeItem(
                id="wilting_causes",
                source_id="crop_science",
                title="Why Plants Wilt Despite Adequate Watering",
                topic="water_stress",
                content=(
                    "Wilting despite watering can indicate: (1) root damage—from overwatering "
                    "(waterlogged roots cannot take up oxygen; root rot by Pythium/Phytophthora), "
                    "root-knot nematodes, or mechanical injury; (2) vascular wilt diseases "
                    "(Fusarium or Verticillium) that block water-conducting tissue; "
                    "(3) bacterial wilt (Ralstonia) causing sudden flaccid collapse; "
                    "(4) soil-borne pathogen entry through damaged roots; "
                    "(5) soil crusting/salt accumulation reducing water uptake; "
                    "(6) midday heat stress when transpiration exceeds uptake on very hot days. "
                    "Diagnosis: check roots for brown/waterlogged tissue, examine stem cross-section "
                    "for vascular discoloration (a sign of wilt diseases), probe soil moisture "
                    "below the surface rather than the top inch, and note the pattern "
                    "(starts on one side of plant = vascular wilt). "
                    "If the soil stays wet and roots are dark, reduce irrigation frequency and "
                    "improve drainage. A brown vascular ring on the cut stem points to Fusarium/Verticillium."
                ),
                source_metadata={
                    "title": "Diagnosing Wilting Crops",
                    "organization": "ICAR-Indian Institute of Horticultural Research",
                    "source_type": "diagnosis_guide",
                    "topic": "plant health diagnosis",
                    "geographic_relevance": "tropical_subtropical",
                },
                tags=["wilting", "root_rot", "fusarium", "verticillium", "bacterial_wilt", "waterlogging", "diagnosis"],
            ),
            KnowledgeItem(
                id="nitrogen_deficiency_yellowing",
                source_id="soil_science",
                title="Diagnosing Yellowing Plants by Pattern",
                topic="nutrient_deficiency",
                content=(
                    "Yellowing (chlorosis) pattern helps diagnose the cause: "
                    "(1) uniform yellowing of older/lower leaves first = nitrogen deficiency; "
                    "(2) yellowing between leaf veins on younger leaves with green veins = "
                    "iron or manganese deficiency (often high pH); "
                    "(3) older leaves yellow on margins and tips with brown scorch = "
                    "potassium deficiency; "
                    "(4) overall pale plants with purple discoloration = phosphorus deficiency "
                    "or cold stress; "
                    "(5) interveinal yellowing of older leaves = magnesium deficiency; "
                    "(6) patchy yellowing with leaf distortion or mosaic = virus; "
                    "(7) sudden wilting + yellowing starting on one side = vascular wilt disease. "
                    "Rule out over/under-watering first: check root health and soil moisture, "
                    "then compare symptoms against crop-specific deficiency charts before "
                    "applying any nutrient."
                ),
                source_metadata={
                    "title": "Leaf Chlorosis: Symptom-Based Diagnosis",
                    "organization": "ICAR-Indian Institute of Soil Science",
                    "source_type": "diagnosis_guide",
                    "topic": "nutrient management",
                    "geographic_relevance": "global",
                },
                tags=["yellowing", "chlorosis", "nitrogen", "iron", "magnesium", "potassium", "diagnosis"],
            ),
            KnowledgeItem(
                id="rice_vegetative_fertilizer",
                source_id="icar",
                title="Fertilizer Recommendation for Rice at Vegetative Stage",
                topic="fertilizer",
                crop="rice",
                content=(
                    "Rice vegetative stage runs from transplanting/seedling to panicle initiation. "
                    "Nitrogen is the key nutrient: apply 25-30% of total N as basal before "
                    "transplanting and a further 25-30% as top-dressing at tillering "
                    "(about 20-25 DAT); the remainder goes at panicle initiation. "
                    "Phosphorus (full dose) and potassium (half dose) are basal. "
                    "For a typical 100:50:50 (N:P2O5:K2O kg/ha) recommendation: "
                    "basal 25kg N + full P + half K; tillering top-dress 25kg N; "
                    "panicle initiation 25kg N + remaining K. "
                    "Use urea (46% N) for top-dressing; deep placement or incorporation "
                    "into wet soil reduces volatilization. In the vegetative phase, "
                    "maintain 2-5 cm standing water after establishment and control weeds, "
                    "then decide N at tillering based on leaf color (Leaf Color Chart) "
                    "rather than fixed schedule where available."
                ),
                source_metadata={
                    "title": "Rice Production Technology",
                    "organization": "ICAR-Indian Institute of Rice Research",
                    "source_type": "production_guide",
                    "topic": "crop nutrition",
                    "geographic_relevance": "india",
                },
                tags=["rice", "vegetative_stage", "tillering", "nitrogen", "basal_dressing", "leaf_color_chart"],
            ),
            KnowledgeItem(
                id="wheat_water_requirement",
                source_id="icar",
                title="Water Requirement of Wheat",
                topic="crop_water",
                crop="wheat",
                content=(
                    "Wheat requires an annual rainfall of about 500-750 mm for rainfed production; "
                    "with irrigation, total water requirement is around 450-650 mm depending on "
                    "climate and duration. Critical irrigation stages (most yield sensitive): "
                    "crown root initiation (CRI) at 20-25 days after sowing, tillering, "
                    "jointing, flowering, and grain filling. In heavy soils 4-5 irrigations "
                    "of 5-7 cm suffice; in sandy soils more frequent lighter irrigations are needed. "
                    "Avoid stress at flowering—the most sensitive stage—and avoid excess water "
                    "at maturity which causes lodging. Total consumptive use peaks between "
                    "heading and grain fill (about 6-7 mm/day under hot conditions)."
                ),
                source_metadata={
                    "title": "Water Management in Wheat",
                    "organization": "ICAR-Indian Institute of Wheat and Barley Research",
                    "source_type": "technical_bulletin",
                    "topic": "crop water requirement",
                    "geographic_relevance": "irrigated_agriculture",
                },
                tags=["wheat", "water_requirement", "cri", "irrigation_scheduling", "critical_stages"],
            ),
            KnowledgeItem(
                id="heavy_rain_precautions",
                source_id="icar",
                title="Precautions Before Heavy Rainfall",
                topic="weather",
                content=(
                    "Before heavy rain is forecast: (1) complete drainage work—clean field channels, "
                    "create outlets, avoid waterlogging in sensitive crops; "
                    "(2) postpone irrigation since rainfall probability is high and excess water "
                    "harms roots; (3) avoid applying fertilizers or pesticides that will leach/wash off—"
                    "especially nitrogen and contact fungicides/insecticides; "
                    "(4) secure polythene covers for vegetable nurseries; "
                    "(5) harvest mature produce—mature vegetables, wheat/grain nearing harvest—early "
                    "to avoid spoilage; "
                    "(6) in orchards, check for standing water near the trunk to prevent root rot; "
                    "(7) avoid spraying systemic pesticides that require dry hours; "
                    "(8) brace tall crops (maize, sugarcane) and erect supports where needed. "
                    "After heavy rain: inspect field for waterlogging, watch for fungal diseases "
                    "that follow prolonged wetness."
                ),
                source_metadata={
                    "title": "Weather-Responsive Farm Operations",
                    "organization": "ICAR-Central Research Institute for Dryland Agriculture",
                    "source_type": "contingency_plan",
                    "topic": "weather risk management",
                    "geographic_relevance": "monsoon_agriculture",
                },
                tags=["heavy_rain", "waterlogging", "drainage", "weather_forecast", "harvest", "contingency"],
            ),
            KnowledgeItem(
                id="npk_explained",
                source_id="soil_science",
                title="What NPK Means and How to Read Fertilizer Numbers",
                topic="fertilizer",
                content=(
                    "NPK stands for Nitrogen (N), Phosphorus (P), and Potassium (K)—the three "
                    "primary macronutrients. Fertilizer bags list three numbers, e.g., 10-26-26 "
                    "(DAP-like), meaning 10% N, 26% P2O5, and 26% K2O by weight. "
                    "How to use: NPK 20-20-20 contains equal parts and is a general all-purpose. "
                    "Nitrogen drives green vegetative growth; phosphorus drives root, flower, "
                    "and fruit development; potassium regulates water, disease resistance, "
                    "and grain/fruit filling. "
                    "Convert P2O5 to P: multiply by 0.44; convert K2O to K: multiply by 0.83. "
                    "Choose a formulation based on crop stage and soil test: high N for leafy "
                    "vegetative growth, high P at planting/rooting, higher K during flowering "
                    "and fruit fill and for stress tolerance."
                ),
                source_metadata={
                    "title": "Understanding Fertilizer: N-P-K",
                    "organization": "USDA Extension",
                    "source_type": "extension_publication",
                    "topic": "fertilizer fundamentals",
                    "geographic_relevance": "global",
                },
                tags=["npk", "fertilizer_numbers", "nitrogen", "phosphorus", "potassium", "crop_stage"],
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

        # Extract meaningful query tokens (drop stop words / small words)
        stop = {"the", "a", "an", "is", "are", "what", "why", "how", "who", "when", "where",
                "should", "can", "do", "does", "did", "my", "i", "to", "of", "in", "on",
                "for", "and", "or", "with", "that", "this", "it", "whats"}
        query_tokens = [w for w in query_lower.split() if len(w) > 2 and w not in stop]
        content_tokens = None

        for item in self.knowledge_items:
            score = 0.0

            # 1. Intent/topic match — boost when the item's topic relates to the intent
            item_topics = [item.topic, item.title.lower()] + (item.tags or [])
            joined = " ".join(item_topics).lower()
            if intent and intent in item.topic:
                score += 3.0
            if intent and intent in joined:
                score += 1.5
            if intent == "disease" and any(t in ["pest", "disease", "plant_pathology"] for t in (item.tags or [])):
                score += 2.0
            if intent == "fertilizer" and "nutrient" in item.topic:
                score += 1.5
            if intent == "irrigation" and "water" in item.topic:
                score += 1.5
            if intent == "soil" and "soil" in item.topic:
                score += 1.5

            # 2. Tag / title exact-token matches (strong signal)
            item_tag_text = " ".join(item.tags or []).lower()
            for tok in query_tokens:
                if tok in item_tag_text:
                    score += 3.0
                if tok in item.title.lower():
                    score += 1.5

            # 3. Content token overlap
            for tok in query_tokens:
                if tok in item.content.lower():
                    score += 0.6

            # 4. Field context relevance
            if field_context and field_context.get("crop"):
                cname = str(field_context["crop"]).lower()
                if cname in item.content.lower():
                    score += 2.0
                if field_context["crop"].lower() == (item.crop or "").lower():
                    score += 3.0

            if field_context:
                if field_context.get("soil_ph") and "ph" in item.content.lower():
                    score += 1.0
                if field_context.get("soil_moisture") and any(w in item.content.lower() for w in ["moisture", "irrigation", "water"]):
                    score += 1.0
                if field_context.get("temperature") and "temperature" in item.content.lower():
                    score += 1.0

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