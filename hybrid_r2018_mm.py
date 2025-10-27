import ezdxf
from ezdxf import units
import json
from collections import Counter


def hybrid_reconstruction_r2018_mm(original_dxf, json_path, output_path):
    """
    Hybrid reconstruction: Keep dimensions from original, replace geometry from JSON
    CRITICAL: Use R2018 format with MM units for AutoCAD compatibility
    """
    print(f"🔨 Hybrid Reconstruction with R2018 + MM units")
    print(f"   Original DXF: {original_dxf}")
    print(f"   JSON data: {json_path}")
    
    # Load JSON data
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    # Load original DXF
    print(f"\n📖 Loading original DXF...")
    original = ezdxf.readfile(original_dxf)
    print(f"   Original has {len(list(original.modelspace()))} entities")
    
    # Count entity types in original
    original_types = Counter(e.dxftype() for e in original.modelspace())
    print(f"   Entity types: {dict(original_types)}")
    
    # Create NEW document with R2018 format and MM units
    print(f"\n🆕 Creating new DXF with R2018 format and MM units...")
    doc = ezdxf.new(dxfversion='R2018', units=units.MM)
    
    print(f"   DXF Version: {doc.dxfversion}")
    print(f"   Units: MM")
    
    # Copy all structure from original (layers, blocks, styles, etc.)
    print(f"\n📋 Copying structure from original...")
    
    # Copy layers
    for layer in original.layers:
        if layer.dxf.name not in doc.layers:
            try:
                doc.layers.new(
                    name=layer.dxf.name,
                    dxfattribs={
                        'color': layer.dxf.color,
                        'linetype': layer.dxf.linetype,
                    }
                )
            except:
                pass
    
    # Copy linetypes
    for linetype in original.linetypes:
        if linetype.dxf.name not in doc.linetypes and linetype.dxf.name not in ['ByBlock', 'ByLayer', 'Continuous']:
            try:
                doc.linetypes.new(
                    name=linetype.dxf.name,
                    dxfattribs={'description': linetype.dxf.description}
                )
            except:
                pass
    
    # Copy text styles
    for style in original.styles:
        if style.dxf.name not in doc.styles:
            try:
                doc.styles.new(
                    name=style.dxf.name,
                    dxfattribs={
                        'font': style.dxf.font,
                        'width': style.dxf.width,
                    }
                )
            except:
                pass
    
    # Copy dimension styles
    for dimstyle in original.dimstyles:
        if dimstyle.dxf.name not in doc.dimstyles:
            try:
                doc.dimstyles.new(dimstyle.dxf.name)
            except:
                pass
    
    # Copy block definitions from original
    for block in original.blocks:
        if block.name not in doc.blocks and not block.name.startswith('*'):
            try:
                new_block = doc.blocks.new(name=block.name)
                # Copy all entities in the block
                for entity in block:
                    try:
                        new_block.add_foreign_entity(entity)
                    except:
                        pass
            except:
                pass
    
    print(f"   Copied {len(doc.layers)} layers")
    print(f"   Copied {len(doc.linetypes)} linetypes")
    print(f"   Copied {len(doc.blocks)} blocks")
    print(f"   Copied {len(doc.dimstyles)} dimension styles")
    
    # STEP 1: Copy ALL DIMENSION and ANNOTATION entities from original
    print(f"\n📐 Preserving dimensions and annotations from original...")
    msp = doc.modelspace()
    dimension_count = 0
    
    ANNOTATION_TYPES = ['DIMENSION', 'MULTILEADER', 'ARC_DIMENSION', 'LEADER']
    
    for entity in original.modelspace():
        if entity.dxftype() in ANNOTATION_TYPES:
            try:
                msp.add_foreign_entity(entity)
                dimension_count += 1
            except Exception as e:
                print(f"   Warning: Could not copy {entity.dxftype()}: {e}")
    
    print(f"   Preserved {dimension_count} annotation entities")
    
    # STEP 2: Add geometry entities from JSON
    print(f"\n🎨 Adding geometry from JSON...")
    geometry_count = 0
    
    for entity_data in json_data.get('modelspace', []):
        dxf_type = entity_data.get('dxf_type')
        
        # Skip annotation entities (already copied from original)
        if dxf_type in ANNOTATION_TYPES:
            continue
        
        # Add geometry entity
        if add_entity_from_json(msp, entity_data):
            geometry_count += 1
    
    print(f"   Added {geometry_count} geometry entities from JSON")
    
    # Set header variables for AutoCAD compatibility
    print(f"\n⚙️  Setting header variables...")
    doc.header['$INSUNITS'] = 4  # Millimeters
    doc.header['$MEASUREMENT'] = 1  # Metric
    doc.header['$LUNITS'] = 2  # Decimal units
    doc.header['$AUNITS'] = 0  # Decimal degrees
    
    # Audit
    print(f"\n🔍 Running audit...")
    try:
        auditor = doc.audit()
        if auditor.has_errors:
            print(f"   Found {len(auditor.errors)} errors")
        if auditor.has_fixes:
            print(f"   Applied {len(auditor.fixes)} fixes")
    except:
        pass
    
    # Save
    doc.saveas(output_path)
    
    # Verify
    print(f"\n✅ Saved: {output_path}")
    verify = ezdxf.readfile(output_path)
    final_count = len(list(verify.modelspace()))
    final_types = Counter(e.dxftype() for e in verify.modelspace())
    
    print(f"\n📊 Final Statistics:")
    print(f"   DXF Version: {verify.dxfversion}")
    print(f"   Units (INSUNITS): {verify.header.get('$INSUNITS')}")
    print(f"   Total entities: {final_count}")
    print(f"   Dimensions: {dimension_count}")
    print(f"   Geometry: {geometry_count}")
    print(f"   Entity types: {dict(final_types)}")
    
    return output_path


