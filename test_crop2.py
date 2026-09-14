from backend.services.crop_knowledge import get_crop_knowledge_base

kb = get_crop_knowledge_base()

# Test 1: Field with low N, high P - should favor crops needing low N, high P
print("=== Test 1: Low N, High P ===")
field1 = {'nitrogen': 20, 'phosphorus': 100, 'potassium': 40, 'ph': 6.0, 'temperature': 25, 'humidity': 60, 'rainfall': 800, 'moisture': 40}
top = kb.get_compatible_crops(field1, 5)
for r in top:
    print(f"{r['crop']}: {r['compatibility']}% | Constraints: {r['constraints']}")

print("\n=== Test 2: High pH, low moisture ===")
field2 = {'nitrogen': 50, 'phosphorus': 30, 'potassium': 40, 'ph': 8.0, 'temperature': 30, 'humidity': 50, 'rainfall': 500, 'moisture': 20}
top = kb.get_compatible_crops(field2, 5)
for r in top:
    print(f"{r['crop']}: {r['compatibility']}% | Constraints: {r['constraints']}")

print("\n=== Test 3: Tomato-specific params ===")
field3 = {'nitrogen': 120, 'phosphorus': 80, 'potassium': 150, 'ph': 6.5, 'temperature': 25, 'humidity': 70, 'rainfall': 1000, 'moisture': 60}
top = kb.get_compatible_crops(field3, 5)
for r in top:
    print(f"{r['crop']}: {r['compatibility']}% | Constraints: {r['constraints']}")

print("\n=== Test 4: Get tomato detail ===")
kb = __import__('backend.services.crop_knowledge', fromlist=['get_crop_knowledge_base']).get_crop_knowledge_base()
tomato = kb.get_crop_detail('Tomato')
if tomato:
    print(f"Tomato: N={tomato.nitrogen_range}, P={tomato.phosphorus_range}, K={tomato.potassium_range}, pH={tomato.ph_range}, temp={tomato.temp_range}, humidity={tomato.humidity_range}, rain={tomato.rain_range}, moisture={tomato.moisture_range}, season={tomato.season}")