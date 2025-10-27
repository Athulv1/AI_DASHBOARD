#!/usr/bin/env python3
"""
DXF Fixture Extraction with Accurate Sizes and Line Length Calculation
=======================================================================

This script extracts all fixtures (block inserts) from a DXF file with:
- Accurate bounding box sizes (width x height)
- Precise X, Y coordinates
- All line entities within each block definition
- Total length calculation for all lines in each fixture

Output: JSON file with comprehensive fixture data
"""

import ezdxf
from ezdxf.math import Vec3
import json
import math
import sys


def calculate_line_length(start, end):
    """Calculate Euclidean distance between two points"""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = (end[2] - start[2]) if len(end) > 2 and len(start) > 2 else 0
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def calculate_polyline_length(points, closed=False):
    """Calculate total length of a polyline"""
    if len(points) < 2:
        return 0.0
    
    total_length = 0.0
    for i in range(len(points) - 1):
        total_length += calculate_line_length(points[i], points[i + 1])
    
    # If closed, add the closing segment
    if closed and len(points) > 2:
        total_length += calculate_line_length(points[-1], points[0])
    
    return total_length


def calculate_arc_length(radius, start_angle, end_angle):
    """Calculate arc length given radius and angles (in degrees)"""
    # Convert to radians
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # Calculate angle difference
    angle_diff = end_rad - start_rad
    
    # Normalize to 0-2π
    while angle_diff < 0:
        angle_diff += 2 * math.pi
    while angle_diff > 2 * math.pi:
        angle_diff -= 2 * math.pi
    
    return radius * angle_diff


def calculate_circle_circumference(radius):
    """Calculate circle circumference"""
    return 2 * math.pi * radius


def extract_block_lines_and_length(block):
    """
    Extract all line entities from a block and calculate total length
    
    Returns:
        dict with 'lines' (list of line data) and 'total_length' (float)
    """
    lines = []
    total_length = 0.0
    
    for entity in block:
        entity_type = entity.dxftype()
        
        if entity_type == "LINE":
            start = [entity.dxf.start.x, entity.dxf.start.y, entity.dxf.start.z]
            end = [entity.dxf.end.x, entity.dxf.end.y, entity.dxf.end.z]
            length = calculate_line_length(start, end)
            
            lines.append({
                'type': 'LINE',
                'start': start,
                'end': end,
                'length': round(length, 3),
                'layer': entity.dxf.layer
            })
            total_length += length
        
        elif entity_type == "LWPOLYLINE":
            points = [[p[0], p[1]] for p in entity.get_points('xy')]
            closed = entity.closed
            length = calculate_polyline_length(points, closed)
            
            lines.append({
                'type': 'LWPOLYLINE',
                'points': points,
                'closed': closed,
                'length': round(length, 3),
                'layer': entity.dxf.layer
            })
            total_length += length
        
        elif entity_type == "POLYLINE":
            points = [[v.dxf.location.x, v.dxf.location.y, v.dxf.location.z] 
                     for v in entity.vertices]
            closed = entity.is_closed
            length = calculate_polyline_length(points, closed)
            
            lines.append({
                'type': 'POLYLINE',
                'points': points,
                'closed': closed,
                'length': round(length, 3),
                'layer': entity.dxf.layer
            })
            total_length += length
        
        elif entity_type == "CIRCLE":
            center = [entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z]
            radius = entity.dxf.radius
            length = calculate_circle_circumference(radius)
            
            lines.append({
                'type': 'CIRCLE',
                'center': center,
                'radius': radius,
                'length': round(length, 3),
                'layer': entity.dxf.layer
            })
            total_length += length
        
        elif entity_type == "ARC":
            center = [entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z]
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            length = calculate_arc_length(radius, start_angle, end_angle)
            
            lines.append({
                'type': 'ARC',
                'center': center,
                'radius': radius,
                'start_angle': start_angle,
                'end_angle': end_angle,
                'length': round(length, 3),
                'layer': entity.dxf.layer
            })
            total_length += length
        
        elif entity_type == "ELLIPSE":
            # Approximate ellipse length (Ramanujan's approximation)
            major_axis = entity.dxf.major_axis
            ratio = entity.dxf.ratio
            
            # Calculate semi-major and semi-minor axes
            a = math.sqrt(major_axis.x**2 + major_axis.y**2 + major_axis.z**2)
            b = a * ratio
            
            # Ramanujan's approximation for ellipse perimeter
            h = ((a - b)**2) / ((a + b)**2)
            length = math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
            
            lines.append({
                'type': 'ELLIPSE',
                'center': [entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z],
                'major_axis': [major_axis.x, major_axis.y, major_axis.z],
                'ratio': ratio,
                'length': round(length, 3),
                'layer': entity.dxf.layer
            })
            total_length += length
        
        elif entity_type == "SPLINE":
            # Approximate spline length by sampling points
            try:
                # Get approximation points from spline
                approx_points = list(entity.flattening(0.01))  # 0.01mm tolerance
                if len(approx_points) > 1:
                    points_list = [[p.x, p.y, p.z] for p in approx_points]
                    length = calculate_polyline_length(points_list, False)
                    
                    lines.append({
                        'type': 'SPLINE',
                        'approximated_points': len(approx_points),
                        'length': round(length, 3),
                        'layer': entity.dxf.layer
                    })
                    total_length += length
            except Exception as e:
                print(f"    Warning: Could not calculate spline length: {e}")
    
    return {
        'lines': lines,
        'total_length': round(total_length, 3),
        'line_count': len(lines)
    }


