# 🎨 PROPOSED CANVAS-BASED FIXTURE MOVER ARCHITECTURE

## 🌟 **SYSTEM OVERVIEW**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WEB-BASED CANVAS EDITOR                         │
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐              │
│  │   Upload    │ →  │   Canvas     │ →  │  Download   │              │
│  │    DXF      │    │   Preview    │    │    DXF      │              │
│  └─────────────┘    └──────────────┘    └─────────────┘              │
│                            ↓                                            │
│                     ┌──────────────┐                                   │
│                     │  Drag & Drop │                                   │
│                     │   Fixtures   │                                   │
│                     └──────────────┘                                   │
│                            ↓                                            │
│                     ┌──────────────┐                                   │
│                     │  Gemini AI   │                                   │
│                     │ Auto-Update  │                                   │
│                     └──────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 **DETAILED WORKFLOW**

### **Step-by-Step Process:**

```
1. UPLOAD DXF FILE
   ├─ User selects .dxf file from computer
   ├─ Flask receives file via /upload endpoint
   ├─ enhanced_dxf_to_json.py converts DXF → JSON
   └─ Store JSON in session/temp storage

2. CANVAS PREVIEW
   ├─ Backend sends simplified canvas data to frontend
   │  └─ Includes: fixtures (INSERTs), walls (LINEs/POLYLINEs)
   ├─ Frontend renders on HTML5 Canvas
   │  ├─ Draw background blueprint (walls, lines)
   │  ├─ Draw fixtures as colored rectangles/shapes
   │  └─ Add labels to fixtures
   └─ User sees interactive visual representation

3. DRAG & DROP INTERACTION
   ├─ User clicks on fixture (mousedown event)
   ├─ Fixture becomes "selected" (highlighted)
   ├─ User drags fixture (mousemove event)
   │  ├─ Display current X,Y coordinates in real-time
   │  └─ Show visual feedback (ghost outline)
   ├─ User releases mouse (mouseup event)
   │  ├─ Capture START coordinates (original position)
   │  └─ Capture END coordinates (new position)
   └─ Display coordinate diff (ΔX, ΔY)

4. AI-POWERED MODIFICATION
   ├─ Frontend sends drag data to /move_fixture endpoint
   │  {
   │    "fixture_name": "D-Table-1200",
   │    "start_position": [12257.10, -862683.05],
   │    "end_position": [13257.10, -862683.05],
   │    "delta": [1000.0, 0.0]
   │  }
   │
   ├─ Backend creates Gemini prompt:
   │  "Update the fixture 'D-Table-1200' from position 
   │   [12257.10, -862683.05] to [13257.10, -862683.05]"
   │
   ├─ Gemini API returns modifications.json:
   │  {
   │    "fixtures": [{
   │      "block_name": "D-Table-1200",
   │      "original_position": [12257.10, -862683.05],
   │      "new_position": [13257.10, -862683.05]
   │    }]
   │  }
   │
   └─ Backend updates master JSON with new coordinates

5. DXF GENERATION & DOWNLOAD
   ├─ User clicks "Download DXF" button
   ├─ Frontend calls /download endpoint
   ├─ Backend uses json_to_dxf.py to rebuild DXF
   ├─ Apply R2018+MM format
   └─ Return DXF file for download
```

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **Backend (Flask) - Python**

```python
# app.py (Flask Web Server)

from flask import Flask, request, jsonify, send_file, render_template
import os
import json
from enhanced_dxf_to_json import dxf_to_json, json_to_dxf
from ai_fixture_mover import AIFixtureMover

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['OUTPUT_FOLDER'] = 'outputs/'

# Global storage (use Redis/DB in production)
session_data = {}

@app.route('/')
def index():
    return render_template('canvas.html')

@app.route('/upload', methods=['POST'])
def upload_dxf():
    """Upload DXF and convert to JSON"""
    # 1. Receive file
    # 2. Save temporarily
    # 3. Convert DXF → JSON
    # 4. Store in session
    # 5. Return canvas data (fixtures + blueprint)
    pass

@app.route('/get_canvas_data/<session_id>')
def get_canvas_data(session_id):
    """Return simplified canvas data for rendering"""
    # Return: {fixtures: [...], walls: [...], bounds: {...}}
    pass

@app.route('/move_fixture', methods=['POST'])
def move_fixture():
    """Process fixture movement with Gemini AI"""
    # 1. Receive drag data
    # 2. Call Gemini API
    # 3. Update JSON
    # 4. Return success
    pass

@app.route('/download/<session_id>')
def download_dxf(session_id):
    """Generate and download modified DXF"""
    # 1. Get modified JSON
    # 2. Convert JSON → DXF
    # 3. Return file
    pass
```

