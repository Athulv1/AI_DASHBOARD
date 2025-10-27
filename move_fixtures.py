#!/usr/bin/env python3
"""
Universal Fixture Mover for DXF Files
======================================

This script moves fixtures in any DXF file based on modifications.json

USAGE:
------
1. Edit modifications.json with the fixtures you want to move
2. Run: python3 move_fixtures.py

The script will:
- Read the original DXF file
- Apply fixture position changes from modifications.json
- Save the result as a new DXF file in R2018+MM format (AutoCAD compatible)

Author: GitHub Copilot
Version: 1.0
"""

import ezdxf
import json
import sys
import os


def move_fixtures(input_dxf, modifications_file, output_dxf):
    """
    Move fixtures in a DXF file based on modifications JSON
    
    Args:
        input_dxf: Path to input DXF file
        modifications_file: Path to modifications.json
        output_dxf: Path to output DXF file
    """
    
    print('=' * 80)
    print('🔧 UNIVERSAL FIXTURE MOVER')
    print('=' * 80)
    
    # Check if files exist
    if not os.path.exists(input_dxf):
        print(f'❌ ERROR: Input DXF file not found: {input_dxf}')
        return False
    
    if not os.path.exists(modifications_file):
        print(f'❌ ERROR: Modifications file not found: {modifications_file}')
        return False
    
    # Load original DXF
    print(f'\n📖 Loading DXF file...')
    print(f'   Input: {input_dxf}')
    try:
        doc = ezdxf.readfile(input_dxf)
        msp = doc.modelspace()
        total_entities = len(list(msp))
        print(f'   ✅ Loaded successfully')
        print(f'   Total entities: {total_entities}')
    except Exception as e:
        print(f'❌ ERROR loading DXF: {e}')
        return False
    
    # Load modifications
    print(f'\n📖 Loading modifications...')
    print(f'   File: {modifications_file}')
    try:
        with open(modifications_file, 'r') as f:
            modifications = json.load(f)
        
        fixtures_to_modify = modifications.get('fixtures', [])
        print(f'   ✅ Loaded successfully')
        print(f'   Fixtures to modify: {len(fixtures_to_modify)}')
    except Exception as e:
        print(f'❌ ERROR loading modifications: {e}')
        return False
    
    if len(fixtures_to_modify) == 0:
        print(f'\n⚠️  WARNING: No fixtures to modify in {modifications_file}')
        return False
    
    # Create fixture mapping
    print(f'\n🔍 Scanning fixtures in DXF...')
    original_fixtures = {}
    fixture_count = 0
    
    for entity in msp:
        if entity.dxftype() == 'INSERT':
            fixture_count += 1
            name = entity.dxf.name
            pos = (round(entity.dxf.insert.x, 2), round(entity.dxf.insert.y, 2))
            key = f'{name}@{pos[0]},{pos[1]}'
            
            if key not in original_fixtures:
                original_fixtures[key] = []
            original_fixtures[key].append(entity)
    
    print(f'   Total fixtures found: {fixture_count}')
    print(f'   Unique fixture positions: {len(original_fixtures)}')
    
    # Apply modifications
    print(f'\n✏️  Applying modifications...')
    print('-' * 80)
    changes_made = 0
    changes_failed = 0
    
    for i, mod in enumerate(fixtures_to_modify, 1):
        block_name = mod.get('block_name', 'UNKNOWN')
        orig_pos = mod.get('original_position', [0, 0])
        new_pos = mod.get('new_position', [0, 0])
        
        orig_pos_key = (round(orig_pos[0], 2), round(orig_pos[1], 2))
        key = f'{block_name}@{orig_pos_key[0]},{orig_pos_key[1]}'
        
        print(f'\n{i}. Fixture: "{block_name}"')
        print(f'   Looking for: {key}')
        
        if key in original_fixtures and original_fixtures[key]:
            fixture_to_update = original_fixtures[key].pop(0)
            new_pos_vec = ezdxf.math.Vec3(new_pos)
            old_pos = fixture_to_update.dxf.insert
            fixture_to_update.dxf.insert = new_pos_vec
            
            # Calculate movement
            delta_x = new_pos_vec.x - old_pos.x
            delta_y = new_pos_vec.y - old_pos.y
            distance = (delta_x**2 + delta_y**2)**0.5
            
            print(f'   ✅ MOVED SUCCESSFULLY')
            print(f'      From: X={old_pos.x:.2f}, Y={old_pos.y:.2f}')
            print(f'      To:   X={new_pos_vec.x:.2f}, Y={new_pos_vec.y:.2f}')
            print(f'      Delta: ΔX={delta_x:.2f}mm, ΔY={delta_y:.2f}mm')
            print(f'      Distance: {distance:.2f}mm')
            changes_made += 1
        else:
            print(f'   ❌ FAILED - Fixture not found')
            print(f'      Make sure the block name and position are exact!')
            changes_failed += 1
    
    print('\n' + '-' * 80)
    print(f'\n📊 Summary:')
    print(f'   ✅ Successfully moved: {changes_made} fixture(s)')
    if changes_failed > 0:
        print(f'   ❌ Failed to move: {changes_failed} fixture(s)')
    
    # Set R2018 + MM format (AutoCAD 2026 compatible)
    print(f'\n⚙️  Setting DXF format...')
    doc.header['$INSUNITS'] = 4  # MM units
    doc.header['$MEASUREMENT'] = 1  # Metric
    print(f'   Format: R2018 (AC1032)')
    print(f'   Units: MM (Millimeters)')
    
    # Save
    print(f'\n💾 Saving modified DXF...')
    print(f'   Output: {output_dxf}')
    try:
        doc.saveas(output_dxf)
        print(f'   ✅ Saved successfully')
    except Exception as e:
        print(f'❌ ERROR saving DXF: {e}')
        return False
    
    # Verify
    print(f'\n🔍 Verifying output...')
    try:
        verify_doc = ezdxf.readfile(output_dxf)
        verify_msp = verify_doc.modelspace()
        verify_entities = len(list(verify_msp))
        
        print(f'   Total entities: {verify_entities}')
        print(f'   DXF Version: {verify_doc.dxfversion}')
        print(f'   Units: {verify_doc.header.get("$INSUNITS")} (4=MM)')
        
        if verify_entities == total_entities:
            print(f'   ✅ All entities preserved!')
        else:
            print(f'   ⚠️  Entity count changed: {total_entities} → {verify_entities}')
    except Exception as e:
        print(f'⚠️  WARNING: Could not verify output: {e}')
    
    print('\n' + '=' * 80)
    if changes_made > 0:
        print('✅ SUCCESS! Fixtures moved successfully')
    else:
        print('⚠️  NO CHANGES MADE')
    print('=' * 80)
    print()
    
    return changes_made > 0


