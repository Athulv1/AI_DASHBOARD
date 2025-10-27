#!/usr/bin/env python3
"""
Test: Change fixture position in JSON and verify it reconstructs correctly
"""
import json
import ezdxf

# Step 1: Load the JSON
print("📖 Loading JSON file...")
with open("ADJ.BELGIAN WAFFLE_MALL ROAD_HOSHIARPUR-COCO-FURNITURE-FULL.json", 'r') as f:
    data = json.load(f)

print(f"\n📊 Original JSON data:")
print(f"   Total entities: {data['total_entities']}")
print(f"   Entity types: {data['modelspace']}")
print(f"   Blocks (fixtures): {len(data['blocks'])}")

# Step 2: Show what we can change
print(f"\n🔧 Available blocks (fixtures) you can modify:")
for i, (block_name, block_data) in enumerate(list(data['blocks'].items())[:10], 1):
    print(f"   {i}. {block_name} ({block_data['entity_count']} entities)")

print(f"\n💡 This JSON has entity TYPE COUNTS, not individual entities.")
print(f"   To change fixture positions, we need the FULL entity JSON.")
print(f"   Let me check if we have the full version...")

# Check if we have full entity data
if isinstance(data['modelspace'], dict):
    print(f"\n⚠️  Current JSON only has entity COUNTS, not positions.")
    print(f"   We need to export FULL entity data to modify positions.")
else:
    print(f"\n✅ This JSON has full entity data - positions can be modified!")
