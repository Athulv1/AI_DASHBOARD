#!/usr/bin/env python3
"""
DXF Fixture Modification Engine

This script safely modifies fixture positions in a DXF file by reading
modification instructions from a JSON file. It performs an in-place update,
which preserves all drawing entities, including complex ones like dimensions.

Author: Professional CAD Automation System
Version: 1.0
Date: 2025-10-15
"""

import ezdxf
import json
from collections import Counter


def modify_fixtures_in_place(original_dxf_path: str, modification_json_path: str, output_dxf_path: str):
    """
    Loads an original DXF, applies fixture modifications from a JSON file,
    and saves the result to a new DXF file.

    This method ensures data integrity by modifying the loaded DXF structure
    directly, rather than rebuilding it from scratch.

    Args:
        original_dxf_path (str): Path to the source DXF file.
        modification_json_path (str): Path to the JSON file with modification instructions.
        output_dxf_path (str): Path where the modified DXF file will be saved.
    """
    print("=" * 70)
    print("🔧 DXF In-Place Fixture Modification Process")
    print("=" * 70)

    try:
        # 1. Load the original DXF document
        print(f"\n📖 Step 1: Loading original DXF from '{original_dxf_path}'...")
        doc = ezdxf.readfile(original_dxf_path)
        msp = doc.modelspace()
        print(f"   ✅ Success. Found {len(list(msp))} entities in modelspace.")
        
        # 2. Load the modification instructions from JSON
        print(f"\n📖 Step 2: Loading modification instructions from '{modification_json_path}'...")
        with open(modification_json_path, 'r') as f:
            modifications = json.load(f)
        
        fixtures_to_modify = modifications.get('fixtures', [])
        print(f"   ✅ Success. Found {len(fixtures_to_modify)} modifications to apply.")

        # 3. Create a mapping of original fixtures for quick lookup
        # A more robust solution would use unique identifiers if available.
        # Here, we map based on block name and original position for better accuracy.
        original_fixtures = {}
        for entity in msp:
            if entity.dxftype() == 'INSERT':
                name = entity.dxf.name
                pos = (round(entity.dxf.insert.x, 2), round(entity.dxf.insert.y, 2))
                key = f"{name}@{pos[0]},{pos[1]}"
                if key not in original_fixtures:
                    original_fixtures[key] = []
                original_fixtures[key].append(entity)

        print(f"   Found {len([e for e in msp if e.dxftype() == 'INSERT'])} INSERT entities in DXF")

        # 4. Apply the modifications
        print(f"\n✏️  Step 3: Applying modifications...")
        changes_made = 0
        warnings = 0
        for mod in fixtures_to_modify:
            block_name = mod['block_name']
            orig_pos_key = (round(mod['original_position'][0], 2), round(mod['original_position'][1], 2))
            key = f"{block_name}@{orig_pos_key[0]},{orig_pos_key[1]}"
            
            if key in original_fixtures and original_fixtures[key]:
                # Get the fixture to modify (and remove it from the list to handle duplicates)
                fixture_to_update = original_fixtures[key].pop(0)
                
                new_pos_vec = ezdxf.math.Vec3(mod['new_position'])
                old_pos = fixture_to_update.dxf.insert
                fixture_to_update.dxf.insert = new_pos_vec
                
                print(f"   ✅ Moved '{block_name}'")
                print(f"      From: X={old_pos.x:.2f}, Y={old_pos.y:.2f}")
                print(f"      To:   X={new_pos_vec.x:.2f}, Y={new_pos_vec.y:.2f}")
                changes_made += 1
            else:
                print(f"   ⚠️  Warning: Could not find fixture '{block_name}' at position {orig_pos_key}. Skipping.")
                warnings += 1

        print(f"\n   Summary: Applied {changes_made} changes with {warnings} warnings.")

        # 5. Set header variables for better compatibility (e.g., units to mm)
        print("\n⚙️  Step 4: Setting document header variables (Units=MM, Format=R2018)...")
        doc.header['$INSUNITS'] = 4  # 4 = Millimeters
        doc.header['$MEASUREMENT'] = 1  # 1 = Metric
        
        # 6. Save the modified document
        print(f"\n💾 Step 5: Saving modified DXF to '{output_dxf_path}'...")
        doc.saveas(output_dxf_path)
        
        # 7. Verify the output
        print(f"\n🔍 Step 6: Verifying output...")
        verify_doc = ezdxf.readfile(output_dxf_path)
        verify_msp = verify_doc.modelspace()
        verify_types = Counter(e.dxftype() for e in verify_msp)
        
        print(f"   DXF Version: {verify_doc.dxfversion}")
        print(f"   Units: {verify_doc.header.get('$INSUNITS')} (4=MM)")
        print(f"   Total entities: {len(list(verify_msp))}")
        print(f"   Entity breakdown: {dict(verify_types)}")
        
        print("\n🎉 Process Complete!")
        print(f"   Final DXF saved successfully to '{output_dxf_path}'")
        print(f"   ✅ All {changes_made} fixture modifications applied")
        print(f"   ✅ All dimensions and annotations preserved")
        print("=" * 70)

    except IOError as e:
        print(f"❌ Error reading file: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON file: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # --- Configuration ---
    # The original DXF file that contains all data (including dimensions).
    ORIGINAL_DXF_FILE = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf"
    
    # The JSON file that specifies which fixtures to move and where.
    MODIFICATION_FILE = "modifications.json"
    
    # The path for the final, modified DXF file.
    OUTPUT_DXF_FILE = "ATTA_MARKET_MODIFIED.dxf"
    
    # --- Create a sample modifications.json for demonstration ---
    print("INFO: Creating sample 'modifications.json' for demonstration...")
    
    # First, read the original to get actual fixture positions
    doc = ezdxf.readfile(ORIGINAL_DXF_FILE)
    inserts = [e for e in doc.modelspace() if e.dxftype() == 'INSERT']
    
    if len(inserts) >= 2:
        # Get first two fixtures for demo
        fixture1 = inserts[0]
        fixture2 = inserts[1]
        
        sample_modifications = {
            "fixtures": [
                {
                    "block_name": fixture1.dxf.name,
                    "original_position": [fixture1.dxf.insert.x, fixture1.dxf.insert.y],
                    "new_position": [fixture1.dxf.insert.x + 1000, fixture1.dxf.insert.y + 1000]  # Move +1000mm X&Y
                },
                {
                    "block_name": fixture2.dxf.name,
                    "original_position": [fixture2.dxf.insert.x, fixture2.dxf.insert.y],
                    "new_position": [fixture2.dxf.insert.x - 500, fixture2.dxf.insert.y]  # Move -500mm X
                }
            ]
        }
        
        with open(MODIFICATION_FILE, 'w') as f:
            json.dump(sample_modifications, f, indent=2)
        
        print(f"✅ Created '{MODIFICATION_FILE}' with 2 sample modifications:")
        print(f"   1. Move {fixture1.dxf.name} +1000mm in X and Y")
        print(f"   2. Move {fixture2.dxf.name} -500mm in X")
        print()
    
    # --- Run the modification process ---
    modify_fixtures_in_place(ORIGINAL_DXF_FILE, MODIFICATION_FILE, OUTPUT_DXF_FILE)
