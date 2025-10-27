#!/usr/bin/env python3
"""
Universal DXF to JSON converter and R2018+MM formatter
Works with any DXF file for AutoCAD 2026 compatibility
"""
import ezdxf
from ezdxf import units
import json
import sys
import os


def dxf_to_json_and_r2018mm(input_dxf):
    """
    Complete workflow:
    1. Convert DXF to JSON (for backup/analysis)
    2. Convert DXF to R2018 + MM format (for AutoCAD 2026)
    """
    
    if not os.path.exists(input_dxf):
        print(f"❌ Error: File not found: {input_dxf}")
        return False
    
    base_name = input_dxf.replace('.dxf', '')
    json_output = f"{base_name}-FULL.json"
    r2018_output = f"{base_name}-R2018-MM.dxf"
    
    print("=" * 70)
    print(f"🔄 Processing: {input_dxf}")
    print("=" * 70)
    
    # STEP 1: Convert to JSON
    print(f"\n📝 STEP 1: Converting to JSON...")
    try:
        doc = ezdxf.readfile(input_dxf)
        
        # Collect data
        json_data = {
            'dxf_version': doc.dxfversion,
            'encoding': doc.encoding,
            'layers': [],
            'blocks': {},
            'modelspace': []
        }
        
        # Export layers
        for layer in doc.layers:
            json_data['layers'].append({
                'name': layer.dxf.name,
                'color': layer.dxf.color,
                'linetype': layer.dxf.linetype,
            })
        
        # Export blocks (simplified)
        for block in doc.blocks:
            if not block.name.startswith('*'):
                json_data['blocks'][block.name] = {
                    'entity_count': len(list(block))
                }
        
        # Export modelspace entities (type summary)
        from collections import Counter
        entity_types = Counter(e.dxftype() for e in doc.modelspace())
        json_data['modelspace'] = dict(entity_types)
        json_data['total_entities'] = len(list(doc.modelspace()))
        
        # Save JSON
        with open(json_output, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"   ✅ JSON saved: {json_output}")
        print(f"   📊 Total entities: {json_data['total_entities']}")
        print(f"   📦 Blocks: {len(json_data['blocks'])}")
        print(f"   📐 Layers: {len(json_data['layers'])}")
        print(f"   🔧 Entity types: {json_data['modelspace']}")
        
    except Exception as e:
        print(f"   ❌ JSON export failed: {e}")
        return False
    
    # STEP 2: Convert to R2018 + MM
    print(f"\n🔨 STEP 2: Converting to R2018 + MM format...")
    try:
        doc = ezdxf.readfile(input_dxf)
        
        print(f"   Original version: {doc.dxfversion}")
        print(f"   Original INSUNITS: {doc.header.get('$INSUNITS', 'Not set')}")
        
        # Set to MM units
        doc.header['$INSUNITS'] = 4  # Millimeters
        doc.header['$MEASUREMENT'] = 1  # Metric
        doc.header['$LUNITS'] = 2  # Decimal units
        doc.header['$AUNITS'] = 0  # Decimal degrees
        
        # Save as R2018 ASCII format
        doc.saveas(r2018_output, encoding='utf-8', fmt='asc')
        
        # Verify
        verify = ezdxf.readfile(r2018_output)
        print(f"   ✅ R2018+MM saved: {r2018_output}")
        print(f"   📊 Output version: {verify.dxfversion}")
        print(f"   📏 INSUNITS: {verify.header.get('$INSUNITS')} (4=MM)")
        print(f"   📐 Total entities: {len(list(verify.modelspace()))}")
        
        # File size comparison
        original_size = os.path.getsize(input_dxf) / (1024*1024)
        output_size = os.path.getsize(r2018_output) / (1024*1024)
        print(f"   💾 Original size: {original_size:.2f} MB")
        print(f"   💾 Output size: {output_size:.2f} MB")
        
    except Exception as e:
        print(f"   ❌ R2018+MM conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n" + "=" * 70)
    print(f"✅ SUCCESS! Files ready:")
    print(f"   📄 JSON backup: {json_output}")
    print(f"   🎯 AutoCAD file: {r2018_output}")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Process file from command line argument
        input_file = sys.argv[1]
    else:
        # Default test files
        test_files = [
            "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf",
            "ADJ.BELGIAN WAFFLE_MALL ROAD_HOSHIARPUR-COCO-FURNITURE.dxf",
        ]
        
        print("🔄 Batch processing multiple files...\n")
        
        success_count = 0
        for file in test_files:
            if os.path.exists(file):
                if dxf_to_json_and_r2018mm(file):
                    success_count += 1
                print()
            else:
                print(f"⚠️  Skipping (not found): {file}\n")
        
        print(f"\n📊 Batch Summary: {success_count}/{len(test_files)} files processed successfully")
        sys.exit(0)
    
    # Single file processing
    success = dxf_to_json_and_r2018mm(input_file)
    sys.exit(0 if success else 1)