---

### **Frontend (HTML + Canvas) - JavaScript**

```html
<!-- templates/canvas.html -->

<!DOCTYPE html>
<html>
<head>
    <title>DXF Canvas Editor</title>
    <style>
        #canvas {
            border: 2px solid #333;
            cursor: crosshair;
        }
        .fixture-selected {
            border: 3px dashed red;
        }
        #coordinates {
            font-family: monospace;
            padding: 10px;
            background: #f0f0f0;
        }
    </style>
</head>
<body>
    <h1>🎨 DXF Fixture Canvas Editor</h1>
    
    <!-- Upload Section -->
    <div id="upload-section">
        <input type="file" id="dxf-upload" accept=".dxf">
        <button onclick="uploadDXF()">Upload DXF</button>
    </div>
    
    <!-- Canvas Section -->
    <div id="canvas-section" style="display:none;">
        <canvas id="canvas" width="1200" height="800"></canvas>
        
        <!-- Coordinate Display -->
        <div id="coordinates">
            <p>Selected: <span id="selected-fixture">None</span></p>
            <p>Start: <span id="start-coords">(0, 0)</span></p>
            <p>Current: <span id="current-coords">(0, 0)</span></p>
            <p>Delta: <span id="delta-coords">(0, 0)</span></p>
        </div>
        
        <!-- Actions -->
        <button onclick="downloadDXF()">📥 Download Modified DXF</button>
    </div>
    
    <script src="/static/canvas-editor.js"></script>
</body>
</html>
```

```javascript
// static/canvas-editor.js

class CanvasEditor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.fixtures = [];
        this.selectedFixture = null;
        this.isDragging = false;
        this.dragStartPos = null;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
    }
    
    loadCanvasData(data) {
        // Load fixtures and blueprint from JSON
        this.fixtures = data.fixtures;
        this.blueprint = data.walls;
        this.render();
    }
    
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw blueprint (walls, lines)
        this.drawBlueprint();
        
        // Draw fixtures
        this.fixtures.forEach(fixture => {
            this.drawFixture(fixture);
        });
    }
    
    drawBlueprint() {
        // Draw walls and lines in light gray
        this.ctx.strokeStyle = '#ccc';
        this.ctx.lineWidth = 1;
        
        this.blueprint.forEach(line => {
            this.ctx.beginPath();
            this.ctx.moveTo(line.start[0], line.start[1]);
            this.ctx.lineTo(line.end[0], line.end[1]);
            this.ctx.stroke();
        });
    }
    
    drawFixture(fixture) {
        const [x, y] = fixture.position;
        const isSelected = this.selectedFixture === fixture;
        
        // Draw fixture as colored rectangle
        this.ctx.fillStyle = isSelected ? '#ff6b6b' : '#4ecdc4';
        this.ctx.fillRect(x - 25, y - 25, 50, 50);
        
        // Draw border
        this.ctx.strokeStyle = isSelected ? '#c92a2a' : '#087f5b';
        this.ctx.lineWidth = isSelected ? 3 : 1;
        this.ctx.strokeRect(x - 25, y - 25, 50, 50);
        
        // Draw label
        this.ctx.fillStyle = '#000';
        this.ctx.font = '10px Arial';
        this.ctx.fillText(fixture.name, x - 20, y + 40);
    }
    
    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Check if clicked on a fixture
        this.selectedFixture = this.getFixtureAt(x, y);
        
        if (this.selectedFixture) {
            this.isDragging = true;
            this.dragStartPos = [...this.selectedFixture.position];
            
            // Update UI
            document.getElementById('selected-fixture').textContent = 
                this.selectedFixture.name;
            document.getElementById('start-coords').textContent = 
                `(${this.dragStartPos[0].toFixed(2)}, ${this.dragStartPos[1].toFixed(2)})`;
        }
    }
    
    onMouseMove(e) {
        if (!this.isDragging || !this.selectedFixture) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Update fixture position
        this.selectedFixture.position = [x, y];
        
        // Update UI
        document.getElementById('current-coords').textContent = 
            `(${x.toFixed(2)}, ${y.toFixed(2)})`;
        
        const dx = x - this.dragStartPos[0];
        const dy = y - this.dragStartPos[1];
        document.getElementById('delta-coords').textContent = 
            `(${dx.toFixed(2)}, ${dy.toFixed(2)})`;
        
        // Re-render
        this.render();
    }
    
    async onMouseUp(e) {
        if (!this.isDragging || !this.selectedFixture) return;
        
        this.isDragging = false;
        
        const endPos = [...this.selectedFixture.position];
        
        // Send to backend for Gemini processing
        await this.updateFixturePosition(
            this.selectedFixture.name,
            this.dragStartPos,
            endPos
        );
    }
    
    async updateFixturePosition(name, startPos, endPos) {
        const response = await fetch('/move_fixture', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                fixture_name: name,
                start_position: startPos,
                end_position: endPos,
                delta: [endPos[0] - startPos[0], endPos[1] - startPos[1]]
            })
        });
        
        const result = await response.json();
        console.log('Gemini AI updated:', result);
    }
    
    getFixtureAt(x, y) {
        return this.fixtures.find(f => {
            const [fx, fy] = f.position;
            return x >= fx - 25 && x <= fx + 25 && 
                   y >= fy - 25 && y <= fy + 25;
        });
    }
}

// Initialize
let editor;

async function uploadDXF() {
    const fileInput = document.getElementById('dxf-upload');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a DXF file');
        return;
    }
    
    const formData = new FormData();
    formData.append('dxf_file', file);
    
    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    
    // Show canvas section
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('canvas-section').style.display = 'block';
    
    // Load canvas data
    editor = new CanvasEditor('canvas');
    editor.loadCanvasData(data.canvas_data);
}

async function downloadDXF() {
    const response = await fetch('/download/' + sessionId);
    const blob = await response.blob();
    
    // Trigger download
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'modified-blueprint.dxf';
    a.click();
}
```

