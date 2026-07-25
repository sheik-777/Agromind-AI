from backend.services.recommendation_services import recommend_crops

soil_report = {
    "laboratory_analysis": {
        "samples": [
            {
                "sample_id": "1",
                "parameters": [
                    {
                        "parameter": "ph",
                        "value": 5.9
                    },
                    {
                        "parameter": "phosphorus",
                        "value": 10
                    },
                    {
                        "parameter": "potassium",
                        "value": 34
                    }
                ]
            }
        ]
    }
}

results = recommend_crops(
    soil_report,
    "backend/datasets/agromind_master_dataset_full (1).csv"
)

print(results)