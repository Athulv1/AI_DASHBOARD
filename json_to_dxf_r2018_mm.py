import ezdxf
from ezdxf import units
import json


def json_to_dxf(json_path, output_dxf_path):
    """Reconstruct DXF from JSON with R2018 format and MM units for AutoCAD compatibility"""
    print(f"📄 Reading JSON: {json_path}")
    
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    print(f"🔨 Rebuilding DXF with R2018 format and MM units...")
    
    # CRITICAL: Create new DXF document with R2018 version and MM units
    doc = ezdxf.new(dxfversion='R2018', units=units.MM)
    
    print(f"   DXF Version: {doc.dxfversion}")
    print(f"   Units: MM (Millimeters)")
    
    msp = doc.modelspace()
    
    # Recreate layers
    print(f"   Creating {len(json_data.get('layers', []))} layers...")
    for layer_data in json_data.get('layers', []):
        layer_name = layer_data['name']
        # Skip default layers that already exist
        if layer_name not in ['0', 'Defpoints'] and layer_name not in doc.layers:
            try:
                doc.layers.new(
                    name=layer_name,
                    dxfattribs={
                        'color': layer_data['color'],
                        'linetype': layer_data['linetype'],
                    }
                )
            except Exception as e:
                print(f"      Warning: Could not create layer '{layer_name}': {e}")
    
    # Recreate block definitions
    blocks = json_data.get('blocks', {})
    print(f"   Creating {len(blocks)} blocks...")
    for block_name, block_data in blocks.items():
        if block_name not in doc.blocks:
            block = doc.blocks.new(name=block_name)
            
            # Add entities to block
            for entity_data in block_data['entities']:
                add_entity_to_container(block, entity_data)
    
    # Recreate modelspace entities
    modelspace_entities = json_data.get('modelspace', [])
    print(f"   Adding {len(modelspace_entities)} entities to modelspace...")
    entity_count = 0
    for entity_data in modelspace_entities:
        if add_entity_to_container(msp, entity_data):
            entity_count += 1
    
    print(f"   Successfully added {entity_count} entities")
    
    # Set header variables for AutoCAD compatibility
    doc.header['$INSUNITS'] = 4  # Millimeters
    doc.header['$MEASUREMENT'] = 1  # Metric
    doc.header['$LUNITS'] = 2  # Decimal units
    doc.header['$AUNITS'] = 0  # Decimal degrees
    
    # Audit and fix any issues before saving
    print(f"   Running audit...")
    try:
        auditor = doc.audit()
        if auditor.has_errors:
            print(f"      Warning: Found {len(auditor.errors)} errors")
            for error in auditor.errors[:5]:  # Show first 5 errors
                print(f"         - {error}")
        if auditor.has_fixes:
            print(f"      Applied {len(auditor.fixes)} fixes")
    except Exception as e:
        print(f"      Audit skipped: {e}")
    
    # Save as R2018 DXF with MM units
    doc.saveas(output_dxf_path)
    print(f"✅ Saved DXF: {output_dxf_path}")
    print(f"   Format: R2018, Units: MM")