---

## 🔄 **DATA FLOW DIAGRAM**

```
USER                    FRONTEND (Canvas)              BACKEND (Flask)               GEMINI AI
 │                            │                              │                           │
 │  1. Upload DXF             │                              │                           │
 ├──────────────────────────► │                              │                           │
 │                            │  2. POST /upload             │                           │
 │                            ├─────────────────────────────►│                           │
 │                            │                              │  3. DXF → JSON            │
 │                            │                              ├─────────────┐             │
 │                            │                              │◄────────────┘             │
 │                            │  4. Return canvas_data       │                           │
 │                            │◄─────────────────────────────┤                           │
 │  5. Display Canvas         │                              │                           │
 │◄───────────────────────────┤                              │                           │
 │                            │                              │                           │
 │  6. Drag Fixture           │                              │                           │
 ├──────────────────────────► │                              │                           │
 │                            │  7. Capture Coordinates      │                           │
 │                            ├────────────┐                 │                           │
 │                            │◄───────────┘                 │                           │
 │                            │                              │                           │
 │  8. Release (Drop)         │                              │                           │
 ├──────────────────────────► │                              │                           │
 │                            │  9. POST /move_fixture       │                           │
 │                            ├─────────────────────────────►│                           │
 │                            │    {start, end, delta}       │  10. Call Gemini API      │
 │                            │                              ├──────────────────────────►│
 │                            │                              │  11. Generate JSON        │
 │                            │                              │◄──────────────────────────┤
 │                            │                              │  12. Update master JSON   │
 │                            │                              ├────────────┐              │
 │                            │                              │◄───────────┘              │
 │                            │  13. Return success          │                           │
 │                            │◄─────────────────────────────┤                           │
 │                            │                              │                           │
 │  14. Click Download        │                              │                           │
 ├──────────────────────────► │                              │                           │
 │                            │  15. GET /download           │                           │
 │                            ├─────────────────────────────►│                           │
 │                            │                              │  16. JSON → DXF           │
 │                            │                              ├────────────┐              │
 │                            │                              │◄───────────┘              │
 │                            │  17. Return DXF file         │                           │
 │                            │◄─────────────────────────────┤                           │
 │  18. Download DXF          │                              │                           │
 │◄───────────────────────────┤                              │                           │
```

---

## 📦 **REQUIRED PACKAGES**

### **Backend:**
```bash
pip install flask
pip install ezdxf
pip install google-generativeai
```

### **Frontend:**
- HTML5 Canvas (built-in)
- Vanilla JavaScript (no frameworks needed)
- Optional: Fabric.js for advanced canvas features

---

## 🎯 **KEY FEATURES**

### **Canvas Rendering:**
- ✅ Display DXF blueprint as background
- ✅ Render fixtures as interactive shapes
- ✅ Color-coding for different fixture types
- ✅ Labels for fixture names

