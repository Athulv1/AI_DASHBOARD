#!/usr/bin/env python3
"""
DEMONSTRATION: Change fixture position in JSON and reconstruct DXF
Shows how to modify entity positions and rebuild with R2018+MM format
"""
import json
import ezdxf
from ezdxf import units


def demo_fixture_position_change():
    """
    Complete workflow demonstrating fixture position modification:
    1. Load full entity JSON (from enhanced_dxf_to_json.py)
    2. Find and modify a fixture (INSERT) position
    3. Reconstruct DXF with R2018+MM format
    4. Verify the change
    """
    
    # Use the FULL JSON from enhanced_dxf_to_json.py (ATTA file has full data)
    json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE.json"
    
    print("=" * 70)
    print("🎯 DEMONSTRATION: Modifying Fixture Position via JSON")
    print("=" * 70)
    
    # STEP 1: Load full JSON
    print(f"\n📖 Step 1: Loading JSON with full entity data...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Check if this has full entity data
    if isinstance(data.get('modelspace'), list):
        print(f"   ✅ JSON has full entity data: {len(data['modelspace'])} entities")
    else:
        print(f"   ❌ This JSON only has summary data. Need full entity export.")
        return
    
    # STEP 2: Find INSERT entities (fixtures/blocks)
    print(f"\n🔍 Step 2: Finding INSERT entities (fixtures)...")
    insert_entities = [e for e in data['modelspace'] if e['dxf_type'] == 'INSERT']
    print(f"   Found {len(insert_entities)} fixture instances")
    
    if insert_entities:
        # Show first few fixtures
        print(f"\n   📦 First 5 fixtures:")
        for i, entity in enumerate(insert_entities[:5], 1):
            block_name = entity.get('name', 'Unknown')
            position = entity.get('insert', [0, 0, 0])
            print(f"      {i}. Block: {block_name}")
            print(f"         Position: X={position[0]:.2f}, Y={position[1]:.2f}, Z={position[2]:.2f}")
        
        # STEP 3: Modify the first fixture position
        print(f"\n✏️  Step 3: Modifying first fixture position...")
        original_pos = insert_entities[0]['insert'].copy()
        print(f"   Original position: {original_pos}")
        
        # Change position - move 1000mm in X and Y direction
        insert_entities[0]['insert'][0] += 1000  # Move 1000mm in X
        insert_entities[0]['insert'][1] += 1000  # Move 1000mm in Y
        new_pos = insert_entities[0]['insert']
        print(f"   New position: {new_pos}")
        print(f"   ✅ Changed: moved +1000mm in X and Y directions")
        
        # Save modified JSON
        modified_json = json_file.replace('.json', '-MODIFIED.json')
        with open(modified_json, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   💾 Saved modified JSON: {modified_json}")
    
    # STEP 4: Reconstruct DXF from modified JSON with R2018+MM
    print(f"\n🔨 Step 4: Reconstructing DXF from modified JSON...")
    output_dxf = "DEMO-MODIFIED-FIXTURE-R2018-MM.dxf"
    
    # Create new DXF with R2018 + MM
    doc = ezdxf.new(dxfversion='R2018', units=units.MM)
    msp = doc.modelspace()
    
    # Set units
    doc.header['$INSUNITS'] = 4  # MM
    doc.header['$MEASUREMENT'] = 1  # Metric
    
    # Recreate layers
    for layer_data in data.get('layers', []):
        if layer_data['name'] not in ['0', 'Defpoints']:
            try:
                doc.layers.new(
                    name=layer_data['name'],
                    dxfattribs={
                        'color': layer_data['color'],
                        'linetype': layer_data['linetype'],
                    }
                )
            except:
                pass
    
    # Recreate blocks
    for block_name, block_data in data.get('blocks', {}).items():
        if block_name not in doc.blocks:
            block = doc.blocks.new(name=block_name)
            # Add entities to block (simplified for demo)
            for entity_data in block_data.get('entities', []):
                add_entity_simple(block, entity_data)
    
    # Add modelspace entities (including modified INSERT)
    added = 0
    for entity_data in data['modelspace']:
        if add_entity_simple(msp, entity_data):
            added += 1
    
    # Save
    doc.saveas(output_dxf)
    
    print(f"   ✅ Reconstructed DXF: {output_dxf}")
    print(f"   📊 Added {added} entities")
    
    # STEP 5: Verify
    print(f"\n🔍 Step 5: Verifying the change...")
    verify = ezdxf.readfile(output_dxf)
    verify_inserts = [e for e in verify.modelspace() if e.dxftype() == 'INSERT']
    
    if verify_inserts:
        first_insert = verify_inserts[0]
        verify_pos = [first_insert.dxf.insert.x, first_insert.dxf.insert.y, first_insert.dxf.insert.z]
        print(f"   Original position in JSON: {original_pos}")
        print(f"   New position in JSON: {new_pos}")
        print(f"   Position in DXF: {verify_pos}")
        
        if abs(verify_pos[0] - new_pos[0]) < 0.01 and abs(verify_pos[1] - new_pos[1]) < 0.01:
            print(f"   ✅ SUCCESS! Fixture position changed correctly!")
        else:
            print(f"   ⚠️  Position mismatch - may need adjustment")
    
    print(f"\n" + "=" * 70)
    print(f"✅ DEMONSTRATION COMPLETE!")
    print(f"   Modified JSON: {modified_json}")
    print(f"   Output DXF: {output_dxf}")
    print(f"   Format: R2018, Units: MM")
    print("=" * 70)
    
    return output_dxf


def add_entity_simple(container, entity_data):
    """Simplified entity addition for demo"""
    dxf_type = entity_data['dxf_type']
    
    common = {
        'layer': entity_data.get('layer', '0'),
        'color': entity_data.get('color', 256),
        'linetype': entity_data.get('linetype', 'BYLAYER'),
    }
    
    try:
        if dxf_type == "LINE":
            container.add_line(entity_data['start'], entity_data['end'], dxfattribs=common)
            return True
        
        elif dxf_type == "LWPOLYLINE":
            poly = container.add_lwpolyline(entity_data['points'], dxfattribs=common)
            poly.closed = entity_data.get('closed', False)
            return True
        
        elif dxf_type == "CIRCLE":
            container.add_circle(entity_data['center'], entity_data['radius'], dxfattribs=common)
            return True
        
        elif dxf_type == "ARC":
            container.add_arc(
                center=entity_data['center'],
                radius=entity_data['radius'],
                start_angle=entity_data['start_angle'],
                end_angle=entity_data['end_angle'],
                dxfattribs=common
            )
            return True
        
        elif dxf_type == "MTEXT":
            container.add_mtext(
                entity_data['text'],
                dxfattribs={**common, 'insert': entity_data.get('insert', (0,0,0)), 'char_height': entity_data.get('char_height', 2.5)}
            )
            return True
        
        elif dxf_type == "INSERT":
            # This is the fixture - use modified position from JSON
            container.add_blockref(
                name=entity_data['name'],
                insert=entity_data['insert'],  # Uses modified position!
                dxfattribs={
                    **common,
                    'xscale': entity_data.get('xscale', 1),
                    'yscale': entity_data.get('yscale', 1),
                    'rotation': entity_data.get('rotation', 0),
                }
            )
            return True
        
        elif dxf_type == "HATCH":
            hatch = container.add_hatch(dxfattribs=common)
            for path in entity_data.get('paths', []):
                for edge in path.get('edges', []):
                    if edge.get('type') == 'LineEdge':
                        edge_path = hatch.paths.add_edge_path()
                        edge_path.add_line(edge['start'], edge['end'])
            if entity_data.get('solid_fill'):
                hatch.set_solid_fill()
            return True
        
        return False
        
    except Exception as e:
        return False


if __name__ == "__main__":
    demo_fixture_position_change()
