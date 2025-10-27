#!/usr/bin/env python3
"""Test script to verify CLINIC_REGULAR_1 dimension fix"""

import ezdxf
import sys
sys.path.insert(0, '.')
from app import dxf_to_json, calculate_block_sizes

# Load DXF file
dxf_file = 'image_F4bz1Dn_processed_W1BgANF_MODIFIED (1).dxf'
print(f'Loading {dxf_file}...')
print('=' * 80)

# Convert to JSON
json_data = dxf_to_json(dxf_file)

print('\nCalculating block sizes...')
print('=' * 80)

# Calculate sizes
block_sizes = calculate_block_sizes(json_data)

print('\n\nCLINIC_REGULAR_1 VERIFICATION:')
print('=' * 80)

if 'CLINIC_REGULAR_1' in block_sizes:
    size = block_sizes['CLINIC_REGULAR_1']
    print(f'Calculated Size: {size["width"]:.1f} × {size["height"]:.1f} mm')
    print(f'Expected Size: 2600.0 × 1700.0 mm')
    
    if abs(size['width'] - 2600.0) < 1 and abs(size['height'] - 1700.0) < 1:
        print('\n✅ SUCCESS! CLINIC_REGULAR_1 now shows correct dimensions!')
    elif abs(size['width'] - 1700.0) < 1 and abs(size['height'] - 2600.0) < 1:
        print('\n✅ SUCCESS! CLINIC_REGULAR_1 shows correct dimensions (swapped)!')
    else:
        print(f'\n❌ FAILED! Still showing wrong dimensions.')
        print(f'   Got: {size["width"]:.1f} × {size["height"]:.1f} mm')
        print(f'   Expected: 2600.0 × 1700.0 mm or 1700.0 × 2600.0 mm')
else:
    print('❌ CLINIC_REGULAR_1 not found in block_sizes!')
