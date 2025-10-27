#!/usr/bin/env python3
"""
AI DXF Fixture Mover - Web Application
======================================

A beautiful web interface for moving fixtures in DXF files using AI.

USAGE:
------
    python3 web_app.py

Then open your browser to: http://localhost:5000

Author: GitHub Copilot + Google Gemini AI
Version: 1.0
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import google.generativeai as genai
import ezdxf
import json
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyDYivSaB99eiXW__eYF_WprJsa8qCZGQ2M"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


def get_fixtures_from_dxf(dxf_path):
    """Extract all fixtures from DXF file"""
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        fixtures = []
        for entity in msp:
            if entity.dxftype() == 'INSERT':
                pos = entity.dxf.insert
                fixtures.append({
                    'name': entity.dxf.name,
                    'x': float(pos.x),
                    'y': float(pos.y),
                    'z': float(pos.z),
                    'rotation': float(entity.dxf.rotation) if hasattr(entity.dxf, 'rotation') else 0.0
                })
        
        return fixtures
    except Exception as e:
        return None


def create_ai_prompt(fixtures, user_command):
    """Create AI prompt for Gemini"""
    
    # Get unique fixture names for reference
    fixture_names = list(set([f['name'] for f in fixtures]))
    fixture_names_str = "\n".join([f"  - {name}" for name in sorted(fixture_names)])
    
    # Show ALL fixtures with full details (not just first 15)
    fixtures_json = json.dumps(fixtures, indent=2)
    
    prompt = f"""You are a DXF fixture movement assistant. The user wants to move/rotate fixtures in a CAD drawing.

AVAILABLE FIXTURE TYPES ({len(fixture_names)} unique types):
{fixture_names_str}

ALL FIXTURES IN THE DRAWING ({len(fixtures)} total):
{fixtures_json}

USER COMMAND: "{user_command}"

Your task is to understand the user's command and generate a JSON modifications file.

CRITICAL FIXTURE MATCHING RULES:
1. Look at the AVAILABLE FIXTURE TYPES list above
2. The user might say "EURO_CENTRE" - this means find ALL fixtures with names containing "EURO_CENTRE"
   Example: EURO_CENTRE_1, EURO_CENTRE_2, EURO_CENTRE_3, EURO_CENTRE_4
3. The user might say "EURO_CENTRE_2" - this means ONLY the fixture named exactly "EURO_CENTRE_2"
4. Use the EXACT block_name from the ALL FIXTURES list - copy it exactly!

MOVEMENT RULES:
1. For "move up/down/left/right by X mm":
   - UP = increase Y (add to Y value)
   - DOWN = decrease Y (subtract from Y value)
   - RIGHT = increase X (add to X value)
   - LEFT = decrease X (subtract from X value)

2. For "rotate by X degrees":
   - Add X to the current rotation value
   - Example: current rotation is 90, user says "rotate by 45" → new rotation = 135

3. For "delete [fixture]" or "remove [fixture]":
   - Find the fixture in the list above
   - Set "delete": true in the JSON
   - Include the original_position
   - DO NOT include new_position or new_rotation
   - Example for "Delete EURO_CENTRE_1":
   {{
     "fixtures": [
       {{
         "block_name": "EURO_CENTRE_1",
         "original_position": [7354.17, -3065.74],
         "delete": true
       }}
     ]
   }}

4. If user says "all [type]", apply to ALL fixtures matching that type

OUTPUT FORMAT EXAMPLES:

For MOVE command:
{{
  "fixtures": [
    {{
      "block_name": "EXACT_NAME_FROM_LIST",
      "original_position": [X, Y],
      "new_position": [NEW_X, NEW_Y]
    }}
  ]
}}

For ROTATE command:
{{
  "fixtures": [
    {{
      "block_name": "EXACT_NAME_FROM_LIST",
      "original_position": [X, Y],
      "new_rotation": NEW_DEGREES
    }}
  ]
}}

For DELETE command:
{{
  "fixtures": [
    {{
      "block_name": "EXACT_NAME_FROM_LIST",
      "original_position": [X, Y],
      "delete": true
    }}
  ]
}}

