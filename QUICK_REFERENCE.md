# 🚀 QUICK REFERENCE - Fixture Mover

## 3 Simple Steps:

### Step 1️⃣: Find Your Fixture
```bash
python3 find_fixtures.py YOUR-FILE.dxf
```
**OR** search for specific fixture:
```bash
python3 find_fixtures.py YOUR-FILE.dxf table
```

**Output example:**
```
📦 Block: "D-Table-1200"
   1. Position: X=12257.10, Y=-862683.05, Z=0.00
```

---

### Step 2️⃣: Edit modifications.json
Copy the EXACT block name and position:

```json
{
  "fixtures": [
    {
      "block_name": "D-Table-1200",
      "original_position": [12257.10, -862683.05],
      "new_position": [13257.10, -862683.05]
    }
  ]
}
```

**To move multiple fixtures**, add more entries:
```json
{
  "fixtures": [
    {
      "block_name": "D-Table-1200",
      "original_position": [12257.10, -862683.05],
      "new_position": [13257.10, -862683.05]
    },
    {
      "block_name": "Chair",
      "original_position": [35163.25, -1327568.76],
      "new_position": [36000.00, -1327568.76]
    }
  ]
}
```

---

### Step 3️⃣: Edit move_fixtures.py (lines 133-135)
```python
INPUT_DXF = 'YOUR-INPUT-FILE.dxf'
MODIFICATIONS_FILE = 'modifications.json'
OUTPUT_DXF = 'YOUR-OUTPUT-FILE.dxf'
```

**Then run:**
```bash
python3 move_fixtures.py
```

---

## 📐 Movement Cheat Sheet

| Direction | X Change | Y Change | Example |
|-----------|----------|----------|---------|
| **RIGHT** | +1000 | 0 | `[12257, -862683]` → `[13257, -862683]` |
| **LEFT** | -1000 | 0 | `[12257, -862683]` → `[11257, -862683]` |
| **UP** | 0 | +1000 | `[12257, -862683]` → `[12257, -861683]` |
| **DOWN** | 0 | -1000 | `[12257, -862683]` → `[12257, -863683]` |
| **DIAGONAL** | +1000 | +1000 | `[12257, -862683]` → `[13257, -861683]` |

**Note:** All values in millimeters (mm)

---

## ⚡ Quick Commands

### Find all fixtures:
```bash
python3 find_fixtures.py YOUR-FILE.dxf
```

### Find specific fixtures (tables, chairs, etc):
```bash
python3 find_fixtures.py YOUR-FILE.dxf table
python3 find_fixtures.py YOUR-FILE.dxf chair
python3 find_fixtures.py YOUR-FILE.dxf euro
```

### Move fixtures:
```bash
python3 move_fixtures.py
```

### Move with custom files:
```bash
python3 move_fixtures.py input.dxf output.dxf modifications.json
```

---

## ✅ Checklist

Before running `move_fixtures.py`:

- [ ] Found fixture position using `find_fixtures.py`
- [ ] Copied EXACT block name to `modifications.json`
- [ ] Copied EXACT position to `modifications.json`
- [ ] Calculated new position correctly
- [ ] Edited INPUT_DXF and OUTPUT_DXF in `move_fixtures.py`
- [ ] Saved all files

---

## 🆘 Common Errors

| Error | Solution |
|-------|----------|
| "Fixture not found" | Use `find_fixtures.py` to get EXACT position |
| "File not found" | Check file name spelling and path |
| "No changes made" | Check `modifications.json` has valid JSON |
| JSON syntax error | Use online JSON validator or check commas/brackets |

---

## 📞 Need Help?

1. **Run the finder first:**
   ```bash
   python3 find_fixtures.py YOUR-FILE.dxf
   ```

2. **Check your JSON syntax:**
   - Every `{` needs a matching `}`
   - Every `[` needs a matching `]`
   - Use commas between array items (but NOT after the last one)

3. **Test with ONE fixture first** before moving multiple

---

## 🎯 Pro Tips

✅ **Always keep a backup** of your original DXF file

✅ **Test with 1 fixture first** before moving many

✅ **Use descriptive output names** like `STORE-TABLES-MOVED.dxf`

✅ **Round positions to 2 decimals** (e.g., 12257.10, not 12257.1017262)

✅ **Check AutoCAD after each change** to verify movement

---

**Created with:** Python + ezdxf  
**Compatible with:** AutoCAD 2026 (R2018 format, MM units)
