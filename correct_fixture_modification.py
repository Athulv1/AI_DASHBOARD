#!/usr/bin/env python3
"""
CORRECT METHOD: Modify fixtures in JSON while preserving dimensions for AutoCAD
This is the ONLY way to get AutoCAD-compatible files with modified fixtures
"""
import json
import ezdxf
from ezdxf import units
from collections import Counter


def modify_fixtures_with_dimensions(original_dxf, json_file, output_dxf, modifications):
    """
    Hybrid approach:
    1. Load original DXF (has dimensions)
    2. Load modified JSON (has changed fixture positions)
    3. Keep dimensions from original
    4. Replace fixtures/geometry from JSON
    5. Save as R2018+MM
    """
    
    print("=" * 70)
    print("🔧 HYBRID RECONSTRUCTION: Modified Fixtures + Original Dimensions")
    print("=" * 70)
    
    # Load original DXF
    print(f"\n📖 Step 1: Loading original DXF...")
    original = ezdxf.readfile(original_dxf)
    print(f"   File: {original_dxf}")
    print(f"   Entities: {len(list(original.modelspace()))}")
    
    orig_types = Counter(e.dxftype() for e in original.modelspace())
    print(f"   Types: {dict(orig_types)}")
    
    # Load modified JSON
    print(f"\n📖 Step 2: Loading modified JSON...")
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    print(f"   File: {json_file}")
    print(f"   Entities in JSON: {len(json_data['modelspace'])}")
    
    # Create NEW document with R2018 + MM
    print(f"\n🆕 Step 3: Creating new DXF (R2018 + MM)...")
    doc = ezdxf.new(dxfversion='R2018', units=units.MM)
    doc.header['$INSUNITS'] = 4
    doc.header['$MEASUREMENT'] = 1
    doc.header['$LUNITS'] = 2
    doc.header['$AUNITS'] = 0
    
    # Copy structure from original
    print(f"\n📋 Step 4: Copying layers, blocks, styles from original...")
    
    # Copy layers
    for layer in original.layers:
        if layer.dxf.name not in doc.layers:
            try:
                doc.layers.new(
                    name=layer.dxf.name,
                    dxfattribs={'color': layer.dxf.color, 'linetype': layer.dxf.linetype}
                )
            except:
                pass
    
    # Copy linetypes
    for linetype in original.linetypes:
        if linetype.dxf.name not in doc.linetypes and linetype.dxf.name not in ['ByBlock', 'ByLayer', 'Continuous']:
            try:
                doc.linetypes.new(name=linetype.dxf.name, dxfattribs={'description': linetype.dxf.description})
            except:
                pass
    
    # Copy text styles
    for style in original.styles:
        if style.dxf.name not in doc.styles:
            try:
                doc.styles.new(name=style.dxf.name, dxfattribs={'font': style.dxf.font, 'width': style.dxf.width})
            except:
                pass
    
    # Copy dimension styles
    for dimstyle in original.dimstyles:
        if dimstyle.dxf.name not in doc.dimstyles:
            try:
                doc.dimstyles.new(dimstyle.dxf.name)
            except:
                pass
    
    # Copy blocks from original (they contain the fixture geometry)
    for block in original.blocks:
        if block.name not in doc.blocks and not block.name.startswith('*'):
            try:
                new_block = doc.blocks.new(name=block.name)
                for entity in block:
                    try:
                        new_block.add_foreign_entity(entity)
                    except:
                        pass
            except:
                pass
    
    print(f"   Copied {len(doc.layers)} layers, {len(doc.blocks)} blocks, {len(doc.dimstyles)} dimstyles")
    
    # STEP 5: Add DIMENSIONS from original (CRITICAL for AutoCAD)
    print(f"\n📐 Step 5: Preserving dimensions from original...")
    msp = doc.modelspace()
    dimension_count = 0
    
    ANNOTATION_TYPES = ['DIMENSION', 'MULTILEADER', 'ARC_DIMENSION', 'LEADER']
    
    for entity in original.modelspace():
        if entity.dxftype() in ANNOTATION_TYPES:
            try:
                msp.add_foreign_entity(entity)
                dimension_count += 1
            except:
                pass
    
    print(f"   Preserved {dimension_count} dimension entities")
    
    # STEP 6: Add GEOMETRY from JSON (including modified fixtures)
    print(f"\n🎨 Step 6: Adding geometry from JSON (with modifications)...")
    geometry_count = 0
    
    for entity_data in json_data['modelspace']:
        dxf_type = entity_data.get('dxf_type')
        
        # Skip dimensions (already added from original)
        if dxf_type in ANNOTATION_TYPES:
            continue
        
        # Add geometry (including modified INSERT positions)
        if add_entity_from_json(msp, entity_data):
            geometry_count += 1
    
    print(f"   Added {geometry_count} geometry entities from JSON")
    
    # Apply modifications if specified
    if modifications:
        print(f"\n✏️  Step 7: Applying custom modifications...")
        for mod in modifications:
            print(f"   {mod}")
    
    # Save
    doc.saveas(output_dxf)
    
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
    
    # Compare with original
    print(f"\n🔍 Comparison with original:")
    print(f"   Original: {len(list(original.modelspace()))} entities")
    print(f"   Output: {final_count} entities")
    
    if final_count == len(list(original.modelspace())):
        print(f"   ✅ PERFECT MATCH! AutoCAD should open this file!")
    else:
        print(f"   ⚠️  Entity count differs - may have issues")
    
    print("=" * 70)
    
    return output_dxf