CRITICAL RULES:
- ALWAYS find matching fixtures from the AVAILABLE FIXTURE TYPES list above
- Use EXACT block_name from the fixture list
- For delete: ONLY include block_name, original_position, and "delete": true
- For rotate: ONLY include block_name, original_position, and new_rotation
- For move: ONLY include block_name, original_position, and new_position
- Output ONLY JSON, no markdown, no explanations

If you cannot find any matching fixtures, output:
{{
  "error": "No fixtures found matching '[fixture_name]'. Available types: [list some types]"
}}"""
    

    return prompt


def apply_modifications(dxf_path, modifications):
    """Apply modifications to DXF and return output path"""
    
    # Load original DXF
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    # Create fixture mapping
    original_fixtures = {}
    for entity in msp:
        if entity.dxftype() == 'INSERT':
            name = entity.dxf.name
            pos = (round(entity.dxf.insert.x, 2), round(entity.dxf.insert.y, 2))
            key = f'{name}@{pos[0]},{pos[1]}'
            
            if key not in original_fixtures:
                original_fixtures[key] = []
            original_fixtures[key].append(entity)
    
    # Apply modifications
    changes = []
    for mod in modifications.get('fixtures', []):
        block_name = mod['block_name']
        orig_pos = mod['original_position']
        new_pos = mod.get('new_position')
        new_rotation = mod.get('new_rotation')
        should_delete = mod.get('delete', False)
        
        # Debug logging
        print(f"DEBUG: Processing {block_name}, delete={should_delete}")
        
        orig_pos_key = (round(orig_pos[0], 2), round(orig_pos[1], 2))
        key = f'{block_name}@{orig_pos_key[0]},{orig_pos_key[1]}'
        
        if key in original_fixtures and original_fixtures[key]:
            fixture_to_update = original_fixtures[key].pop(0)
            old_pos = fixture_to_update.dxf.insert
            old_rotation = fixture_to_update.dxf.rotation if hasattr(fixture_to_update.dxf, 'rotation') else 0
            
            change_info = {'name': block_name}
            
            # Handle deletion
            if should_delete:
                print(f"DEBUG: Deleting {block_name} from modelspace")
                msp.delete_entity(fixture_to_update)
                change_info['deleted'] = True
                change_info['position'] = {'x': old_pos.x, 'y': old_pos.y}
                changes.append(change_info)
                continue
            
            # Update position if provided
            if new_pos:
                new_pos_vec = ezdxf.math.Vec3(new_pos)
                fixture_to_update.dxf.insert = new_pos_vec
                
                delta_x = new_pos_vec.x - old_pos.x
                delta_y = new_pos_vec.y - old_pos.y
                
                change_info.update({
                    'from': {'x': old_pos.x, 'y': old_pos.y},
                    'to': {'x': new_pos_vec.x, 'y': new_pos_vec.y},
                    'delta': {'x': delta_x, 'y': delta_y}
                })
            
            # Update rotation if provided
            if new_rotation is not None:
                fixture_to_update.dxf.rotation = new_rotation
                change_info['rotation'] = {
                    'from': old_rotation,
                    'to': new_rotation,
                    'delta': new_rotation - old_rotation
                }
            
            changes.append(change_info)
    
    # Set R2018 + MM format
    doc.header['$INSUNITS'] = 4
    doc.header['$MEASUREMENT'] = 1
    
    # Generate output filename
    session_id = session.get('session_id', uuid.uuid4().hex)
    output_filename = f"modified_{session_id}.dxf"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    # Save
    doc.saveas(output_path)
    
    return output_path, changes


@app.route('/')
def index():
    """Main page"""
    session['session_id'] = uuid.uuid4().hex
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload DXF file"""
    
    if 'dxf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['dxf_file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.dxf'):
        return jsonify({'error': 'Only DXF files are allowed'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    session_id = session.get('session_id', uuid.uuid4().hex)
    session['session_id'] = session_id
    
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
    file.save(upload_path)
    
    # Extract fixtures
    fixtures = get_fixtures_from_dxf(upload_path)
    
    if fixtures is None:
        return jsonify({'error': 'Failed to read DXF file'}), 400
    
    # Store in session
    session['dxf_path'] = upload_path
    session['original_filename'] = filename
    
    # Group fixtures by type
    fixture_types = {}
    for f in fixtures:
        name = f['name']
        if name not in fixture_types:
            fixture_types[name] = []
        fixture_types[name].append(f)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'total_fixtures': len(fixtures),
        'fixture_types': {k: len(v) for k, v in fixture_types.items()},
        'sample_fixtures': fixtures[:5]  # First 5 as preview
    })