def calculate_manual_bounding_box(block):
    """
    Manually calculate bounding box from block entities
    
    Returns:
        tuple: (min_point, max_point) or None if no geometry
    """
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    has_geometry = False
    
    for entity in block:
        entity_type = entity.dxftype()
        
        try:
            if entity_type == "LINE":
                for point in [entity.dxf.start, entity.dxf.end]:
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    min_z = min(min_z, point.z)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)
                    max_z = max(max_z, point.z)
                    has_geometry = True
            
            elif entity_type == "LWPOLYLINE":
                for point in entity.get_points('xy'):
                    min_x = min(min_x, point[0])
                    min_y = min(min_y, point[1])
                    max_x = max(max_x, point[0])
                    max_y = max(max_y, point[1])
                    has_geometry = True
            
            elif entity_type == "POLYLINE":
                for vertex in entity.vertices:
                    point = vertex.dxf.location
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    min_z = min(min_z, point.z)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)
                    max_z = max(max_z, point.z)
                    has_geometry = True
            
            elif entity_type == "CIRCLE":
                center = entity.dxf.center
                radius = entity.dxf.radius
                min_x = min(min_x, center.x - radius)
                min_y = min(min_y, center.y - radius)
                min_z = min(min_z, center.z)
                max_x = max(max_x, center.x + radius)
                max_y = max(max_y, center.y + radius)
                max_z = max(max_z, center.z)
                has_geometry = True
            
            elif entity_type == "ARC":
                center = entity.dxf.center
                radius = entity.dxf.radius
                # Simplified: use full circle bounds
                min_x = min(min_x, center.x - radius)
                min_y = min(min_y, center.y - radius)
                min_z = min(min_z, center.z)
                max_x = max(max_x, center.x + radius)
                max_y = max(max_y, center.y + radius)
                max_z = max(max_z, center.z)
                has_geometry = True
            
            elif entity_type == "ELLIPSE":
                center = entity.dxf.center
                major_axis = entity.dxf.major_axis
                a = math.sqrt(major_axis.x**2 + major_axis.y**2 + major_axis.z**2)
                b = a * entity.dxf.ratio
                # Simplified: use rectangular bounds
                min_x = min(min_x, center.x - a)
                min_y = min(min_y, center.y - b)
                min_z = min(min_z, center.z)
                max_x = max(max_x, center.x + a)
                max_y = max(max_y, center.y + b)
                max_z = max(max_z, center.z)
                has_geometry = True
            
            elif entity_type == "SPLINE":
                for point in entity.control_points:
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    min_z = min(min_z, point.z)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)
                    max_z = max(max_z, point.z)
                    has_geometry = True
            
            elif entity_type in ["TEXT", "MTEXT"]:
                point = entity.dxf.insert
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)
                min_z = min(min_z, point.z)
                max_x = max(max_x, point.x)
                max_y = max(max_y, point.y)
                max_z = max(max_z, point.z)
                has_geometry = True
        
        except Exception:
            # Skip entities that can't be processed
            pass
    
    if not has_geometry or min_x == float('inf'):
        return None
    
    return (Vec3(min_x, min_y, min_z), Vec3(max_x, max_y, max_z))


