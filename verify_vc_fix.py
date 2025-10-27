#!/usr/bin/env python3
"""
Quick verification that VC fixtures are correctly resolved
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import calculate_block_sizes, dxf_to_json
import json

print("=" * 80)
print("VERIFYING VC FIXTURE SIZE FIX")
print("=" * 80)
print()

# Load a DXF file
dxf_file = 'image_F4bz1Dn_processed_W1BgANF_MODIFIED (1).dxf'

if os.path.exists(dxf_file):
    print(f"📄 Loading: {dxf_file}")
    
    # Convert to JSON
    json_data = dxf_to_json(dxf_file)
    
    print(f"   Blocks: {len(json_data.get('blocks', {}))}")
    print()
    
    # Calculate sizes
    block_sizes = calculate_block_sizes(json_data, dxf_file)
    
    print()
    print("🔍 VC FIXTURE SIZES:")
    print("-" * 80)
    
    vc_fixtures_found = False
    for i in range(1, 11):
        block_name = f'VC_FIXTURE_LARGE_{i}'
        if block_name in block_sizes:
            vc_fixtures_found = True
            size = block_sizes[block_name]
            width = size['width']
            height = size['height']
            
            if width == 300 and height == 300:
                print(f"   ❌ {block_name}: {width:.1f} × {height:.1f} mm (DEFAULT - NOT RESOLVED!)")
            else:
                print(f"   ✅ {block_name}: {width:.1f} × {height:.1f} mm (CORRECTLY RESOLVED)")
    
    if not vc_fixtures_found:
        print("   ⚠️  No VC_FIXTURE_LARGE blocks found in this file")
    
    print()
    print("=" * 80)
    
    # Count correct vs incorrect
    vc_correct = sum(1 for i in range(1, 11) 
                     if f'VC_FIXTURE_LARGE_{i}' in block_sizes 
                     and block_sizes[f'VC_FIXTURE_LARGE_{i}']['width'] != 300)
    vc_total = sum(1 for i in range(1, 11) if f'VC_FIXTURE_LARGE_{i}' in block_sizes)
    
    if vc_total > 0:
        print(f"RESULT: {vc_correct}/{vc_total} VC fixtures correctly resolved")
        if vc_correct == vc_total:
            print("✅ ALL VC FIXTURES ARE CORRECT!")
        else:
            print("❌ SOME VC FIXTURES STILL SHOWING 300×300!")
    
    print("=" * 80)
    
else:
    print(f"❌ Test file not found: {dxf_file}")
