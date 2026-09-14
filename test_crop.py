from backend.services.crop_knowledge import get_crop_knowledge_base

kb = get_crop_knowledge_base()
field = {
    'nitrogen': 60, 'phosphorus': 30, 'potassium': 40,
    'ph': 6.5, 'temperature': 28, 'humidity': 70,
    'rainfall': 1200, 'moisture': 50
}
top = kb.get_compatible_crops(field, 10)
for r in top:
    print(f"{r['crop']}: {r['compatibility']}%")
    print(f"  Matched: {r['matched']}")
    print(f"  Constraints: {r['constraints']}")
    print(f"  Scores: {r['scores']}")
    print()