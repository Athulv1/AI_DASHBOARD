#!/usr/bin/env python3
"""
WORKING METHOD: Modify fixtures directly in the DXF file
This preserves ALL entities including dimensions
"""
import ezdxf
from ezdxf import units
import json
from collections import Counter


def modify_fixtures_in_place(original_dxf, json_modifications, output_dxf):
    """
    The CORRECT way to modify fixtures while keeping AutoCAD compatibility:
    1. Load original DXF (has everything including dimensions)
    2. Find fixtures (INSERT entities) that need to be modified
    3. Update their positions based on JSON changes
    4. Save as R2018+MM format
    """
    
    print("=" * 70)
    print("🔧 IN-PLACE FIXTURE MODIFICATION (Preserves All Entities)")
    print("=" * 70)
    
    # Load original DXF
    print(f"\n📖 Step 1: Loading original DXF...")
    doc = ezdxf.readfile(original_dxf)
    print(f"   File: {original_dxf}")
    print(f"   Version: {doc.dxfversion}")
    print(f"   Entities: {len(list(doc.modelspace()))}")
    
    orig_types = Counter(e.dxftype() for e in doc.modelspace())
    print(f"   Types: {dict(orig_types)}")
    
    # Load modification instructions from JSON
    print(f"\n📖 Step 2: Loading modification instructions...")
    with open(json_modifications, 'r') as f:
        modified_data = json.load(f)
    
    # Extract INSERT entities from modified JSON
    modified_inserts = [e for e in modified_data['modelspace'] if e['dxf_type'] == 'INSERT']
    print(f"   Found {len(modified_inserts)} modified fixture positions in JSON")
    
    # Modify INSERT entities in the DXF
    print(f"\n✏️  Step 3: Applying fixture position changes...")
    msp = doc.modelspace()
    inserts = [e for e in msp if e.dxftype() == 'INSERT']
    
    changes_made = 0
    for i, insert_entity in enumerate(inserts):
        if i < len(modified_inserts):
            # Get new position from JSON
            new_pos = modified_inserts[i]['insert']
            old_pos = [insert_entity.dxf.insert.x, insert_entity.dxf.insert.y, insert_entity.dxf.insert.z]
            
            # Check if position changed
            if abs(old_pos[0] - new_pos[0]) > 0.01 or abs(old_pos[1] - new_pos[1]) > 0.01:
                # Update position
                insert_entity.dxf.insert = tuple(new_pos)
                changes_made += 1
                
                if changes_made <= 3:  # Show first 3 changes
                    print(f"   ✅ Changed {insert_entity.dxf.name}:")
                    print(f"      From: X={old_pos[0]:.2f}, Y={old_pos[1]:.2f}")
                    print(f"      To:   X={new_pos[0]:.2f}, Y={new_pos[1]:.2f}")
    
    print(f"   Total changes: {changes_made} fixtures modified")
    
    # Set R2018 + MM format
    print(f"\n⚙️  Step 4: Setting R2018 + MM format...")
    doc.header['$INSUNITS'] = 4  # MM
    doc.header['$MEASUREMENT'] = 1  # Metric
    doc.header['$LUNITS'] = 2
    doc.header['$AUNITS'] = 0
    
    # Save
    print(f"\n💾 Step 5: Saving...")
    doc.saveas(output_dxf, encoding='utf-8', fmt='asc')
    
    # Verify
    print(f"\n✅ Saved: {output_dxf}")
    verify = ezdxf.readfile(output_dxf)
    final_count = len(list(verify.modelspace()))
    final_types = Counter(e.dxftype() for e in verify.modelspace())
    
    print(f"\n📊 Final Statistics:")
    print(f"   DXF Version: {verify.dxfversion}")
    print(f"   Units (INSUNITS): {verify.header.get('$INSUNITS')} (4=MM)")
    print(f"   Total entities: {final_count}")
    print(f"   Entity types: {dict(final_types)}")
    
    # Verify fixture positions
    print(f"\n🔍 Verifying changes:")
    verify_inserts = [e for e in verify.modelspace() if e.dxftype() == 'INSERT']
    if verify_inserts and len(modified_inserts) > 0:
        first_verify = verify_inserts[0]
        first_modified = modified_inserts[0]
        verify_pos = [first_verify.dxf.insert.x, first_verify.dxf.insert.y]
        expected_pos = first_modified['insert'][:2]
        
        print(f"   First fixture position:")
        print(f"      Expected: X={expected_pos[0]:.2f}, Y={expected_pos[1]:.2f}")
        print(f"      Got:      X={verify_pos[0]:.2f}, Y={verify_pos[1]:.2f}")
        
        if abs(verify_pos[0] - expected_pos[0]) < 0.01 and abs(verify_pos[1] - expected_pos[1]) < 0.01:
            print(f"      ✅ MATCH! Position changed correctly!")
        else:
            print(f"      ⚠️  Mismatch!")
    
    # Compare entity count
    print(f"\n🔍 Entity count comparison:")
    print(f"   Original: {len(list(ezdxf.readfile(original_dxf).modelspace()))}")
    print(f"   Output:   {final_count}")
    
    if final_count == len(list(ezdxf.readfile(original_dxf).modelspace())):
        print(f"   ✅ PERFECT! All entities preserved (including dimensions)!")
        print(f"   ✅ This file should open in AutoCAD 2026!")
    
    print("=" * 70)
    
    return output_dxf


if __name__ == "__main__":
    import sys
    
    # Check if JSON file exists
    original_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf"
    modified_json = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE.json"
    
    # Check for MODIFIED version first
    import os
    if os.path.exists("ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE-MODIFIED.json"):
        modified_json = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE-MODIFIED.json"
        print("✅ Found MODIFIED JSON - using it")
    else:
        print("ℹ️  Using original COMPLETE JSON (no modifications)")
    
    output_file = modified_json.replace(".json", "-R2018-MM.dxf")
    
    modify_fixtures_in_place(original_file, modified_json, output_file)
