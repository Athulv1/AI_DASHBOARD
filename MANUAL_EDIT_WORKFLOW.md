# 📝 Manual Workflow: Delete a Fixture from JSON and Rebuild

## Step-by-Step Instructions:

### **Step 1: Export DXF to JSON**

Run this command:
```bash
python3 enhanced_dxf_to_json.py
```

**Output:** `ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE.json`

---

### **Step 2: Manually Edit the JSON**

1. Open the JSON file in any text editor (VS Code, Notepad++, etc.)

2. Search for a fixture block name, for example: `"awefqwf"` or `"Chair"`

3. You'll find something like this:
```json
{
  "dxf_type": "INSERT",
  "layer": "dimensions",
  "color": 3,
  "linetype": "BYLAYER",
  "name": "awefqwf",        ← This is the block name
  "insert": [
    21813.88630240032,      ← X position
    -858363.0549321924,     ← Y position
    0.0                     ← Z position
  ],
  "xscale": 1,
  "yscale": 1,
  "zscale": 1,
  "rotation": 0
}
```

4. **To DELETE this fixture:**
   - Select the entire JSON object (from opening `{` to closing `}`)
   - Delete it
   - **Don't forget** to remove the comma before or after (to keep valid JSON)

5. **Save the file as:**
   `ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE-MODIFIED.json`

---

### **Step 3: Rebuild DXF from Modified JSON**

Run this command:
```bash
python3 autocad_method_reconstruction.py
```

**Output:** `ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-COMPLETE-MODIFIED-R2018-MM.dxf`

This file will have:
- ✅ The fixture you deleted REMOVED
- ✅ All other fixtures in their original positions
- ✅ All dimensions preserved
- ✅ R2018 format + MM units
- ✅ Ready for AutoCAD 2026!

---

## 📦 Available Fixtures to Delete:

Here are all 59 fixtures in the file (you can delete any of these):

1. **awefqwf** at X=21813.89, Y=-858363.05
2. **Chair** at X=35163.25, Y=-1327568.76
3. **D-Table-1200** at X=12257.10, Y=-862683.05
4. **D-Table-1200** at X=14657.10, Y=-862683.05
5. **D-Table-1200** at X=9857.10, Y=-860828.57
... (and 54 more)

---

## ✏️ Example: Delete "awefqwf" Fixture

**Before (in JSON):**
```json
{
  "dxf_type": "INSERT",
  "name": "awefqwf",
  "insert": [21813.89, -858363.05, 0.0],
  ...
},
{
  "dxf_type": "LWPOLYLINE",
  ...
}
```

**After (deleted):**
```json
{
  "dxf_type": "LWPOLYLINE",
  ...
}
```

**Result:** The "awefqwf" fixture will NOT appear in the rebuilt DXF! ✅

---

## 🔍 How to Verify:

After running Step 3, check the output:

```
✅ Saved: ATTA-...-MODIFIED-R2018-MM.dxf
   Entities: 316 (was 317)  ← One less entity!
   INSERT entities: 58 (was 59)  ← One less fixture!
```

Open in AutoCAD 2026 - the deleted fixture will be missing! ✅

---

## 💡 Tips:

- **JSON syntax:** Make sure commas are correct after deletion
- **Backup:** Keep the original JSON file
- **Multiple deletes:** You can delete multiple INSERT entities at once
- **Position changes:** Instead of deleting, you can change the `"insert"` coordinates to move fixtures

---

## 🚀 Quick Reference:

| Step | Command | File |
|------|---------|------|
| 1. Export | `python3 enhanced_dxf_to_json.py` | Creates COMPLETE.json |
| 2. Edit | Manual editing | Save as MODIFIED.json |
| 3. Rebuild | `python3 autocad_method_reconstruction.py` | Creates R2018-MM.dxf |

**All done! Your modified DXF is ready for AutoCAD 2026!** ✅
