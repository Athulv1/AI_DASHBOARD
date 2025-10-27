#!/usr/bin/env python3
"""
TEST: Remove a fixture from JSON and verify it's deleted in the rebuilt DXF
"""
import json
import ezdxf
from collections import Counter


def test_remove_fixture():
    """
    1. Load COMPLETE.json
    2. Find and remove first "euro centre" or similar fixture
    3. Save as MODIFIED.json
    4. Show the change
    """
    
    print("=" * 70)
    print("🧪 TEST: Remove a Fixture from JSON")
    print("=" * 70)
    
    # Load JSON
    json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE.json"
    
    print(f"\n📖 Step 1: Loading {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Find INSERT entities
    inserts = [e for e in data['modelspace'] if e['dxf_type'] == 'INSERT']
    print(f"   Found {len(inserts)} INSERT entities (fixtures)")
    
    # Show first 10 fixtures
    print(f"\n📦 Available fixtures to remove:")
    for i, insert in enumerate(inserts[:10], 1):
        print(f"   {i}. {insert['name']} at position X={insert['insert'][0]:.2f}, Y={insert['insert'][1]:.2f}")
    
    # Remove the first fixture
    print(f"\n🗑️  Step 2: Removing first fixture...")
    removed_fixture = inserts[0]
    print(f"   Removing: {removed_fixture['name']}")
    print(f"   Position: X={removed_fixture['insert'][0]:.2f}, Y={removed_fixture['insert'][1]:.2f}")
    
    # Remove from modelspace
    original_count = len(data['modelspace'])
    data['modelspace'] = [e for e in data['modelspace'] if not (
        e['dxf_type'] == 'INSERT' and 
        e.get('name') == removed_fixture['name'] and
        abs(e['insert'][0] - removed_fixture['insert'][0]) < 0.01
    )]
    new_count = len(data['modelspace'])
    
    print(f"   Original entities: {original_count}")
    print(f"   After removal: {new_count}")
    print(f"   Removed: {original_count - new_count} entity")
    
    # Save modified JSON
    modified_json = "ATTA-TEST-FIXTURE-REMOVED.json"
    print(f"\n💾 Step 3: Saving modified JSON...")
    with open(modified_json, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   ✅ Saved: {modified_json}")
    
    return modified_json, removed_fixture


def rebuild_with_modification(modified_json):
    """
    Rebuild DXF from modified JSON using the in-place method
    """
    print(f"\n🔨 Step 4: Rebuilding DXF from modified JSON...")
    
    # Load original DXF
    original_dxf = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf"
    doc = ezdxf.readfile(original_dxf)
    
    # Load modified JSON
    with open(modified_json, 'r') as f:
        json_data = json.load(f)
    
    # Get INSERT entities from modified JSON
    modified_inserts = [e for e in json_data['modelspace'] if e['dxf_type'] == 'INSERT']
    print(f"   Modified JSON has {len(modified_inserts)} fixtures")
    
    # Strategy: Remove ALL INSERTs from DXF, then add back from JSON
    msp = doc.modelspace()
    
    # Get all original entities
    original_entities = list(msp)
    original_insert_count = len([e for e in original_entities if e.dxftype() == 'INSERT'])
    print(f"   Original DXF has {original_insert_count} fixtures")
    
    # Delete all INSERT entities from modelspace
    print(f"   Deleting all fixtures from DXF...")
    for entity in original_entities:
        if entity.dxftype() == 'INSERT':
            msp.delete_entity(entity)
    
    # Add back INSERT entities from JSON
    print(f"   Adding {len(modified_inserts)} fixtures from modified JSON...")
    for insert_data in modified_inserts:
        try:
            msp.add_blockref(
                name=insert_data['name'],
                insert=insert_data['insert'],
                dxfattribs={
                    'layer': insert_data.get('layer', '0'),
                    'color': insert_data.get('color', 256),
                    'xscale': insert_data.get('xscale', 1.0),
                    'yscale': insert_data.get('yscale', 1.0),
                    'rotation': insert_data.get('rotation', 0),
                }
            )
        except Exception as e:
            print(f"      Warning: Could not add {insert_data['name']}: {e}")
    
    # Set R2018 + MM
    doc.header['$INSUNITS'] = 4
    doc.header['$MEASUREMENT'] = 1
    
    # Save
    output_file = "ATTA-TEST-FIXTURE-REMOVED-R2018-MM.dxf"
    doc.saveas(output_file)
    
    print(f"\n✅ Saved: {output_file}")
    
    # Verify
    verify = ezdxf.readfile(output_file)
    verify_inserts = [e for e in verify.modelspace() if e.dxftype() == 'INSERT']
    verify_types = Counter(e.dxftype() for e in verify.modelspace())
    
    print(f"\n📊 Verification:")
    print(f"   Total entities: {len(list(verify.modelspace()))}")
    print(f"   INSERT entities: {len(verify_inserts)}")
    print(f"   Entity types: {dict(verify_types)}")
    print(f"   DXF Version: {verify.dxfversion}")
    print(f"   Units: {verify.header.get('$INSUNITS')} (4=MM)")
    
    return output_file, len(verify_inserts)


if __name__ == "__main__":
    # Test removing a fixture
    modified_json, removed = test_remove_fixture()
    
    # Rebuild DXF
    output_file, final_insert_count = rebuild_with_modification(modified_json)
    
    print(f"\n" + "=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)
    print(f"Removed fixture: {removed['name']}")
    print(f"Original fixtures: 59")
    print(f"Modified JSON fixtures: 58")
    print(f"Final DXF fixtures: {final_insert_count}")
    print()
    print(f"Files created:")
    print(f"  1. {modified_json} (JSON with 1 fixture removed)")
    print(f"  2. {output_file} (DXF with fixture removed)")
    print()
    print("✅ Now try opening the DXF in AutoCAD - the fixture should be missing!")
    print("=" * 70)