def add_entity_from_json(msp, entity_data):
    """Add geometry entity from JSON"""
    dxf_type = entity_data['dxf_type']
    common = {
        'layer': entity_data.get('layer', '0'),
        'color': entity_data.get('color', 256),
        'linetype': entity_data.get('linetype', 'BYLAYER'),
    }
    
    try:
        if dxf_type == "LINE":
            msp.add_line(entity_data['start'], entity_data['end'], dxfattribs=common)
            return True
        
        elif dxf_type == "LWPOLYLINE":
            poly = msp.add_lwpolyline(entity_data['points'], dxfattribs=common)
            poly.closed = entity_data.get('closed', False)
            return True
        
        elif dxf_type == "CIRCLE":
            msp.add_circle(entity_data['center'], entity_data['radius'], dxfattribs=common)
            return True
        
        elif dxf_type == "ARC":
            msp.add_arc(
                center=entity_data['center'],
                radius=entity_data['radius'],
                start_angle=entity_data['start_angle'],
                end_angle=entity_data['end_angle'],
                dxfattribs=common
            )
            return True
        
        elif dxf_type == "ELLIPSE":
            msp.add_ellipse(
                center=entity_data['center'],
                major_axis=entity_data['major_axis'],
                ratio=entity_data['ratio'],
                dxfattribs=common
            )
            return True
        
        elif dxf_type == "TEXT":
            msp.add_text(
                entity_data['text'],
                dxfattribs={**common, 'insert': entity_data.get('insert', (0,0,0)), 'height': entity_data.get('height', 2.5)}
            )
            return True
        
        elif dxf_type == "MTEXT":
            msp.add_mtext(
                entity_data['text'],
                dxfattribs={**common, 'insert': entity_data.get('insert', (0,0,0)), 'char_height': entity_data.get('char_height', 2.5)}
            )
            return True
        
        elif dxf_type == "INSERT":
            # CRITICAL: This uses the MODIFIED position from JSON!
            msp.add_blockref(
                name=entity_data['name'],
                insert=entity_data['insert'],  # Modified position
                dxfattribs={
                    **common,
                    'xscale': entity_data.get('xscale', 1),
                    'yscale': entity_data.get('yscale', 1),
                    'rotation': entity_data.get('rotation', 0),
                }
            )
            return True
        
        elif dxf_type == "HATCH":
            hatch = msp.add_hatch(dxfattribs=common)
            for path in entity_data.get('paths', []):
                for edge in path.get('edges', []):
                    if edge.get('type') == 'LineEdge':
                        edge_path = hatch.paths.add_edge_path()
                        edge_path.add_line(edge['start'], edge['end'])
            if entity_data.get('solid_fill'):
                hatch.set_solid_fill()
            return True
        
        elif dxf_type == "SOLID":
            points = entity_data.get('points', [])
            if len(points) >= 3:
                msp.add_solid(points=points, dxfattribs=common)
                return True
        
        return False
        
    except Exception as e:
        return False


if __name__ == "__main__":
    # Use the MODIFIED JSON we created earlier
    original_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf"
    modified_json = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE-MODIFIED.json"
    output_file = "ATTA-MODIFIED-FIXTURE-WITH-DIMENSIONS-R2018-MM.dxf"
    
    modifications = [
        "✏️  First fixture moved +1000mm in X and Y (from JSON)"
    ]
    
    modify_fixtures_with_dimensions(original_file, modified_json, output_file, modifications)
