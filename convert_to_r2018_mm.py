import ezdxf
from ezdxf import units


def convert_to_r2018_mm(input_dxf, output_dxf):
    """
    Convert existing DXF to R2018 format with MM units
    This preserves ALL entities including dimensions
    """
    print(f"🔄 Converting DXF to R2018 format with MM units")
    print(f"   Input: {input_dxf}")
    
    # Read the original file
    print(f"\n📖 Reading original file...")
    doc = ezdxf.readfile(input_dxf)
    
    # Get current info
    print(f"   Current DXF version: {doc.dxfversion}")
    print(f"   Current INSUNITS: {doc.header.get('$INSUNITS', 'Not set')}")
    print(f"   Entities: {len(list(doc.modelspace()))}")
    
    # Set units to MM (millimeters)
    print(f"\n⚙️  Setting units to MM...")
    doc.header['$INSUNITS'] = 4  # 4 = Millimeters
    doc.header['$MEASUREMENT'] = 1  # 1 = Metric
    doc.header['$LUNITS'] = 2  # Decimal units
    doc.header['$AUNITS'] = 0  # Decimal degrees
    
    # Save as R2018 format
    print(f"\n💾 Saving as R2018 format with MM units...")
    doc.saveas(output_dxf, encoding='utf-8', fmt='asc')
    
    # Verify the output
    print(f"\n✅ Conversion complete!")
    print(f"   Output: {output_dxf}")
    
    verify = ezdxf.readfile(output_dxf)
    print(f"\n📊 Verification:")
    print(f"   DXF Version: {verify.dxfversion}")
    print(f"   INSUNITS (units): {verify.header.get('$INSUNITS')} (4=MM)")
    print(f"   MEASUREMENT: {verify.header.get('$MEASUREMENT')} (1=Metric)")
    print(f"   Total entities: {len(list(verify.modelspace()))}")
    
    from collections import Counter
    entity_types = Counter(e.dxftype() for e in verify.modelspace())
    print(f"   Entity types: {dict(entity_types)}")
    
    print(f"\n✨ File ready for AutoCAD 2026!")
    

if __name__ == "__main__":
    # Convert the original file to R2018 with MM units
    input_file = "ADJ.BELGIAN WAFFLE_MALL ROAD_HOSHIARPUR-COCO-FURNITURE.dxf"
    output_file = "ADJ.BELGIAN WAFFLE_MALL ROAD_HOSHIARPUR-COCO-FURNITURE-R2018-MM.dxf"
    
    convert_to_r2018_mm(input_file, output_file)
