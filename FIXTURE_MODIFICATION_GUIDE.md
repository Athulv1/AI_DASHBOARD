# 📖 How to Change Fixture Positions via JSON

## ✅ **YES! You can modify fixture positions in JSON and reconstruct the DXF!**

---

## 🔄 Complete Workflow:

### Step 1: Export DXF to FULL JSON (with all entity data)
```bash
# Edit enhanced_dxf_to_json.py to set your input file
python3 enhanced_dxf_to_json.py
```
This creates: `YOUR-FILE-COMPLETE.json` with **full entity data**

### Step 2: Modify Fixture Positions in JSON

Open the JSON file and find INSERT entities (these are fixtures):

```json
{
  "dxf_type": "INSERT",
  "name": "Chair",
  "insert": [35163.25, -1327568.76, 0.0],  ← Change these X, Y, Z values
  "xscale": 1.0,
  "yscale": 1.0,
  "rotation": 0.0,
  "layer": "FURNITURE",
  "color": 256
}
```

**What you can change:**
- `"insert": [X, Y, Z]` - Position of the fixture
- `"rotation": 0.0` - Rotation angle in degrees
- `"xscale": 1.0` - Scale in X direction
- `"yscale": 1.0` - Scale in Y direction
- `"layer": "FURNITURE"` - Which layer it's on

### Step 3: Reconstruct DXF from Modified JSON

Use the `json_to_dxf_r2018_mm.py` script:

```bash
python3 json_to_dxf_r2018_mm.py
```

This creates a **R2018 format DXF with MM units** that AutoCAD 2026 can open!

---

## 🎯 Example: Moving a Chair 1000mm to the right

**Original JSON:**
```json
{
  "dxf_type": "INSERT",
  "name": "Chair",
  "insert": [35163.25, -1327568.76, 0.0]
}
```

**Modified JSON (moved 1000mm in X):**
```json
{
  "dxf_type": "INSERT",
  "name": "Chair",
  "insert": [36163.25, -1327568.76, 0.0]  ← Changed X from 35163.25 to 36163.25
}
```

**Reconstruct** → The chair will be 1000mm to the right!

---

## 📊 What Entity Types You Can Modify:

| Entity Type | What You Can Change |
|-------------|---------------------|
| **INSERT** (fixtures) | Position, rotation, scale |
| **LINE** | Start point, end point |
| **CIRCLE** | Center position, radius |
| **LWPOLYLINE** | All vertex positions |
| **MTEXT** (text) | Position, content, height |
| **ARC** | Center, radius, angles |

---

## ⚠️ Important Notes:

1. **Always use the COMPLETE.json** file from `enhanced_dxf_to_json.py`
   - The `*-FULL.json` from `universal_dxf_converter.py` only has summary data

2. **Coordinates are in MM** (millimeters)
   - If you want to move 1 meter, change by 1000

3. **The reconstructed file will be in R2018 + MM format**
   - Ready for AutoCAD 2026!

4. **Dimensions won't be in the reconstruction**
   - Only geometry and fixtures
   - Use the hybrid method if you need dimensions

---

## 🚀 Quick Test:

```bash
# Already done in demo_fixture_modification.py
python3 demo_fixture_modification.py
```

This automatically:
1. Loads the JSON
2. Moves the first fixture +1000mm in X and Y
3. Saves modified JSON
4. Reconstructs DXF with R2018+MM
5. Verifies the change worked!

**Result:** `DEMO-MODIFIED-FIXTURE-R2018-MM.dxf` ✅

---

## 💡 Workflow Summary:

```
Original DXF
    ↓ (enhanced_dxf_to_json.py)
Full JSON with all entities
    ↓ (Edit in text editor)
Modified JSON (changed fixture positions)
    ↓ (json_to_dxf_r2018_mm.py)
New DXF with changed positions (R2018 + MM format)
    ↓
Open in AutoCAD 2026 ✅
```

---

## ✅ Confirmed Working!

The demonstration successfully:
- ✅ Changed fixture position in JSON (+1000mm X, +1000mm Y)
- ✅ Reconstructed DXF with R2018 format
- ✅ Set MM units (INSUNITS=4)
- ✅ Verified position changed correctly in final DXF

**You can now modify any fixture position in JSON and reconstruct!**
