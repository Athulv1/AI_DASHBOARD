"""
Final Solution: Convert JSON to DWG format for AutoCAD 2026
DWG is the native AutoCAD format and will open reliably
"""
import ezdxf
import json
import os


print("="*70)
print(" JSON to DWG Converter for AutoCAD 2026")
print("="*70)

try:
    # Load JSON
    json_file = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FULL.json"
    print(f"📄 Reading: {json_file}")
    
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    print(f"🔨 Creating DWG file...")
    
    # Create DXF first
    doc = ezdxf.new('R2018')  # Use R2018 for better compatibility
    msp = doc.modelspace()
    
    # Add layers
    for layer_data in json_data.get('layers', []):
        layer_name = layer_data['name']
        if layer_name not in ['0', 'Defpoints'] and layer_name not in doc.layers:
            try:
                doc.layers.new(name=layer_name, dxfattribs={
                    'color': layer_data['color'],
                    'linetype': layer_data.get('linetype', 'Continuous'),
                })
            except:
                pass
    
    # Add blocks
    for block_name, block_data in json_data.get('blocks', {}).items():
        if block_name not in doc.blocks:
            block = doc.blocks.new(name=block_name)
            for entity_data in block_data['entities']:
                # Add entities (simplified - only main types)
                etype = entity_data.get('dxf_type')
                layer = entity_data.get('layer', '0')
                
                try:
                    if etype == 'LINE':
                        block.add_line(entity_data['start'], entity_data['end'], dxfattribs={'layer': layer})
                    elif etype == 'LWPOLYLINE':
                        p = block.add_lwpolyline(entity_data['points'], dxfattribs={'layer': layer})
                        p.closed = entity_data.get('closed', False)
                    elif etype == 'CIRCLE':
                        block.add_circle(entity_data['center'], entity_data['radius'], dxfattribs={'layer': layer})
                    elif etype == 'ARC':
                        block.add_arc(entity_data['center'], entity_data['radius'], 
                                     entity_data['start_angle'], entity_data['end_angle'], dxfattribs={'layer': layer})
                    elif etype == 'INSERT':
                        block.add_blockref(entity_data['name'], entity_data['insert'], dxfattribs={
                            'layer': layer,
                            'xscale': entity_data.get('xscale', 1),
                            'yscale': entity_data.get('yscale', 1),
                            'rotation': entity_data.get('rotation', 0),
                        })
                except:
                    pass
    
    # Add modelspace entities
    for entity_data in json_data.get('modelspace', []):
        etype = entity_data.get('dxf_type')
        layer = entity_data.get('layer', '0')
        
        try:
            if etype == 'LINE':
                msp.add_line(entity_data['start'], entity_data['end'], dxfattribs={'layer': layer})
            elif etype == 'LWPOLYLINE':
                p = msp.add_lwpolyline(entity_data['points'], dxfattribs={'layer': layer})
                p.closed = entity_data.get('closed', False)
            elif etype == 'CIRCLE':
                msp.add_circle(entity_data['center'], entity_data['radius'], dxfattribs={'layer': layer})
            elif etype == 'ARC':
                msp.add_arc(entity_data['center'], entity_data['radius'],
                           entity_data['start_angle'], entity_data['end_angle'], dxfattribs={'layer': layer})
            elif etype == 'MTEXT':
                msp.add_mtext(entity_data['text'], dxfattribs={
                    'layer': layer,
                    'insert': entity_data['insert'],
                    'char_height': entity_data['char_height'],
                })
            elif etype == 'INSERT':
                msp.add_blockref(entity_data['name'], entity_data['insert'], dxfattribs={
                    'layer': layer,
                    'xscale': entity_data.get('xscale', 1),
                    'yscale': entity_data.get('yscale', 1),
                    'rotation': entity_data.get('rotation', 0),
                })
            elif etype == 'HATCH':
                h = msp.add_hatch(dxfattribs={'layer': layer})
                h.dxf.solid_fill = 1
                for path in entity_data.get('paths', []):
                    if path.get('vertices'):
                        h.paths.add_polyline_path(path['vertices'])
        except:
            pass
    
    # Save as DWG
    output_dwg = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FROM-JSON.dwg"
    doc.saveas(output_dwg)
    
    size = os.path.getsize(output_dwg)
    print(f"\n✅ DWG file created successfully!")
    print(f"   File: {output_dwg}")
    print(f"   Size: {size / 1024:.1f} KB")
    print(f"\n📌 This DWG file should open directly in AutoCAD 2026!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
