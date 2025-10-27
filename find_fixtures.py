#!/usr/bin/env python3
"""
Fixture Finder - Find all fixtures in a DXF file
=================================================

This helper script lists all fixtures (INSERT entities) in a DXF file
to help you identify which fixtures to move.

USAGE:
------
    python3 find_fixtures.py YOUR-FILE.dxf

Or edit the DXF_FILE variable below and run:
    python3 find_fixtures.py
"""

import ezdxf
import sys
import os


def find_fixtures(dxf_file, filter_name=None):
    """
    Find all fixtures in a DXF file
    
    Args:
        dxf_file: Path to DXF file
        filter_name: Optional filter to search for specific fixture names
    """
    
    print('=' * 80)
    print('🔍 FIXTURE FINDER')
    print('=' * 80)
    
    if not os.path.exists(dxf_file):
        print(f'\n❌ ERROR: File not found: {dxf_file}')
        return
    
    print(f'\n📖 Loading: {dxf_file}')
    
    try:
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()
    except Exception as e:
        print(f'❌ ERROR: Could not read DXF file: {e}')
        return
    
    print(f'✅ Loaded successfully\n')
    
    # Collect all fixtures
    fixtures = []
    for entity in msp:
        if entity.dxftype() == 'INSERT':
            name = entity.dxf.name
            pos = entity.dxf.insert
            
            # Apply filter if specified
            if filter_name is None or filter_name.lower() in name.lower():
                fixtures.append({
                    'name': name,
                    'x': pos.x,
                    'y': pos.y,
                    'z': pos.z,
                    'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
                })
    
    if len(fixtures) == 0:
        if filter_name:
            print(f'❌ No fixtures found matching: "{filter_name}"')
        else:
            print(f'❌ No fixtures found in this DXF file')
        return
    
    # Group by fixture type
    fixture_types = {}
    for fixture in fixtures:
        name = fixture['name']
        if name not in fixture_types:
            fixture_types[name] = []
        fixture_types[name].append(fixture)
    
    # Display results
    print(f'📊 Found {len(fixtures)} fixture(s) of {len(fixture_types)} type(s)')
    
    if filter_name:
        print(f'🔎 Filtered by: "{filter_name}"')
    
    print('\n' + '=' * 80)
    print('FIXTURES LIST')
    print('=' * 80)
    
    total_count = 0
    for fixture_name in sorted(fixture_types.keys()):
        fixture_list = fixture_types[fixture_name]
        total_count += len(fixture_list)
        
        print(f'\n📦 Block: "{fixture_name}"')
        print(f'   Count: {len(fixture_list)} instance(s)')
        print('-' * 80)
        
        for i, fixture in enumerate(fixture_list, 1):
            print(f'   {i}. Position: X={fixture["x"]:.2f}, Y={fixture["y"]:.2f}, Z={fixture["z"]:.2f}')
            if fixture['rotation'] != 0:
                print(f'      Rotation: {fixture["rotation"]:.2f}°')
    
    print('\n' + '=' * 80)
    print('📋 COPY-PASTE TEMPLATE FOR modifications.json')
    print('=' * 80)
    print('\nTo move a fixture, copy one of these templates:\n')
    
    # Show first 3 fixtures as examples
    example_count = 0
    for fixture_name in sorted(fixture_types.keys()):
        if example_count >= 3:
            break
        
        fixture_list = fixture_types[fixture_name]
        fixture = fixture_list[0]  # Take first instance
        
        print(f'// Example {example_count + 1}: Move "{fixture_name}"')
        print('{')
        print(f'  "block_name": "{fixture["name"]}",')
        print(f'  "original_position": [{fixture["x"]}, {fixture["y"]}],')
        print(f'  "new_position": [NEW_X_HERE, NEW_Y_HERE]')
        print('},')
        print()
        
        example_count += 1
    
    print('=' * 80)
    print(f'\n✅ Total fixtures found: {total_count}')
    print('=' * 80)
    print()


def main():
    """Main entry point"""
    
    # Default DXF file (you can edit this)
    DXF_FILE = 'ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf'
    FILTER = None  # Set to search term or None for all fixtures
    
    # Check command line arguments
    if len(sys.argv) >= 2:
        DXF_FILE = sys.argv[1]
    if len(sys.argv) >= 3:
        FILTER = sys.argv[2]
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                           FIXTURE FINDER                                   ║
║                                                                            ║
║  Find all fixtures (INSERT entities) in a DXF file                        ║
╚════════════════════════════════════════════════════════════════════════════╝

USAGE:
------
Method 1: Edit this script
    1. Edit DXF_FILE variable (line 70)
    2. Run: python3 find_fixtures.py

Method 2: Command line
    python3 find_fixtures.py <file.dxf> [search_term]

Examples:
    python3 find_fixtures.py MYSTORE.dxf
    python3 find_fixtures.py MYSTORE.dxf table    (find only tables)
    python3 find_fixtures.py MYSTORE.dxf chair    (find only chairs)

""")
    
    print(f"Current file: {DXF_FILE}")
    if FILTER:
        print(f"Filter: {FILTER}")
    print()
    
    find_fixtures(DXF_FILE, FILTER)


if __name__ == "__main__":
    main()
