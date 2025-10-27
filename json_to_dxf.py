import ezdxf
import json


def json_to_dxf(json_path, output_dxf_path):
    """Reconstruct DXF from comprehensive JSON"""
    print(f"📄 Reading JSON: {json_path}")
    
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    print(f"🔨 Rebuilding DXF...")
    
    # Create new DXF document - use AC1032 or newer for AutoCAD 2018+
    dxf_version = json_data.get('dxf_version', 'R2018')
    print(f"   DXF Version: {dxf_version}")
    
    try:
        doc = ezdxf.new(dxf_version)
    except:
        # Fallback to R2018 if version not supported
        print(f"   Warning: Version {dxf_version} not supported, using R2018")
        doc = ezdxf.new('R2018')
    
    msp = doc.modelspace()
    
    # Recreate layers
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
                print(f"Warning: Could not create layer '{layer_name}': {e}")
    
    # Recreate block definitions
    for block_name, block_data in json_data.get('blocks', {}).items():
        if block_name not in doc.blocks:
            block = doc.blocks.new(name=block_name)
            
            # Add entities to block
            for entity_data in block_data['entities']:
                add_entity_to_container(block, entity_data)
    
    # Recreate modelspace entities
    for entity_data in json_data.get('modelspace', []):
        add_entity_to_container(msp, entity_data)
    
    # Set header variables for better AutoCAD compatibility
    doc.header['$INSUNITS'] = 4  # Millimeters
    doc.header['$MEASUREMENT'] = 1  # Metric
    
    # Audit and fix any issues before saving
    try:
        auditor = doc.audit()
        if auditor.has_errors:
            print(f"   Warning: Found {len(auditor.errors)} errors during audit")
        if auditor.has_fixes:
            print(f"   Info: Applied {len(auditor.fixes)} fixes")
    except:
        pass
    
    doc.saveas(output_dxf_path)
    print(f"✅ Rebuilt DXF: {output_dxf_path}")


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
        
        elif dxf_type == "LWPOLYLINE":
            polyline = container.add_lwpolyline(
                points=entity_data['points'],
                dxfattribs=common_attribs
            )
            polyline.closed = entity_data.get('closed', False)
        
        elif dxf_type == "POLYLINE":
            polyline = container.add_polyline3d(
                points=entity_data['points'],
                dxfattribs=common_attribs
            )
            if entity_data.get('closed', False):
                polyline.close()
        
        elif dxf_type == "CIRCLE":
            container.add_circle(
                center=entity_data['center'],
                radius=entity_data['radius'],
                dxfattribs=common_attribs
            )
        
        elif dxf_type == "ARC":
            container.add_arc(
                center=entity_data['center'],
                radius=entity_data['radius'],
                start_angle=entity_data['start_angle'],
                end_angle=entity_data['end_angle'],
                dxfattribs=common_attribs
            )
        
        elif dxf_type == "ELLIPSE":
            container.add_ellipse(
                center=entity_data['center'],
                major_axis=entity_data['major_axis'],
                ratio=entity_data['ratio'],
                start_param=entity_data.get('start_param', 0),
                end_param=entity_data.get('end_param', 6.283185307179586),
                dxfattribs=common_attribs
            )
        
        elif dxf_type == "SPLINE":
            spline = container.add_spline(
                dxfattribs=common_attribs
            )
            spline.fit_points = entity_data['control_points']
            spline.dxf.degree = entity_data.get('degree', 3)
            if entity_data.get('knots'):
                spline.knots = entity_data['knots']
        
        elif dxf_type == "TEXT":
            container.add_text(
                text=entity_data['text'],
                dxfattribs={
                    **common_attribs,
                    'insert': entity_data['insert'],
                    'height': entity_data['height'],
                    'rotation': entity_data.get('rotation', 0),
                    'style': entity_data.get('style', 'Standard'),
                }
            )
        
        elif dxf_type == "MTEXT":
            container.add_mtext(
                text=entity_data['text'],
                dxfattribs={
                    **common_attribs,
                    'insert': entity_data['insert'],
                    'char_height': entity_data['char_height'],
                    'width': entity_data.get('width', 0),
                    'rotation': entity_data.get('rotation', 0),
                }
            )
        
        elif dxf_type == "INSERT":
            container.add_blockref(
                name=entity_data['name'],
                insert=entity_data['insert'],
                dxfattribs={
                    **common_attribs,
                    'xscale': entity_data.get('xscale', 1.0),
                    'yscale': entity_data.get('yscale', 1.0),
                    'zscale': entity_data.get('zscale', 1.0),
                    'rotation': entity_data.get('rotation', 0),
                }
            )
    
    except Exception as e:
        print(f"Warning: Could not recreate {dxf_type}: {e}")


# === MAIN SCRIPT ===

if __name__ == "__main__":
    try:
        # Reconstruct DXF from the JSON file
        json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FULL.json"
        output_dxf = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-RECONSTRUCTED.dxf"
        
        json_to_dxf(json_file, output_dxf)
        
        print("\n" + "="*60)
        print("✅ RECONSTRUCTION COMPLETE!")
        print("="*60)
        print(f"Original DXF:      ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf")
        print(f"Reconstructed DXF: {output_dxf}")
        print("\n📌 If AutoCAD 2026 won't open the file, try:")
        print("   1. Right-click the DXF → Properties → Unblock")
        print("   2. Open with 'Recover' command in AutoCAD")
        print("   3. Check if file size is reasonable (not 0 bytes)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