def extract_fixtures_with_details(dxf_path):
    """
    Extract all fixtures from DXF with complete details
    
    Returns:
        dict with fixture data including positions, sizes, lines, and lengths
    """
    print(f"📄 Reading DXF: {dxf_path}")
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    # Store block definitions with their bounding boxes and lines
    block_definitions = {}
    
    print(f"\n📐 Analyzing block definitions...")
    for block in doc.blocks:
        block_name = block.name
        
        # Skip anonymous blocks and special blocks
        if block_name.startswith('*') or block_name.startswith('_'):
            continue
        
        try:
            # Calculate bounding box manually
            bbox = calculate_manual_bounding_box(block)
            
            if bbox:
                min_pt, max_pt = bbox
                width = abs(max_pt[0] - min_pt[0])
                height = abs(max_pt[1] - min_pt[1])
                
                # Extract lines and calculate total length
                print(f"  • {block_name}: Extracting lines...")
                line_data = extract_block_lines_and_length(block)
                
                block_definitions[block_name] = {
                    'width': round(width, 3),
                    'height': round(height, 3),
                    'bounding_box': {
                        'min': [round(min_pt[0], 3), round(min_pt[1], 3), round(min_pt[2], 3)],
                        'max': [round(max_pt[0], 3), round(max_pt[1], 3), round(max_pt[2], 3)]
                    },
                    'lines': line_data['lines'],
                    'line_count': line_data['line_count'],
                    'total_length': line_data['total_length']
                }
                
                print(f"    ✓ Size: {width:.1f} × {height:.1f} mm, Lines: {line_data['line_count']}, Total Length: {line_data['total_length']:.1f} mm")
        
        except Exception as e:
            print(f"    ⚠️  Warning: Could not process block '{block_name}': {e}")
    
    print(f"\n✅ Processed {len(block_definitions)} block definitions\n")
    
    # Extract fixtures (INSERT entities) from modelspace
    print(f"🔍 Extracting fixtures from modelspace...")
    fixtures = []
    fixture_index = 1
    
    for entity in msp:
        if entity.dxftype() == "INSERT":
            block_name = entity.dxf.name
            
            # Skip if block not in definitions
            if block_name not in block_definitions:
                continue
            
            block_def = block_definitions[block_name]
            
            # Get insertion point
            insert_point = entity.dxf.insert
            x = round(insert_point.x, 3)
            y = round(insert_point.y, 3)
            z = round(insert_point.z, 3)
            
            # Get scale factors
            xscale = abs(entity.dxf.xscale) if hasattr(entity.dxf, 'xscale') else 1.0
            yscale = abs(entity.dxf.yscale) if hasattr(entity.dxf, 'yscale') else 1.0
            zscale = abs(entity.dxf.zscale) if hasattr(entity.dxf, 'zscale') else 1.0
            
            # Get rotation
            rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0
            
            # Calculate actual fixture size with scaling
            actual_width = block_def['width'] * xscale
            actual_height = block_def['height'] * yscale
            
            # Calculate actual total length with scaling (average of x and y scale)
            avg_scale = (xscale + yscale) / 2.0
            scaled_length = block_def['total_length'] * avg_scale
            
            fixture_data = {
                'fixture_id': f"F{fixture_index:04d}",
                'block_name': block_name,
                'position': {
                    'x': x,
                    'y': y,
                    'z': z
                },
                'size': {
                    'width': round(actual_width, 3),
                    'height': round(actual_height, 3),
                    'base_width': block_def['width'],
                    'base_height': block_def['height']
                },
                'scale': {
                    'x': round(xscale, 3),
                    'y': round(yscale, 3),
                    'z': round(zscale, 3)
                },
                'rotation': round(rotation, 3),
                'layer': entity.dxf.layer,
                'lines': {
                    'count': block_def['line_count'],
                    'base_total_length': block_def['total_length'],
                    'scaled_total_length': round(scaled_length, 3),
                    'entities': block_def['lines']
                }
            }
            
            fixtures.append(fixture_data)
            
            print(f"  {fixture_data['fixture_id']}: {block_name} at ({x:.1f}, {y:.1f}) - "
                  f"{actual_width:.1f}×{actual_height:.1f} mm - Length: {scaled_length:.1f} mm")
            
            fixture_index += 1
    
    print(f"\n✅ Extracted {len(fixtures)} fixtures\n")
    
    # Calculate summary statistics
    total_line_length = sum(f['lines']['scaled_total_length'] for f in fixtures)
    total_entities = sum(f['lines']['count'] for f in fixtures)
    
    output = {
        'source_file': dxf_path,
        'summary': {
            'total_fixtures': len(fixtures),
            'unique_blocks': len(block_definitions),
            'total_line_entities': total_entities,
            'total_line_length_mm': round(total_line_length, 3),
            'total_line_length_meters': round(total_line_length / 1000, 3)
        },
        'block_definitions': block_definitions,
        'fixtures': fixtures
    }
    
    return output


def main():
    """Main execution function"""
    
    # Check if filename provided
    if len(sys.argv) > 1:
        dxf_file = sys.argv[1]
    else:
        # Default file
        dxf_file = "image_F4bz1Dn_processed_W1BgANF_MODIFIED (1).dxf"
    
    try:
        # Extract fixture details
        result = extract_fixtures_with_details(dxf_file)
        
        # Generate output filename
        output_file = dxf_file.replace('.dxf', '_FIXTURE_ANALYSIS.json')
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"=" * 80)
        print(f"📊 SUMMARY")
        print(f"=" * 80)
        print(f"Total Fixtures: {result['summary']['total_fixtures']}")
        print(f"Unique Block Types: {result['summary']['unique_blocks']}")
        print(f"Total Line Entities: {result['summary']['total_line_entities']}")
        print(f"Total Line Length: {result['summary']['total_line_length_mm']:.2f} mm ({result['summary']['total_line_length_meters']:.2f} m)")
        print(f"\n✅ Detailed analysis saved to: {output_file}")
        print(f"=" * 80)
        
    except FileNotFoundError:
        print(f"❌ Error: File '{dxf_file}' not found")
        print(f"Usage: python extract_fixture_details.py <dxf_file>")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
