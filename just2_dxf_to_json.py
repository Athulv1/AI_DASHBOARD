import ezdxf
import json
import math


def v2(vec):
    return (vec.x, vec.y)


def get_entity_bounds(entity):
    try:
        dxf_type = entity.dxftype()

        if dxf_type == "LINE":
            start, end = v2(entity.dxf.start), v2(entity.dxf.end)
            return [start, end]

        elif dxf_type == "LWPOLYLINE":
            return [v2(p[0]) for p in entity.get_points()]

        elif dxf_type == "POLYLINE":
            return [v2(vertex.dxf.location) for vertex in entity.vertices()]

    except Exception:
        pass
    return []


def transform(points, insert):
    """Apply INSERT translation, rotation, scale to a list of (x, y) points"""
    try:
        dx, dy = insert.dxf.insert.x, insert.dxf.insert.y
        angle = math.radians(getattr(insert.dxf, 'rotation', 0))
        scale_x = abs(getattr(insert.dxf, 'xscale', 1.0))
        scale_y = abs(getattr(insert.dxf, 'yscale', 1.0))

        cos_a, sin_a = math.cos(angle), math.sin(angle)

        transformed = []
        for x, y in points:
            x *= scale_x
            y *= scale_y
            x_rot = x * cos_a - y * sin_a
            y_rot = x * sin_a + y * cos_a
            transformed.append([x_rot + dx, y_rot + dy])
        return transformed
    except:
        return points


def get_block_geometry(block, doc, insert_ctx=None, depth=0):
    polygons = []
    if depth > 10:
        return polygons

    for entity in block:
        if entity.dxftype() == "INSERT":
            try:
                nested_block = doc.blocks[entity.dxf.name]
                nested_polys = get_block_geometry(nested_block, doc, entity, depth + 1)
                polygons.extend(nested_polys)
            except KeyError:
                continue
        else:
            poly = get_entity_bounds(entity)
            if poly:
                if insert_ctx:
                    poly = transform(poly, insert_ctx)
                polygons.append(poly)

    return polygons


def get_block_area(block, doc):
    try:
        points = []
        for entity in block:
            poly = get_entity_bounds(entity)
            if poly:
                points.extend(poly)
        if not points:
            return 0
        xs, ys = zip(*points)
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        return width * height
    except:
        return 0


# === MAIN SCRIPT ===

try:
    path = "ADJ-BLUE BUDDHA_MI ROAD_JAIPUR-COCO.dxf"
    print(f"📄 Reading {path}")
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    insert_entities = [e for e in msp if e.dxftype() == "INSERT"]

    # Determine the largest block as floorplan
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
        geometry = get_block_geometry(block, doc, entity) if block else []

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
    print(f"Fixtures: {len(output['fixtures'])}")

except Exception as e:
    print(f"❌ Error: {e}")
