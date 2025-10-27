"""
CRITICAL FIX: Serialize and Reconstruct DIMENSION entities
This is why AutoCAD won't open - dimensions are missing!
"""
import ezdxf
import json


def serialize_dimension_complete(entity):
    """Completely serialize a DIMENSION entity with all properties"""
    data = {
        'dxf_type': 'DIMENSION',
        'layer': entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0',
        'color': entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
    }
    
    # Get all DXF attributes
    dxf_attribs = {}
    for attr in dir(entity.dxf):
        if not attr.startswith('_'):
            try:
                value = getattr(entity.dxf, attr)
                # Convert vectors to lists
                if hasattr(value, 'x') and hasattr(value, 'y'):
                    dxf_attribs[attr] = [value.x, value.y, value.z if hasattr(value, 'z') else 0]
                elif isinstance(value, (int, float, str, bool)):
                    dxf_attribs[attr] = value
            except:
                pass
    
    data['dxf_attribs'] = dxf_attribs
    data['dim_type'] = entity.dimtype
    
    return data


def serialize_multileader_complete(entity):
    """Serialize MULTILEADER entity"""
    data = {
        'dxf_type': 'MULTILEADER',
        'layer': entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0',
        'color': entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
    }
    
    # Get DXF attributes
    dxf_attribs = {}
    for attr in dir(entity.dxf):
        if not attr.startswith('_'):
            try:
                value = getattr(entity.dxf, attr)
                if hasattr(value, 'x') and hasattr(value, 'y'):
                    dxf_attribs[attr] = [value.x, value.y, value.z if hasattr(value, 'z') else 0]
                elif isinstance(value, (int, float, str, bool)):
                    dxf_attribs[attr] = value
            except:
                pass
    
    data['dxf_attribs'] = dxf_attribs
    
    return data


print("="*70)
print("EXPORTING DIMENSIONS AND MULTILEADERS TO JSON")
print("="*70)

# Read original
doc = ezdxf.readfile('ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf')
msp = doc.modelspace()

dimensions = []
multileaders = []

for entity in msp:
    if entity.dxftype() == 'DIMENSION':
        dimensions.append(serialize_dimension_complete(entity))
    elif entity.dxftype() == 'MULTILEADER':
        multileaders.append(serialize_multileader_complete(entity))
    elif entity.dxftype() == 'ARC_DIMENSION':
        # Treat as regular dimension
        dimensions.append(serialize_dimension_complete(entity))

output = {
    'dimensions': dimensions,
    'multileaders': multileaders
}

# Save to file
with open('DIMENSIONS_AND_LEADERS.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Exported:")
print(f"   Dimensions: {len(dimensions)}")
print(f"   Multileaders: {len(multileaders)}")
print(f"   File: DIMENSIONS_AND_LEADERS.json")

# Now show a sample
if dimensions:
    print(f"\n📋 Sample Dimension attributes:")
    sample = dimensions[0]
    print(f"   Type: {sample.get('dim_type')}")
    print(f"   Layer: {sample.get('layer')}")
    print(f"   Attributes: {list(sample.get('dxf_attribs', {}).keys())[:10]}")

print("\n" + "="*70)