def add_entity_from_json(msp, entity_data):
    """Add geometry entity from JSON data"""
    dxf_type = entity_data['dxf_type']
    
    common_attribs = {
        'layer': entity_data.get('layer', '0'),
        'color': entity_data.get('color', 256),
        'linetype': entity_data.get('linetype', 'BYLAYER'),
    }
    
    try:
        if dxf_type == "LINE":
            msp.add_line(
                start=entity_data['start'],
                end=entity_data['end'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "LWPOLYLINE":
            polyline = msp.add_lwpolyline(
                points=entity_data['points'],
                dxfattribs=common_attribs
            )
            polyline.closed = entity_data.get('closed', False)
            return True
        
        elif dxf_type == "CIRCLE":
            msp.add_circle(
                center=entity_data['center'],
                radius=entity_data['radius'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "ARC":
            msp.add_arc(
                center=entity_data['center'],
                radius=entity_data['radius'],
                start_angle=entity_data['start_angle'],
                end_angle=entity_data['end_angle'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "ELLIPSE":
            msp.add_ellipse(
                center=entity_data['center'],
                major_axis=entity_data['major_axis'],
                ratio=entity_data['ratio'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "TEXT":
            msp.add_text(
                text=entity_data['text'],
                dxfattribs={
                    **common_attribs,
                    'insert': entity_data.get('insert', (0, 0, 0)),
                    'height': entity_data.get('height', 2.5),
                }
            )
            return True
        
        elif dxf_type == "MTEXT":
            msp.add_mtext(
                text=entity_data['text'],
                dxfattribs={
                    **common_attribs,
                    'insert': entity_data.get('insert', (0, 0, 0)),
                    'char_height': entity_data.get('char_height', 2.5),
                }
            )
            return True
        
        elif dxf_type == "INSERT":
            block_name = entity_data.get('name')
            if block_name:
                msp.add_blockref(
                    name=block_name,
                    insert=entity_data.get('insert', (0, 0, 0)),
                    dxfattribs={
                        **common_attribs,
                        'xscale': entity_data.get('xscale', 1),
                        'yscale': entity_data.get('yscale', 1),
                        'rotation': entity_data.get('rotation', 0),
                    }
                )
                return True
        
        elif dxf_type == "HATCH":
            hatch = msp.add_hatch(dxfattribs=common_attribs)
            # Add basic hatch paths
            for path_data in entity_data.get('paths', []):
                edges = path_data.get('edges', [])
                if edges:
                    edge_path = hatch.paths.add_edge_path()
                    for edge in edges:
                        if edge.get('type') == 'LineEdge':
                            edge_path.add_line(edge['start'], edge['end'])
            if entity_data.get('solid_fill'):
                hatch.set_solid_fill()
            return True
        
        elif dxf_type == "SOLID":
            points = entity_data.get('points', [])
            if len(points) >= 3:
                msp.add_solid(points=points, dxfattribs=common_attribs)
                return True
        
        return False
        
    except Exception as e:
        return False


if __name__ == "__main__":
    original_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf"
    json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FULL.json"
    output_file = "ATTA-R2018-MM-HYBRID.dxf"
    
    hybrid_reconstruction_r2018_mm(original_file, json_file, output_file)
