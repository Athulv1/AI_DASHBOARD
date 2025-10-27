"""
AutoCAD 2026 Compatible DXF Reconstructor
This script reads the JSON file and creates a DXF that should open in AutoCAD 2026
"""
import ezdxf
import json
import os


def json_to_autocad_dxf(json_path, output_dxf_path):
    """Reconstruct DXF with full AutoCAD 2026 compatibility"""
    print(f"📄 Reading JSON: {json_path}")
    
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    print(f"🔨 Rebuilding DXF for AutoCAD 2026...")
    
    # Use the EXACT same DXF version from original
    dxf_version = json_data.get('dxf_version', 'AC1032')
    print(f"   DXF Version: {dxf_version} (AutoCAD 2018+)")
    
    # Create document
    doc = ezdxf.new(dxf_version)
    msp = doc.modelspace()
    
    print(f"   Creating {len(json_data.get('layers', []))} layers...")
    # Recreate layers
    for layer_data in json_data.get('layers', []):
        layer_name = layer_data['name']
        if layer_name not in ['0', 'Defpoints'] and layer_name not in doc.layers:
            try:
                doc.layers.new(
                    name=layer_name,
                    dxfattribs={
                        'color': layer_data['color'],
                        'linetype': layer_data.get('linetype', 'Continuous'),
                    }
                )
            except Exception as e:
                pass  # Skip if layer exists
    
    print(f"   Creating {len(json_data.get('blocks', {}))} blocks...")
    # Recreate block definitions
    for block_name, block_data in json_data.get('blocks', {}).items():
        if block_name not in doc.blocks:
            try:
                block = doc.blocks.new(name=block_name)
                
                # Add entities to block
                for entity_data in block_data['entities']:
                    add_entity_to_container(block, entity_data)
            except Exception as e:
                print(f"   Warning: Could not create block '{block_name}': {e}")
    
    print(f"   Adding {len(json_data.get('modelspace', []))} entities to modelspace...")
    # Recreate modelspace entities
    for entity_data in json_data.get('modelspace', []):
        add_entity_to_container(msp, entity_data)
    
    # Set header variables for AutoCAD compatibility
    doc.header['$INSUNITS'] = 4  # Millimeters
    doc.header['$MEASUREMENT'] = 1  # Metric
    doc.header['$ACADVER'] = dxf_version
    
    # Audit and fix
    print(f"   Running audit and fixes...")
    try:
        auditor = doc.audit()
        if auditor.has_errors:
            print(f"   ⚠️  Found {len(auditor.errors)} errors - attempting fixes...")
        if auditor.has_fixes:
            print(f"   ✓ Applied {len(auditor.fixes)} automatic fixes")
    except Exception as e:
        print(f"   Warning during audit: {e}")
    
    # Save file
    doc.saveas(output_dxf_path)
    
    # Verify file was created
    file_size = os.path.getsize(output_dxf_path)
    print(f"\n✅ DXF file created successfully!")
    print(f"   File: {output_dxf_path}")
    print(f"   Size: {file_size / 1024:.1f} KB")
    
    return output_dxf_path


def add_entity_to_container(container, entity_data):
    """Add a single entity to a container (modelspace or block)"""
    dxf_type = entity_data.get('dxf_type')
    if not dxf_type:
        return
    
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
        pass  # Silently skip problematic entities


# === MAIN SCRIPT ===

if __name__ == "__main__":
    print("="*70)
    print(" AutoCAD 2026 Compatible DXF Reconstruction")
    print("="*70)
    
    try:
        # Reconstruct DXF from the JSON file
        json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FULL.json"
        output_dxf = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-AUTOCAD2026.dxf"
        
        json_to_autocad_dxf(json_file, output_dxf)
        
        print("\n" + "="*70)
        print("📌 TROUBLESHOOTING TIPS FOR AUTOCAD 2026:")
        print("="*70)
        print("If the file still won't open in AutoCAD 2026:")
        print("")
        print("1. Use RECOVER command:")
        print("   - In AutoCAD, type: RECOVER")
        print("   - Browse to the reconstructed DXF file")
        print("")
        print("2. Use DXFIN command:")
        print("   - Create new drawing in AutoCAD")
        print("   - Type: DXFIN")
        print("   - Select the reconstructed DXF")
        print("")
        print("3. Try importing as a block:")
        print("   - Type: INSERT")
        print("   - Browse to DXF file")
        print("")
        print("4. Convert to DWG first:")
        print("   - Use online converter or DWG TrueView")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
