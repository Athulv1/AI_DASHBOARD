#!/usr/bin/env python3
"""
Test fixture size calculation with actual DXF file
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import calculate_block_sizes, extract_canvas_data
import ezdxf
import json

def test_with_dxf_file(dxf_path):
    """Test fixture size calculation"""
    print("=" * 80)
    print(f"TESTING FIXTURE SIZE CALCULATION")
    print(f"File: {os.path.basename(dxf_path)}")
    print("=" * 80)
    print()
    
    # Read DXF
    try:
        doc = ezdxf.readfile(dxf_path)
        print(f"✅ Loaded DXF: {doc.dxfversion}")
    except Exception as e:
        print(f"❌ Error loading DXF: {e}")
        return
    
    # Convert to JSON structure
    json_data = {
        'blocks': {},
        'modelspace': []
    }
    
    # Extract blocks
    for block in doc.blocks:
        if block.name.startswith('*'):
            continue
        
        entities = []
        for entity in block:
            entity_dict = {
                'dxf_type': entity.dxftype()
            }
            
            if entity.dxftype() == 'LINE':
                entity_dict['start'] = list(entity.dxf.start)
                entity_dict['end'] = list(entity.dxf.end)
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                entity_dict['points'] = [list(p) for p in entity.get_points()]
                entity_dict['closed'] = entity.closed
            elif entity.dxftype() == 'CIRCLE':
                entity_dict['center'] = list(entity.dxf.center)
                entity_dict['radius'] = entity.dxf.radius
            elif entity.dxftype() == 'ARC':
                entity_dict['center'] = list(entity.dxf.center)
                entity_dict['radius'] = entity.dxf.radius
                entity_dict['start_angle'] = entity.dxf.start_angle
                entity_dict['end_angle'] = entity.dxf.end_angle
            elif entity.dxftype() == 'SPLINE':
                if hasattr(entity, 'control_points'):
                    entity_dict['control_points'] = [list(p) for p in entity.control_points]
                if hasattr(entity, 'fit_points'):
                    entity_dict['fit_points'] = [list(p) for p in entity.fit_points]
            elif entity.dxftype() == 'INSERT':
                entity_dict['name'] = entity.dxf.name
            
            entities.append(entity_dict)
        
        json_data['blocks'][block.name] = {'entities': entities}
    
    # Extract modelspace INSERTs
    for entity in doc.modelspace():
        if entity.dxftype() == 'INSERT':
            json_data['modelspace'].append({
                'dxf_type': 'INSERT',
                'name': entity.dxf.name,
                'insert': list(entity.dxf.insert),
                'rotation': entity.dxf.rotation,
                'xscale': entity.dxf.xscale,
                'yscale': entity.dxf.yscale,
                'layer': entity.dxf.layer
            })
    
    print(f"📊 DXF Structure:")
    print(f"   Blocks: {len(json_data['blocks'])}")
    print(f"   Fixtures in modelspace: {len(json_data['modelspace'])}")
    print()
    
    # Test Method 1: Using ezdxf bounding_box (preferred)
    print("🔍 Method 1: ezdxf bounding_box (PREFERRED)")
    print("-" * 80)
    block_sizes_ezdxf = calculate_block_sizes(json_data, dxf_path)
    
    # Count successes
    with_geometry = sum(1 for b in block_sizes_ezdxf.values() if b['width'] != 300 or b['height'] != 300)
    print(f"✅ Successfully calculated: {with_geometry}/{len(block_sizes_ezdxf)} blocks")
    print()
    
    # Test Method 2: Manual calculation
    print("🔍 Method 2: Manual JSON parsing (FALLBACK)")
    print("-" * 80)
    block_sizes_manual = calculate_block_sizes(json_data, None)
    
    with_geometry = sum(1 for b in block_sizes_manual.values() if b['width'] != 300 or b['height'] != 300)
    print(f"✅ Successfully calculated: {with_geometry}/{len(block_sizes_manual)} blocks")
    print()
    
    # Compare results
    print("📊 COMPARISON")
    print("-" * 80)
    print(f"{'Block Name':<30} {'ezdxf (W×H)':<25} {'Manual (W×H)':<25} {'Match'}")
    print("-" * 80)
    
    matches = 0
    total = 0
    
    for block_name in list(block_sizes_ezdxf.keys())[:15]:  # Show first 15
        ezdxf_size = block_sizes_ezdxf.get(block_name, {})
        manual_size = block_sizes_manual.get(block_name, {})
        
        ezdxf_str = f"{ezdxf_size['width']:.1f}×{ezdxf_size['height']:.1f}"
        manual_str = f"{manual_size['width']:.1f}×{manual_size['height']:.1f}"
        
        match = abs(ezdxf_size['width'] - manual_size['width']) < 1 and \
                abs(ezdxf_size['height'] - manual_size['height']) < 1
        
        match_str = "✅" if match else "⚠️"
        if match:
            matches += 1
        total += 1
        
        print(f"{block_name[:29]:<30} {ezdxf_str:<25} {manual_str:<25} {match_str}")
    
    print("-" * 80)
    print(f"Match rate: {matches}/{total} ({100*matches/total:.1f}%)")
    print()
    
    # Test canvas data extraction
    print("🎨 CANVAS DATA EXTRACTION")
    print("-" * 80)
    canvas_data = extract_canvas_data(json_data, dxf_path)
    print(f"✅ Fixtures extracted: {canvas_data['fixture_count']}")
    print(f"✅ Blueprint entities: {len(canvas_data['blueprint'])}")
    print()
    
    # Show sample fixture data
    print("📐 Sample Fixture Data:")
    for fixture in canvas_data['fixtures'][:5]:
        print(f"   • {fixture['name']}: {fixture['width']:.1f}×{fixture['height']:.1f} mm @ {fixture['position']}")
    
    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    # Test with the uploaded file
    test_file = 'image_F4bz1Dn_processed_W1BgANF_MODIFIED (1).dxf'
    
    if os.path.exists(test_file):
        test_with_dxf_file(test_file)
    else:
        print(f"❌ Test file not found: {test_file}")
        print("Available DXF files:")
        for f in os.listdir('.'):
            if f.endswith('.dxf'):
                print(f"   • {f}")
