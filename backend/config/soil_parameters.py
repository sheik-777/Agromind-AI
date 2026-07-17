"""
==========================================================
AgroMind Soil Knowledge Base
==========================================================

This file contains the master database of every soil
parameter understood by AgroMind.

The parser, recommendation engine, dashboard,
AI assistant and validation system will all use this file.

==========================================================
"""

SOIL_PARAMETERS = {

    # =====================================================
    # SOIL PROPERTIES
    # =====================================================

    "ph": {
        "display_name": "pH",
        "aliases": ["pH", "PH", "Soil pH", "Soil Reaction"],
        "unit": "",
        "datatype": "float",
        "valid_range": (0, 14),
        "category": "Soil Property",
        "required": True,
        "description": "Measures soil acidity or alkalinity.",
        "affects": ["crop_selection", "fertilizer"],
        "priority": "critical"
    },

    "electrical_conductivity": {
        "display_name": "Electrical Conductivity",
        "aliases": ["EC", "Electrical Conductivity", "Conductivity"],
        "unit": "dS/m",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Soil Property",
        "required": False,
        "description": "Indicates salinity level.",
        "affects": ["crop_selection", "irrigation"],
        "priority": "high"
    },

    "organic_matter": {
        "display_name": "Organic Matter",
        "aliases": ["Organic Matter", "OM"],
        "unit": "%",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Soil Property",
        "required": False,
        "description": "Improves fertility and soil structure.",
        "affects": ["crop_selection", "fertility"],
        "priority": "high"
    },

    "organic_carbon": {
        "display_name": "Organic Carbon",
        "aliases": ["Organic Carbon", "OC"],
        "unit": "%",
        "datatype": "float",
        "valid_range": (0, 20),
        "category": "Soil Property",
        "required": False,
        "description": "Indicates soil carbon content.",
        "affects": ["fertility"],
        "priority": "medium"
    },

    "moisture": {
        "display_name": "Moisture",
        "aliases": ["Moisture", "Moisture Content"],
        "unit": "%",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Soil Property",
        "required": False,
        "description": "Represents current soil moisture.",
        "affects": ["irrigation"],
        "priority": "critical"
    },

    # =====================================================
    # PRIMARY NUTRIENTS
    # =====================================================

    "nitrogen": {
        "display_name": "Nitrogen",
        "aliases": ["Nitrogen", "Available Nitrogen", "N"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 5000),
        "category": "Primary Nutrient",
        "required": False,
        "description": "Supports vegetative plant growth.",
        "affects": ["crop_selection", "fertilizer"],
        "priority": "critical"
    },

    "phosphorus": {
        "display_name": "Phosphorus",
        "aliases": [
            "Phosphorus",
            "Available Phosphorus",
            "P",
            "P2O5"
        ],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 2000),
        "category": "Primary Nutrient",
        "required": False,
        "description": "Supports root development and flowering.",
        "affects": ["crop_selection", "fertilizer"],
        "priority": "critical"
    },

    "potassium": {
        "display_name": "Potassium",
        "aliases": [
            "Potassium",
            "Available Potassium",
            "K",
            "K2O",
            "Potash"
        ],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 5000),
        "category": "Primary Nutrient",
        "required": False,
        "description": "Improves disease resistance and water regulation.",
        "affects": ["crop_selection", "fertilizer"],
        "priority": "critical"
    },

    # =====================================================
    # SECONDARY NUTRIENTS
    # =====================================================

    "calcium": {
        "display_name": "Calcium",
        "aliases": ["Calcium", "Ca"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 5000),
        "category": "Secondary Nutrient",
        "required": False,
        "description": "Essential for cell wall development.",
        "affects": ["fertility"],
        "priority": "medium"
    },

    "magnesium": {
        "display_name": "Magnesium",
        "aliases": ["Magnesium", "Mg"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 3000),
        "category": "Secondary Nutrient",
        "required": False,
        "description": "Central component of chlorophyll.",
        "affects": ["fertility"],
        "priority": "medium"
    },

    "sulphur": {
        "display_name": "Sulphur",
        "aliases": ["Sulphur", "Sulfur", "S"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 1000),
        "category": "Secondary Nutrient",
        "required": False,
        "description": "Required for protein synthesis.",
        "affects": ["fertility"],
        "priority": "medium"
    },

    # =====================================================
    # MICRONUTRIENTS
    # =====================================================

    "zinc": {
        "display_name": "Zinc",
        "aliases": ["Zinc", "Zn"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Micronutrient",
        "required": False,
        "description": "Supports enzyme activity.",
        "affects": ["fertility"],
        "priority": "medium"
    },

    "iron": {
        "display_name": "Iron",
        "aliases": ["Iron", "Fe"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 500),
        "category": "Micronutrient",
        "required": False,
        "description": "Essential for chlorophyll formation.",
        "affects": ["fertility"],
        "priority": "medium"
    },

    "copper": {
        "display_name": "Copper",
        "aliases": ["Copper", "Cu"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Micronutrient",
        "required": False,
        "description": "Supports reproductive growth.",
        "affects": ["fertility"],
        "priority": "low"
    },

    "boron": {
        "display_name": "Boron",
        "aliases": ["Boron", "B"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 20),
        "category": "Micronutrient",
        "required": False,
        "description": "Important for flowering and fruit development.",
        "affects": ["fertility"],
        "priority": "low"
    },

    "manganese": {
        "display_name": "Manganese",
        "aliases": ["Manganese", "Mn"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 300),
        "category": "Micronutrient",
        "required": False,
        "description": "Supports photosynthesis.",
        "affects": ["fertility"],
        "priority": "low"
    },

    # =====================================================
    # SALINITY
    # =====================================================

    "sodium": {
        "display_name": "Sodium",
        "aliases": ["Sodium", "Na"],
        "unit": "ppm",
        "datatype": "float",
        "valid_range": (0, 5000),
        "category": "Salinity",
        "required": False,
        "description": "High levels can reduce crop productivity.",
        "affects": ["crop_selection"],
        "priority": "medium"
    },

    "sar": {
        "display_name": "Sodium Adsorption Ratio",
        "aliases": ["SAR", "Sodium Adsorption Ratio"],
        "unit": "",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Salinity",
        "required": False,
        "description": "Measures sodium hazard.",
        "affects": ["crop_selection", "irrigation"],
        "priority": "medium"
    },

    "esp": {
        "display_name": "Exchangeable Sodium Percentage",
        "aliases": ["ESP", "Exchangeable Sodium Percentage"],
        "unit": "%",
        "datatype": "float",
        "valid_range": (0, 100),
        "category": "Salinity",
        "required": False,
        "description": "Indicates sodicity level.",
        "affects": ["crop_selection"],
        "priority": "medium"
    }

}

UNKNOWN_PARAMETERS = {}