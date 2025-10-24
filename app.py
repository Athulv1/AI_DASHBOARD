#!/usr/bin/env python3
"""
Canvas-Based DXF Fixture Mover - Flask Web Application
=======================================================

A web-based interface for moving fixtures in DXF files using:
- HTML5 Canvas for visual display
- Drag-and-drop mouse interaction
- Gemini AI for automatic JSON updates
- Real-time coordinate tracking

Author: GitHub Copilot
Version: 1.0
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
import uuid
from werkzeug.utils import secure_filename
import ezdxf
from enhanced_dxf_to_json import dxf_to_json, json_to_dxf
from ai_fixture_mover import AIFixtureMover

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store session data (use Redis/DB in production)
session_storage = {}

# Gemini AI configuration
GEMINI_API_KEY = "AIzaSyDYivSaB99eiXW__eYF_WprJsa8qCZGQ2M"


@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')


@app.route('/canvas')
def canvas():
    """Canvas editor page"""
    return render_template('canvas.html')


@app.route('/upload', methods=['POST'])
def upload_dxf():
    """
    Handle DXF file upload
    
    Returns:
        JSON with session_id and canvas_data
    """
    try:
        # Check if file was uploaded
        if 'dxf_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['dxf_file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(upload_path)
        
        print(f"📁 Uploaded: {filename} → {session_id}")
        
        # Convert DXF to JSON
        print(f"🔄 Converting DXF to JSON...")
        json_data = dxf_to_json(upload_path)
        
        # Debug: Check JSON structure
        print(f"📋 JSON keys: {list(json_data.keys())}")
        print(f"   Blocks: {len(json_data.get('blocks', {}))} definitions")
        print(f"   Modelspace: {len(json_data.get('modelspace', []))} entities")
        
        # Store in session
        session_storage[session_id] = {
            'original_dxf': upload_path,
            'filename': filename,
            'json_data': json_data,
            'modifications': []
        }
        
        # Extract canvas data (fixtures and blueprint) - pass DXF path for accurate sizing
        canvas_data = extract_canvas_data(json_data, upload_path)
        
        print(f"✅ Ready! Session: {session_id}")
        print(f"   Fixtures: {len(canvas_data['fixtures'])}")
        print(f"   Blueprint entities: {len(canvas_data['blueprint'])}")
        
        # Debug: Show first few fixtures with sizes
        if canvas_data['fixtures']:
            print(f"\n📐 Sample fixture sizes:")
            for fixture in canvas_data['fixtures'][:3]:
                print(f"   • {fixture['name']}: {fixture.get('width', 'N/A')} × {fixture.get('height', 'N/A')} mm")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'canvas_data': canvas_data
        })
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def calculate_block_sizes(json_data, dxf_path=None):
    """
    Calculate the bounding box size of each block definition
    
    Args:
        json_data: Complete DXF JSON structure
        dxf_path: Optional path to DXF file for using ezdxf's bounding_box method
    
    Returns:
        Dictionary mapping block names to their sizes
    """
    block_sizes = {}
    
    # Note: ezdxf's bounding_box() method may not be available on all versions
    # We'll use manual calculation which handles nested blocks better
    
    # Note: ezdxf's bounding_box() method may not be available on all versions
    # We'll use manual calculation which handles nested blocks better
    
    # Fallback: Manual calculation from JSON data
    print("⚙️  Using manual bounding box calculation from JSON...")
    
    # First pass: Calculate all blocks with actual geometry
    for block_name, block_data in json_data.get('blocks', {}).items():
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        has_geometry = False
        entity_count = 0
        
        for entity in block_data.get('entities', []):
            entity_type = entity['dxf_type']
            entity_count += 1
            
            if entity_type == 'LINE':
                points = [entity['start'][:2], entity['end'][:2]]
                for x, y in points:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                has_geometry = True
            
            elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
                for point in entity.get('points', []):
                    x, y = point[:2] if len(point) > 2 else point
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                has_geometry = True
            
            elif entity_type == 'CIRCLE':
                center = entity['center'][:2]
                radius = entity['radius']
                min_x = min(min_x, center[0] - radius)
                min_y = min(min_y, center[1] - radius)
                max_x = max(max_x, center[0] + radius)
                max_y = max(max_y, center[1] + radius)
                has_geometry = True
            
            elif entity_type == 'ARC':
                center = entity['center'][:2]
                radius = entity['radius']
                min_x = min(min_x, center[0] - radius)
                min_y = min(min_y, center[1] - radius)
                max_x = max(max_x, center[0] + radius)
                max_y = max(max_y, center[1] + radius)
                has_geometry = True
            
            elif entity_type == 'SPLINE':
                # SPLINEs have control_points or fit_points
                control_points = entity.get('control_points', [])
                fit_points = entity.get('fit_points', [])
                points = control_points if control_points else fit_points
                
                for point in points:
                    x, y = point[:2] if len(point) > 2 else point
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                has_geometry = True
            
            elif entity_type == 'ELLIPSE':
                # ELLIPSE has center, major_axis, and ratio
                center = entity.get('center', [0, 0])[:2]
                major_axis = entity.get('major_axis', [0, 0])[:2]
                ratio = entity.get('ratio', 1.0)
                
                # Calculate semi-major and semi-minor axes lengths
                major_length = (major_axis[0]**2 + major_axis[1]**2)**0.5
                minor_length = major_length * ratio
                
                # Approximate bounding box (not exact for rotated ellipses)
                min_x = min(min_x, center[0] - major_length)
                min_y = min(min_y, center[1] - major_length)
                max_x = max(max_x, center[0] + major_length)
                max_y = max(max_y, center[1] + major_length)
                has_geometry = True
            
            elif entity_type in ['TEXT', 'MTEXT']:
                # TEXT/MTEXT: Only use insertion point, do NOT calculate text width
                # Text width can incorrectly inflate bounding boxes
                insert = entity.get('insert', entity.get('position', [0, 0]))[:2]
                min_x = min(min_x, insert[0])
                min_y = min(min_y, insert[1])
                max_x = max(max_x, insert[0])
                max_y = max(max_y, insert[1])
                has_geometry = True
            
            elif entity_type == 'POINT':
                # POINT has a location
                location = entity.get('location', [0, 0])[:2]
                min_x = min(min_x, location[0])
                min_y = min(min_y, location[1])
                max_x = max(max_x, location[0])
                max_y = max(max_y, location[1])
                has_geometry = True
            
            # Note: We do NOT include INSERT entities in Pass 1
            # INSERT entities will be resolved in Pass 2 and Pass 3
            # Including them here causes issues with insertion points far from geometry
        
        if has_geometry and min_x != float('inf'):
            width = max_x - min_x
            height = max_y - min_y
            
            # Use absolute values to handle negative sizes
            width = abs(width)
            height = abs(height)
            
            # Ensure minimum size for visibility
            width = max(width, 100)
            height = max(height, 100)
            
            block_sizes[block_name] = {
                'width': width,
                'height': height,
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y
            }


            # Debug output
            if entity_count > 0:
                print(f"   ✓ {block_name}: {width:.1f} × {height:.1f} mm ({entity_count} entities)")
        else:
            # Default size if no geometry found
            print(f"   ⚠ {block_name}: No geometry found, using default 300×300mm")
            block_sizes[block_name] = {
                'width': 300,
                'height': 300,
                'min_x': -150,
                'min_y': -150,
                'max_x': 150,
                'max_y': 150
            }
    
    # Second pass: Resolve nested blocks (blocks that only contain INSERT entities)
    print("🔗 Resolving nested block references...")
    resolved_count = 0
    
    # Create case-insensitive lookup for block sizes
    block_sizes_lower = {k.lower(): (k, v) for k, v in block_sizes.items()}
    
    for block_name, block_data in json_data.get('blocks', {}).items():
        # Check if this block contains INSERT entities
        entities = block_data.get('entities', [])
        insert_entities = [e for e in entities if e.get('dxf_type') == 'INSERT']
        non_text_entities = [e for e in entities if e.get('dxf_type') not in ['TEXT', 'MTEXT', 'INSERT']]
        
        # If block has INSERT entities, check if referenced blocks are larger
        if insert_entities:
            # Get the largest referenced block size
            max_ref_width = 0
            max_ref_height = 0
            
            for insert in insert_entities:
                ref_block_name = insert.get('name')
                ref_block_key = ref_block_name.lower() if ref_block_name else None
                if ref_block_key and ref_block_key in block_sizes_lower:
                    actual_name, ref_block_size = block_sizes_lower[ref_block_key]
                else:
                    ref_block_size = block_sizes.get(ref_block_name)
                
                if ref_block_size:
                    max_ref_width = max(max_ref_width, ref_block_size['width'])
                    max_ref_height = max(max_ref_height, ref_block_size['height'])
            
            # If current block has calculated size, check if referenced block is significantly larger
            current_size = block_sizes.get(block_name, {'width': 300, 'height': 300})
            current_width = current_size['width']
            current_height = current_size['height']
            
            # Determine if we should use the INSERT reference instead of calculated geometry
            should_resolve = False
            
            # Case 1: No real geometry, only INSERT+TEXT (always resolve)
            if len(non_text_entities) == 0:
                should_resolve = True
            # Case 2: Current size is default or suspiciously small in BOTH dimensions
            elif (current_width == 300 and current_height == 300) or \
                 (current_width == 100 and current_height == 100) or \
                 (current_width < 200 and current_height < 200):
                # Only override if referenced block is much larger
                if max_ref_width > current_width * 2 or max_ref_height > current_height * 2:
                    should_resolve = True
            # Case 3: One dimension is very small (< 150mm) but referenced block is much larger
            elif (current_width < 150 or current_height < 150) and \
                 (max_ref_width > current_width * 3 and max_ref_height > current_height * 3):
                should_resolve = True
            
        # If block has INSERT and should be resolved, resolve from INSERT
        if insert_entities and should_resolve:
            # This block only contains references to other blocks
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            resolved = False
            
            for insert in insert_entities:
                ref_block_name = insert.get('name')
                
                # Try case-insensitive lookup
                ref_block_key = ref_block_name.lower() if ref_block_name else None
                if ref_block_key and ref_block_key in block_sizes_lower:
                    actual_name, ref_block_size = block_sizes_lower[ref_block_key]
                else:
                    ref_block_size = block_sizes.get(ref_block_name)
                
                if ref_block_size and ref_block_size['width'] != 300:
                    # Get the referenced block's size and position
                    insert_pos = insert.get('insert', [0, 0, 0])[:2]
                    
                    # Get scale factors (can be negative for mirroring)
                    xscale = insert.get('xscale', 1.0)
                    yscale = insert.get('yscale', 1.0)
                    
                    # Get referenced block's bounding box in its local coordinate system
                    ref_min_x = ref_block_size.get('min_x', 0)
                    ref_min_y = ref_block_size.get('min_y', 0)
                    ref_max_x = ref_block_size.get('max_x', ref_block_size['width'])
                    ref_max_y = ref_block_size.get('max_y', ref_block_size['height'])
                    
                    # Transform referenced block's bbox into parent block's coordinate system
                    # Handle mirroring: if scale is negative, the coordinates flip
                    if xscale < 0:
                        # X-axis mirrored: swap and negate X coordinates
                        world_min_x = insert_pos[0] + (-ref_max_x) * abs(xscale)
                        world_max_x = insert_pos[0] + (-ref_min_x) * abs(xscale)
                    else:
                        world_min_x = insert_pos[0] + ref_min_x * xscale
                        world_max_x = insert_pos[0] + ref_max_x * xscale
                    
                    if yscale < 0:
                        # Y-axis mirrored: swap and negate Y coordinates
                        world_min_y = insert_pos[1] + (-ref_max_y) * abs(yscale)
                        world_max_y = insert_pos[1] + (-ref_min_y) * abs(yscale)
                    else:
                        world_min_y = insert_pos[1] + ref_min_y * yscale
                        world_max_y = insert_pos[1] + ref_max_y * yscale
                    
                    # Expand parent block's bounding box
                    min_x = min(min_x, world_min_x, world_max_x)
                    max_x = max(max_x, world_min_x, world_max_x)
                    min_y = min(min_y, world_min_y, world_max_y)
                    max_y = max(max_y, world_min_y, world_max_y)
                    
                    resolved = True
            
            if resolved and min_x != float('inf'):
                width = abs(max_x - min_x)
                height = abs(max_y - min_y)
                
                # Check if we're overriding a previous calculation
                old_size = block_sizes.get(block_name)
                if old_size and old_size['width'] != 300:
                    print(f"   🔄 {block_name}: {old_size['width']:.1f} × {old_size['height']:.1f} mm → {width:.1f} × {height:.1f} mm (corrected from '{ref_block_name}')")
                else:
                    print(f"   🔗 {block_name}: {width:.1f} × {height:.1f} mm (resolved from '{ref_block_name}')")
                
                block_sizes[block_name] = {
                    'width': width,
                    'height': height,
                    'min_x': min_x,
                    'min_y': min_y,
                    'max_x': max_x,
                    'max_y': max_y
                }
                resolved_count += 1
    
    if resolved_count > 0:
        print(f"✅ Resolved {resolved_count} nested blocks")
    
    # NOTE: Pass 3 (bbox expansion) DISABLED - it was causing issues
    # Pass 2 already correctly resolves all nested blocks like MIRROR and CLINIC
    # clinic_regular is 2600×1700mm from its geometry, CLINIC_REGULAR_1 inherits this size
    # This matches how MIRROR works: mirror unit has geometry, MIRROR_DIFFERENT_1 inherits it
    
    return block_sizes


def extract_canvas_data(json_data, dxf_path=None):
    """
    Extract simplified canvas data from DXF JSON
    
    Args:
        json_data: Complete DXF JSON structure
        dxf_path: Optional path to DXF file for accurate size calculation
    
    Returns:
        Dictionary with fixtures and blueprint data
    """
    fixtures = []
    blueprint = []
    
    # Calculate fixture sizes from block definitions
    block_sizes = calculate_block_sizes(json_data, dxf_path)
    print(f"📐 Calculated sizes for {len(block_sizes)} blocks")
    
    # Extract fixtures (INSERT entities)
    for entity in json_data.get('modelspace', []):
        if entity.get('dxf_type') == 'INSERT':
            block_name = entity['name']
            size = block_sizes.get(block_name, {'width': 300, 'height': 300, 'min_x': -150, 'min_y': -150, 'max_x': 150, 'max_y': 150})
            
            fixtures.append({
                'id': f"{entity['name']}@{entity['insert'][0]},{entity['insert'][1]}",
                'name': entity['name'],
                'position': entity['insert'][:2],  # X, Y only
                'rotation': entity.get('rotation', 0),
                'layer': entity.get('layer', '0'),
                'width': size['width'] * abs(entity.get('xscale', 1.0)),
                'height': size['height'] * abs(entity.get('yscale', 1.0)),
                'scale_x': entity.get('xscale', 1.0),  # Keep original sign for mirroring
                'scale_y': entity.get('yscale', 1.0),   # Keep original sign for mirroring
                'block_min_x': size.get('min_x', -size['width']/2),  # Block content offset from origin
                'block_min_y': size.get('min_y', -size['height']/2),  # Block content offset from origin
                'block_max_x': size.get('max_x', size['width']/2),
                'block_max_y': size.get('max_y', size['height']/2)
            })
        
        # Extract blueprint geometry (lines, polylines, etc.)
        elif entity.get('dxf_type') in ['LINE', 'LWPOLYLINE', 'POLYLINE', 'CIRCLE', 'ARC']:
            blueprint.append({
                'type': entity['dxf_type'],
                'data': extract_geometry_data(entity)
            })
    
    print(f"✅ Extracted {len(fixtures)} fixtures from modelspace")
    
    # Calculate bounds for auto-scaling
    bounds = calculate_bounds(fixtures, blueprint)
    
    return {
        'fixtures': fixtures,
        'blueprint': blueprint,
        'bounds': bounds,
        'fixture_count': len(fixtures)
    }


def extract_geometry_data(entity):
    """Extract geometry data for canvas rendering"""
    entity_type = entity['dxf_type']
    
    if entity_type == 'LINE':
        return {
            'start': entity['start'][:2],
            'end': entity['end'][:2]
        }
    
    elif entity_type == 'LWPOLYLINE' or entity_type == 'POLYLINE':
        return {
            'points': [p[:2] if len(p) > 2 else p for p in entity.get('points', [])],
            'closed': entity.get('closed', False)
        }
    
    elif entity_type == 'CIRCLE':
        return {
            'center': entity['center'][:2],
            'radius': entity['radius']
        }
    
    elif entity_type == 'ARC':
        return {
            'center': entity['center'][:2],
            'radius': entity['radius'],
            'start_angle': entity['start_angle'],
            'end_angle': entity['end_angle']
        }
    
    return {}


def calculate_bounds(fixtures, blueprint):
    """Calculate bounding box for canvas scaling"""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    # Check fixture positions
    for fixture in fixtures:
        x, y = fixture['position']
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
    
    # Check blueprint geometry
    for entity in blueprint:
        if entity['type'] == 'LINE':
            data = entity['data']
            for point in [data['start'], data['end']]:
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])
    
    # Add padding
    padding = 1000  # mm
    
    return {
        'min_x': min_x - padding,
        'min_y': min_y - padding,
        'max_x': max_x + padding,
        'max_y': max_y + padding,
        'width': max_x - min_x + 2 * padding,
        'height': max_y - min_y + 2 * padding
    }


@app.route('/move_fixture', methods=['POST'])
def move_fixture():
    """
    Process fixture movement with Gemini AI
    
    Expects JSON:
    {
        "session_id": "...",
        "fixture_id": "...",
        "fixture_name": "...",
        "start_position": [x, y],
        "end_position": [x, y],
        "delta": [dx, dy]
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id not in session_storage:
            return jsonify({'error': 'Invalid session'}), 400
        
        fixture_name = data.get('fixture_name')
        start_pos = data.get('start_position')
        end_pos = data.get('end_position')
        delta = data.get('delta')
        
        print(f"\n🔧 Moving fixture:")
        print(f"   Name: {fixture_name}")
        print(f"   From: ({start_pos[0]:.2f}, {start_pos[1]:.2f})")
        print(f"   To:   ({end_pos[0]:.2f}, {end_pos[1]:.2f})")
        print(f"   Delta: ({delta[0]:.2f}, {delta[1]:.2f})")
        
        # Use Gemini AI to generate modification
        ai_mover = AIFixtureMover(GEMINI_API_KEY)
        
        # Create prompt for Gemini
        prompt = f"""
        Generate a fixture modification in JSON format.
        
        Fixture to move:
        - Name: {fixture_name}
        - Original position: {start_pos}
        - New position: {end_pos}
        
        Output ONLY valid JSON in this exact format:
        {{
          "fixtures": [
            {{
              "block_name": "{fixture_name}",
              "original_position": {start_pos},
              "new_position": {end_pos}
            }}
          ]
        }}
        """
        
        print(f"🤖 Calling Gemini AI...")
        
        # Call Gemini API
        try:
            response = ai_mover.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            
            modification = json.loads(response_text)
            
            print(f"✅ AI generated modification")
            
        except Exception as e:
            print(f"⚠️  AI failed, using direct modification: {e}")
            # Fallback: create modification manually
            modification = {
                "fixtures": [{
                    "block_name": fixture_name,
                    "original_position": start_pos,
                    "new_position": end_pos
                }]
            }
        
        # Store modification
        session_storage[session_id]['modifications'].append(modification)
        
        # Update JSON data
        update_json_with_modification(session_id, modification)
        
        return jsonify({
            'success': True,
            'modification': modification
        })
    
    except Exception as e:
        print(f"❌ Move error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def update_json_with_modification(session_id, modification):
    """Update the stored JSON data with the modification"""
    json_data = session_storage[session_id]['json_data']
    
    for mod in modification.get('fixtures', []):
        block_name = mod['block_name']
        orig_pos = mod['original_position']
        new_pos = mod['new_position']
        
        # Find and update the fixture in modelspace
        for entity in json_data.get('modelspace', []):
            if entity['dxf_type'] == 'INSERT' and entity['name'] == block_name:
                # Check if position matches (with tolerance)
                current_pos = entity['insert'][:2]
                if (abs(current_pos[0] - orig_pos[0]) < 0.1 and 
                    abs(current_pos[1] - orig_pos[1]) < 0.1):
                    # Update position
                    entity['insert'] = [new_pos[0], new_pos[1], entity['insert'][2]]
                    print(f"   ✅ Updated {block_name} in JSON")
                    break


@app.route('/download/<session_id>')
def download_dxf(session_id):
    """
    Generate and download modified DXF file
    """
    try:
        if session_id not in session_storage:
            return jsonify({'error': 'Invalid session'}), 400
        
        session_data = session_storage[session_id]
        json_data = session_data['json_data']
        original_filename = session_data['filename']
        
        print(f"\n📥 Generating DXF for download...")
        
        # Generate output filename
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}-MODIFIED.dxf"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_{output_filename}")
        
        # Convert JSON back to DXF
        json_to_dxf(json_data, output_path)
        
        print(f"✅ Generated: {output_filename}")
        
        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/dxf'
        )
    
    except Exception as e:
        print(f"❌ Download error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/session/<session_id>')
def get_session_info(session_id):
    """Get session information"""
    if session_id not in session_storage:
        return jsonify({'error': 'Invalid session'}), 400
    
    session_data = session_storage[session_id]
    
    return jsonify({
        'filename': session_data['filename'],
        'modifications_count': len(session_data['modifications'])
    })


if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  CANVAS-BASED DXF FIXTURE MOVER                            ║
║                  Flask Web Application                                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🌐 Starting server...
📍 Open your browser to: http://localhost:5000

Features:
✅ Upload DXF files
✅ Visual canvas display
✅ Drag & drop fixtures
✅ Real-time coordinate tracking
✅ Gemini AI integration
✅ Download modified DXF

Press Ctrl+C to stop the server
""")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