def add_entity_to_container(container, entity_data):
    """Add a single entity to a container (modelspace or block)"""
    dxf_type = entity_data['dxf_type']
    
    common_attribs = {
        'layer': entity_data.get('layer', '0'),
        'color': entity_data.get('color', 256),
        'linetype': entity_data.get('linetype', 'BYLAYER'),
    }
    
    try:
        if dxf_type == "LINE":
            container.add_line(
                start=entity_data['start'],
                end=entity_data['end'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "LWPOLYLINE":
            polyline = container.add_lwpolyline(
                points=entity_data['points'],
                dxfattribs=common_attribs
            )
            polyline.closed = entity_data.get('closed', False)
            if 'width' in entity_data:
                polyline.dxf.const_width = entity_data['width']
            return True
        
        elif dxf_type == "POLYLINE":
            polyline = container.add_polyline3d(
                points=entity_data['points'],
                dxfattribs=common_attribs
            )
            polyline.closed = entity_data.get('closed', False)
            return True
        
        elif dxf_type == "CIRCLE":
            container.add_circle(
                center=entity_data['center'],
                radius=entity_data['radius'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "ARC":
            container.add_arc(
                center=entity_data['center'],
                radius=entity_data['radius'],
                start_angle=entity_data['start_angle'],
                end_angle=entity_data['end_angle'],
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "ELLIPSE":
            container.add_ellipse(
                center=entity_data['center'],
                major_axis=entity_data['major_axis'],
                ratio=entity_data['ratio'],
                start_param=entity_data.get('start_param', 0),
                end_param=entity_data.get('end_param', 6.283185307179586),
                dxfattribs=common_attribs
            )
            return True
        
        elif dxf_type == "SPLINE":
            control_points = entity_data.get('control_points', [])
            if control_points:
                container.add_spline(
                    control_points=control_points,
                    degree=entity_data.get('degree', 3),
                    dxfattribs=common_attribs
                )
                return True
        
        elif dxf_type == "TEXT":
            container.add_text(
                text=entity_data['text'],
                dxfattribs={
                    **common_attribs,
                    'insert': entity_data.get('insert', (0, 0, 0)),
                    'height': entity_data.get('height', 2.5),
                    'rotation': entity_data.get('rotation', 0),
                    'style': entity_data.get('style', 'Standard'),
                }
            )
            return True
        
        elif dxf_type == "MTEXT":
            container.add_mtext(
                text=entity_data['text'],
                dxfattribs={
                    **common_attribs,
                    'insert': entity_data.get('insert', (0, 0, 0)),
                    'char_height': entity_data.get('char_height', 2.5),
                    'width': entity_data.get('width', 0),
                    'attachment_point': entity_data.get('attachment_point', 1),
                    'style': entity_data.get('style', 'Standard'),
                }
            )
            return True
        
        elif dxf_type == "INSERT":
            # Block reference
            block_name = entity_data.get('name')
            if block_name:
                insert_attribs = {
                    **common_attribs,
                    'insert': entity_data.get('insert', (0, 0, 0)),
                }
                if 'xscale' in entity_data:
                    insert_attribs['xscale'] = entity_data['xscale']
                if 'yscale' in entity_data:
                    insert_attribs['yscale'] = entity_data['yscale']
                if 'zscale' in entity_data:
                    insert_attribs['zscale'] = entity_data['zscale']
                if 'rotation' in entity_data:
                    insert_attribs['rotation'] = entity_data['rotation']
                
                container.add_blockref(
                    name=block_name,
                    insert=insert_attribs['insert'],
                    dxfattribs=insert_attribs
                )
                return True
        
        elif dxf_type == "HATCH":
            # Create hatch entity
            hatch = container.add_hatch(
                color=entity_data.get('color', 256),
                dxfattribs=common_attribs
            )
            
            # Add paths (boundary edges)
            for path_data in entity_data.get('paths', []):
                path_type = path_data.get('type', 0)
                edges = path_data.get('edges', [])
                
                if edges:
                    edge_path = hatch.paths.add_edge_path()
                    for edge in edges:
                        edge_type = edge.get('type')
                        if edge_type == 'LineEdge':
                            edge_path.add_line(edge['start'], edge['end'])
                        elif edge_type == 'ArcEdge':
                            edge_path.add_arc(
                                center=edge['center'],
                                radius=edge['radius'],
                                start_angle=edge['start_angle'],
                                end_angle=edge['end_angle'],
                                ccw=edge.get('ccw', True)
                            )
                        elif edge_type == 'EllipseEdge':
                            edge_path.add_ellipse(
                                center=edge['center'],
                                major_axis=edge['major_axis'],
                                ratio=edge['ratio'],
                                start_angle=edge['start_angle'],
                                end_angle=edge['end_angle'],
                                ccw=edge.get('ccw', True)
                            )
                        elif edge_type == 'SplineEdge':
                            edge_path.add_spline(
                                fit_points=edge.get('fit_points', []),
                                control_points=edge.get('control_points', []),
                                knot_values=edge.get('knot_values', []),
                                weights=edge.get('weights', []),
                                degree=edge.get('degree', 3)
                            )
            
            # Set pattern
            if 'pattern' in entity_data:
                pattern = entity_data['pattern']
                if pattern.get('name'):
                    hatch.set_pattern_fill(
                        name=pattern['name'],
                        scale=pattern.get('scale', 1.0),
                        angle=pattern.get('angle', 0.0)
                    )
            elif 'solid_fill' in entity_data and entity_data['solid_fill']:
                hatch.set_solid_fill()
            
            return True
        
        elif dxf_type == "SOLID":
            points = entity_data.get('points', [])
            if len(points) >= 3:
                container.add_solid(
                    points=points,
                    dxfattribs=common_attribs
                )
                return True
        
        elif dxf_type in ["DIMENSION", "MULTILEADER", "ARC_DIMENSION"]:
            # Skip complex annotation entities - these are better preserved from original
            return False
        
        else:
            print(f"      Warning: Unsupported entity type: {dxf_type}")
            return False
            
    except Exception as e:
        print(f"      Error adding {dxf_type}: {str(e)[:100]}")
        return False


if __name__ == "__main__":
    json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FULL.json"
    output_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-R2018-MM.dxf"
    
    json_to_dxf(json_file, output_file)
    
    # Verify the output
    print("\n🔍 Verifying output file...")
    try:
        verify = ezdxf.readfile(output_file)
        print(f"   DXF Version: {verify.dxfversion}")
        print(f"   Units (INSUNITS): {verify.header.get('$INSUNITS', 'Not set')}")
        print(f"   Measurement: {verify.header.get('$MEASUREMENT', 'Not set')}")
        
        entity_count = len(list(verify.modelspace()))
        print(f"   Modelspace entities: {entity_count}")
        print(f"   Blocks: {len(verify.blocks)}")
        print(f"   Layers: {len(verify.layers)}")
    except Exception as e:
        print(f"   Error verifying: {e}")