@app.route('/analyze', methods=['POST'])
def analyze_command():
    """Analyze command and show matching fixtures"""
    
    data = request.get_json()
    user_command = data.get('command', '').strip()
    
    if not user_command:
        return jsonify({'error': 'No command provided'}), 400
    
    dxf_path = session.get('dxf_path')
    if not dxf_path or not os.path.exists(dxf_path):
        return jsonify({'error': 'No DXF file uploaded'}), 400
    
    # Get fixtures
    fixtures = get_fixtures_from_dxf(dxf_path)
    
    # Extract fixture name from command (simple pattern matching)
    import re
    
    # Try to find fixture name in command - handle Move, Rotate, and Delete
    # Pattern 1: Move/Rotate/Delete <fixture> <direction/action>
    fixture_name_pattern = r'(?:Move|move|Rotate|rotate|Delete|delete|Remove|remove)\s+([A-Za-z0-9\-_\s]+?)(?:\s+at|\s+right|\s+left|\s+up|\s+down|\s+by|$)'
    match = re.search(fixture_name_pattern, user_command)
    
    # Pattern 2: If pattern 1 fails, try to get everything after Move/Rotate until prepositions
    if not match:
        fixture_name_pattern2 = r'(?:Move|move|Rotate|rotate)\s+(all\s+)?([A-Za-z0-9\-_]+)'
        match = re.search(fixture_name_pattern2, user_command)
        if match:
            match_groups = match.groups()
            fixture_type = match_groups[1] if len(match_groups) > 1 else match_groups[0]
    
    matching_fixtures = []
    fixture_type = None
    
    if match:
        fixture_type = match.group(1).strip() if not fixture_type else fixture_type.strip()
        
        # Remove "all" prefix if present
        if fixture_type.lower().startswith('all '):
            fixture_type = fixture_type[4:].strip()
        
        # Find all matching fixtures - use smarter matching
        for f in fixtures:
            fixture_name = f['name']
            # Exact match
            if fixture_name.lower() == fixture_type.lower():
                matching_fixtures.append(f)
            # Partial match (fixture_type is substring of fixture name)
            elif fixture_type.lower() in fixture_name.lower():
                matching_fixtures.append(f)
            # Base name match (remove trailing numbers/underscores)
            else:
                # Extract base name: EURO_CENTRE_2 -> EURO_CENTRE
                base_fixture = re.sub(r'_\d+$', '', fixture_name)
                base_search = re.sub(r'_\d+$', '', fixture_type)
                if base_fixture.lower() == base_search.lower():
                    matching_fixtures.append(f)
    
    # If "all" is mentioned, find all of that type
    if 'all' in user_command.lower() and fixture_type:
        for f in fixtures:
            if fixture_type.lower() in f['name'].lower():
                if f not in matching_fixtures:
                    matching_fixtures.append(f)
    
    return jsonify({
        'fixture_type': fixture_type,
        'total_found': len(matching_fixtures),
        'matching_fixtures': matching_fixtures[:20],  # Limit to 20 for display
        'needs_selection': len(matching_fixtures) > 1 and 'all' not in user_command.lower()
    })