def main():
    """Main entry point"""
    
    # Default configuration (you can edit these)
    INPUT_DXF = 'ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf'
    MODIFICATIONS_FILE = 'modifications.json'
    OUTPUT_DXF = 'OUTPUT-MODIFIED.dxf'
    
    # Check if command line arguments are provided
    if len(sys.argv) >= 2:
        INPUT_DXF = sys.argv[1]
    if len(sys.argv) >= 3:
        OUTPUT_DXF = sys.argv[2]
    if len(sys.argv) >= 4:
        MODIFICATIONS_FILE = sys.argv[3]
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      UNIVERSAL FIXTURE MOVER                               ║
║                                                                            ║
║  This script moves fixtures in DXF files based on modifications.json      ║
╚════════════════════════════════════════════════════════════════════════════╝

USAGE:
------
Method 1: Edit the script and run
    1. Edit INPUT_DXF, OUTPUT_DXF in this script (lines 133-135)
    2. Edit modifications.json with fixtures to move
    3. Run: python3 move_fixtures.py

Method 2: Use command line arguments
    python3 move_fixtures.py <input.dxf> <output.dxf> [modifications.json]

CURRENT CONFIGURATION:
----------------------
""")
    
    print(f"Input DXF:       {INPUT_DXF}")
    print(f"Output DXF:      {OUTPUT_DXF}")
    print(f"Modifications:   {MODIFICATIONS_FILE}")
    print()
    
    # Run the fixture mover
    success = move_fixtures(INPUT_DXF, MODIFICATIONS_FILE, OUTPUT_DXF)
    
    if success:
        print(f"\n✅ DONE! You can now open '{OUTPUT_DXF}' in AutoCAD 2026")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED! Please check the errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