### **Drag & Drop:**
- ✅ Click to select fixture
- ✅ Drag with mouse to new position
- ✅ Real-time coordinate display
- ✅ Visual feedback (highlighting, ghost outline)
- ✅ Snap-to-grid (optional)

### **Coordinate Tracking:**
- ✅ Start position (original)
- ✅ Current position (during drag)
- ✅ End position (after drop)
- ✅ Delta (ΔX, ΔY) display
- ✅ Distance traveled

### **AI Integration:**
- ✅ Automatic prompt generation
- ✅ Gemini API call with movement data
- ✅ JSON modification
- ✅ Error handling

### **DXF Management:**
- ✅ Upload DXF
- ✅ Convert to JSON
- ✅ Modify JSON
- ✅ Convert back to DXF
- ✅ Download modified file

---

## 🚀 **IMPLEMENTATION PHASES**

### **Phase 1: Basic Web App (1-2 hours)**
- ✅ Create Flask app with routes
- ✅ Create basic HTML template
- ✅ File upload functionality
- ✅ DXF → JSON conversion

### **Phase 2: Canvas Rendering (2-3 hours)**
- ✅ Set up HTML5 Canvas
- ✅ Render fixtures as rectangles
- ✅ Display fixture labels
- ✅ Draw background blueprint (lines)

### **Phase 3: Drag & Drop (2-3 hours)**
- ✅ Mouse event handlers
- ✅ Fixture selection logic
- ✅ Drag mechanics
- ✅ Coordinate tracking UI

### **Phase 4: Gemini Integration (1-2 hours)**
- ✅ Create prompt from drag data
- ✅ Call Gemini API
- ✅ Parse response
- ✅ Update JSON

### **Phase 5: DXF Generation (1 hour)**
- ✅ Convert modified JSON → DXF
- ✅ Download functionality
- ✅ File naming

### **Phase 6: Polish & Testing (2-3 hours)**
- ✅ Error handling
- ✅ Loading indicators
- ✅ Better UI/UX
- ✅ Testing with real DXF files

**Total Estimated Time: 9-14 hours**

---

## 🎨 **UI MOCKUP**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🏠 DXF Canvas Fixture Editor                              [Upload] [⚙️] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                         CANVAS AREA                               │ │
│  │                                                                   │ │
│  │    ╔═══╗                                                          │ │
│  │    ║ T ║  ← D-Table-1200                                          │ │
│  │    ╚═══╝                                                          │ │
│  │                                                                   │ │
│  │         ┌───┐  ← Chair-01                                         │ │
│  │         │ C │                                                     │ │
│  │         └───┘                                                     │ │
│  │                                                                   │ │
│  │    ╔═══╗                                                          │ │
│  │    ║ T ║  ← D-Table-1200                                          │ │
│  │    ╚═══╝                                                          │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  📍 Selected: D-Table-1200                                              │
│  📍 Start Position: (12257.10, -862683.05)                             │
│  📍 Current Position: (13257.10, -862683.05)                           │
│  📍 Delta: (1000.0 mm, 0.0 mm) → Right                                │
│                                                                         │
│  [📥 Download Modified DXF]  [🔄 Reset]  [↩️ Undo Last Move]           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 💡 **ADVANTAGES OF THIS APPROACH**

1. **Visual Feedback** - See exactly what you're doing
2. **Intuitive Interface** - No need to type commands
3. **Precise Control** - Pixel-perfect placement
4. **Real-time Coordinates** - Know exact positions
5. **AI-Powered** - Automatic JSON updates
6. **Immediate Results** - Download instantly
7. **Error Prevention** - See conflicts before saving
8. **Professional** - Modern web-based tool

---

## 🔒 **CONSIDERATIONS**

### **Performance:**
- Large DXF files (>10MB) may be slow to render
- Consider pagination/viewport limiting for huge blueprints
- Use web workers for JSON processing

### **Accuracy:**
- Canvas coordinate system vs DXF coordinate system
- May need coordinate transformation/scaling
- Preserve Z-axis values (usually 0 for 2D)

### **User Experience:**
- Add zoom/pan controls
- Undo/redo functionality
- Multi-select for moving multiple fixtures
- Collision detection (optional)

### **Security:**
- File size limits
- File type validation
- Session management
- API key protection

---

## ✅ **READY TO BUILD?**

This architecture gives you:
- Clear separation of concerns
- Scalable structure
- Reusable components
- Professional workflow

**Let's start implementing! Which phase would you like to begin with?** 🚀