@app.route('/process', methods=['POST'])
def process_command():
    """Process user command with AI"""
    
    data = request.get_json()
    user_command = data.get('command', '').strip()
    selected_fixtures = data.get('selected_fixtures', None)  # NEW: Selected fixtures
    
    if not user_command:
        return jsonify({'error': 'No command provided'}), 400
    
    dxf_path = session.get('dxf_path')
    if not dxf_path or not os.path.exists(dxf_path):
        return jsonify({'error': 'No DXF file uploaded'}), 400
    
    # Get fixtures
    fixtures = get_fixtures_from_dxf(dxf_path)
    
    try:
        # If specific fixtures selected, modify the command
        if selected_fixtures:
            # Create targeted prompt with only selected fixtures
            prompt = create_targeted_prompt(selected_fixtures, user_command)
        else:
            # Create prompt and call Gemini
            prompt = create_ai_prompt(fixtures, user_command)
        
        response = gemini_model.generate_content(prompt)
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        
        # Parse JSON
        modifications = json.loads(response_text)
        
        # Check for errors
        if 'error' in modifications:
            return jsonify({
                'success': False,
                'error': modifications['error']
            })
        
        # Store modifications in session
        session['modifications'] = modifications
        
        return jsonify({
            'success': True,
            'modifications': modifications,
            'fixtures_to_move': len(modifications.get('fixtures', []))
        })
        
    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': 'AI response is not valid JSON',
            'details': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def create_targeted_prompt(selected_fixtures, user_command):
    """Create AI prompt for specific selected fixtures"""
    
    fixtures_json = json.dumps(selected_fixtures, indent=2)
    
    prompt = f"""You are a DXF fixture movement assistant. The user has selected SPECIFIC fixtures to move/rotate/delete.

SELECTED FIXTURES:
{fixtures_json}

USER COMMAND: "{user_command}"

Your task is to process ONLY these selected fixtures according to the command.

COMMAND TYPES:

1. MOVE commands ("move up/down/left/right by X mm"):
   - UP = increase Y
   - DOWN = decrease Y
   - RIGHT = increase X
   - LEFT = decrease X
   Output: {{"block_name": "...", "original_position": [x,y], "new_position": [newX,newY]}}

2. ROTATE commands ("rotate by X degrees"):
   - Add X to current rotation
   Output: {{"block_name": "...", "original_position": [x,y], "new_rotation": newDegrees}}

3. DELETE/REMOVE commands ("delete" or "remove"):
   - Mark for deletion
   Output: {{"block_name": "...", "original_position": [x,y], "delete": true}}

CRITICAL: 
- Use EXACT block_name from the selected fixtures
- For DELETE: ONLY include block_name, original_position, and "delete": true
- Do NOT include new_position or new_rotation for delete commands

OUTPUT FORMAT (MUST BE VALID JSON ONLY):
{{
  "fixtures": [
    {{
      "block_name": "EXACT_FIXTURE_NAME_FROM_SELECTED",
      "original_position": [X, Y],
      "new_position": [NEW_X, NEW_Y],
      "new_rotation": NEW_ROTATION,
      "delete": true
    }}
  ]
}}

REMEMBER: 
- Use EXACT block_name from selected fixtures
- For MOVE: include new_position
- For ROTATE: include new_rotation
- For DELETE: include "delete": true (and NO new_position or new_rotation)
- Output ONLY JSON, no markdown, no explanations."""
    
    return prompt


@app.route('/apply', methods=['POST'])
def apply_changes():
    """Apply modifications and generate output DXF"""
    
    dxf_path = session.get('dxf_path')
    modifications = session.get('modifications')
    
    if not dxf_path or not modifications:
        return jsonify({'error': 'No modifications to apply'}), 400
    
    try:
        output_path, changes = apply_modifications(dxf_path, modifications)
        
        session['output_path'] = output_path
        session['output_filename'] = Path(session['original_filename']).stem + '_MODIFIED.dxf'
        
        return jsonify({
            'success': True,
            'changes': changes,
            'download_ready': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/download')
def download_file():
    """Download modified DXF file"""
    
    output_path = session.get('output_path')
    output_filename = session.get('output_filename', 'modified.dxf')
    
    if not output_path or not os.path.exists(output_path):
        return "File not found", 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_filename,
        mimetype='application/dxf'
    )


@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up session files"""
    
    # Clean up uploaded file
    dxf_path = session.get('dxf_path')
    if dxf_path and os.path.exists(dxf_path):
        try:
            os.remove(dxf_path)
        except:
            pass
    
    # Clean up output file
    output_path = session.get('output_path')
    if output_path and os.path.exists(output_path):
        try:
            os.remove(output_path)
        except:
            pass
    
    # Clear session
    session.clear()
    
    return jsonify({'success': True})


if __name__ == '__main__':
    print("""
================================================================================
              AI DXF FIXTURE MOVER - WEB APPLICATION                        
              Powered by Google Gemini AI                                   
================================================================================

Starting server...

Open your browser and go to:

    http://localhost:5000

Gemini API: Configured
Web Interface: Ready

Press Ctrl+C to stop the server
================================================================================
""")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
