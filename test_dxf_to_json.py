import ezdxf
import json
import math


def get_entity_bounds(entity):
    try:
        dxf_type = entity.dxftype()

        if dxf_type == "LINE":
            start, end = entity.dxf.start, entity.dxf.end
            return [start[:2], end[:2]]

        elif dxf_type == "LWPOLYLINE":
            return [list(p)[:2] for p in entity.get_points()]

        elif dxf_type == "POLYLINE":
            return [list(vertex.dxf.location)[:2] for vertex in entity.vertices()]

    except Exception:
        pass
    return []


def get_block_geometry(block, doc, depth=0):
    polygons = []
    if depth > 10:
        return polygons

    for entity in block:
        if entity.dxftype() == "INSERT":
            try:
                nested_block = doc.blocks[entity.dxf.name]
                polygons += get_block_geometry(nested_block, doc, depth + 1)
            except KeyError:
                continue
        else:
            poly = get_entity_bounds(entity)
            if poly:
                polygons.append(poly)

    return polygons


def get_block_area(block, doc):
    try:
        bounds = []
        for entity in block:
            b = get_entity_bounds(entity)
            if isinstance(b, list) and len(b) == 2:
                bounds.append(b)

        if bounds:
            xs = [p[0] for pair in bounds for p in pair]
            ys = [p[1] for pair in bounds for p in pair]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            return width * height
    except:
        pass
    return 0


# === MAIN SCRIPT ===

try:
    path = "ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE.dxf"
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    insert_entities = [e for e in msp if e.dxftype() == "INSERT"]

    blocks_with_area = []
    for e in insert_entities:
        try:
            bname = e.dxf.name
            block = doc.blocks[bname]
            area = get_block_area(block, doc)
            blocks_with_area.append((area, e))
        except:
            continue

    blocks_with_area.sort(reverse=True, key=lambda x: x[0])
    floor_entity = blocks_with_area[0][1] if blocks_with_area else None

    output = {
        "floorplan": {},
        "fixtures": []
    }

    for entity in insert_entities:
        bname = entity.dxf.name
        position = entity.dxf.insert
        angle = round(getattr(entity.dxf, 'rotation', 0), 2)
        scale_x = abs(getattr(entity.dxf, 'xscale', 1.0))
        scale_y = abs(getattr(entity.dxf, 'yscale', 1.0))

        block = doc.blocks.get(bname, None)
        geometry = get_block_geometry(block, doc) if block else []

        data = {
            "type": bname.lower(),
            "x": round(position.x, 2),
            "y": round(position.y, 2),
            "angle": angle,
            "scale": [scale_x, scale_y],
            "geometry": geometry
        }

        if entity == floor_entity:
            output["floorplan"] = data
        else:
            output["fixtures"].append(data)

    outname = path.replace(".dxf", ".json")
    with open(outname, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Exported: {outname}")

except Exception as e:
    print(f"❌ Error: {e}")
