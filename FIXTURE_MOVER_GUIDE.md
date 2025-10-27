# 🔧 Universal Fixture Mover for DXF Files

## 📋 Quick Start Guide

### What You Need:
1. ✅ `move_fixtures.py` - The Python script (already created)
2. ✅ `modifications.json` - Your fixture movement instructions (edit manually)
3. ✅ Your DXF file

---

## 🚀 How to Use

### Method 1: Simple (Recommended)

1. **Edit the script** `move_fixtures.py` (lines 133-135):
   ```python
   INPUT_DXF = 'YOUR-FILE.dxf'           # Your input DXF file name
   MODIFICATIONS_FILE = 'modifications.json'  # Keep this as is
   OUTPUT_DXF = 'YOUR-FILE-MODIFIED.dxf'     # Your output file name
   ```

2. **Edit `modifications.json`** with fixtures you want to move:
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

3. **Run the script:**
   ```bash
   python3 move_fixtures.py
   ```

### Method 2: Command Line

```bash
python3 move_fixtures.py input.dxf output.dxf modifications.json
```

---

## 📝 How to Edit modifications.json

### Step 1: Find the Fixture Position

Run this command to find fixture names and positions:

```bash
python3 -c "
import ezdxf

doc = ezdxf.readfile('YOUR-FILE.dxf')
msp = doc.modelspace()

print('All fixtures in your DXF:\n')
for entity in msp:
    if entity.dxftype() == 'INSERT':
        pos = entity.dxf.insert
        print(f'Block: \"{entity.dxf.name}\"')
        print(f'   Position: X={pos.x:.2f}, Y={pos.y:.2f}\n')
"
```

### Step 2: Create Your Modification

Copy the EXACT block name and position into `modifications.json`:

```json
{
  "fixtures": [
    {
      "block_name": "EXACT-BLOCK-NAME-HERE",
      "original_position": [X-VALUE, Y-VALUE],
      "new_position": [NEW-X-VALUE, NEW-Y-VALUE]
    }
  ]
}
```

### Step 3: Add More Fixtures (Optional)

To move multiple fixtures, add more objects to the array:

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
    },
    {
      "block_name": "Euro Centre",
      "original_position": [23169.29, -860603.05],
      "new_position": [24000.00, -860603.05]
    }
  ]
}
```

---

## 📐 Understanding Positions

### DXF Coordinate System:
- **X-axis**: Horizontal (left ← → right)
  - Increase X = Move RIGHT
  - Decrease X = Move LEFT
  
- **Y-axis**: Vertical (down ↓ ↑ up)
  - Increase Y = Move UP (less negative)
  - Decrease Y = Move DOWN (more negative)

### Example Movements:

```json
// Move 1000mm to the RIGHT
"original_position": [12257.10, -862683.05],
"new_position": [13257.10, -862683.05]  // X increased by 1000

// Move 2000mm to the LEFT
"original_position": [12257.10, -862683.05],
"new_position": [10257.10, -862683.05]  // X decreased by 2000

// Move 1500mm UP
"original_position": [12257.10, -862683.05],
"new_position": [12257.10, -861183.05]  // Y increased by 1500

// Move 1500mm DOWN
"original_position": [12257.10, -862683.05],
"new_position": [12257.10, -864183.05]  // Y decreased by 1500

// Move DIAGONALLY (right + up)
"original_position": [12257.10, -862683.05],
"new_position": [13257.10, -861683.05]  // X+1000, Y+1000
```

---

## ✅ Complete Example Workflow

### 1. Find Your Fixture
```bash
python3 -c "
import ezdxf
doc = ezdxf.readfile('MYSTORE.dxf')
for e in doc.modelspace():
    if e.dxftype() == 'INSERT' and 'table' in e.dxf.name.lower():
        print(f'{e.dxf.name} at X={e.dxf.insert.x:.2f}, Y={e.dxf.insert.y:.2f}')
"
```

Output:
```
D-Table-1200 at X=12257.10, Y=-862683.05
```

### 2. Edit modifications.json
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

### 3. Edit move_fixtures.py (lines 133-135)
```python
INPUT_DXF = 'MYSTORE.dxf'
MODIFICATIONS_FILE = 'modifications.json'
OUTPUT_DXF = 'MYSTORE-MODIFIED.dxf'
```

### 4. Run
```bash
python3 move_fixtures.py
```

### 5. Result
```
✅ SUCCESS! Fixtures moved successfully
✅ DONE! You can now open 'MYSTORE-MODIFIED.dxf' in AutoCAD 2026
```

---

## 🎯 Tips & Tricks

### ✅ DO:
- Copy EXACT block names (case-sensitive)
- Use positions with 2 decimal places (e.g., 12257.10)
- Test with ONE fixture first before moving multiple
- Keep backup of original DXF file
- Use descriptive output file names

### ❌ DON'T:
- Change block names (must match exactly)
- Guess positions (use the finder script)
- Edit the DXF file while script is running
- Forget to save modifications.json before running

---

## 🔧 Troubleshooting

### Problem: "Fixture not found"
**Solution:** 
- Use the finder script to get EXACT position
- Make sure block name matches exactly (case-sensitive)
- Check position has correct decimal values

### Problem: "File not found"
**Solution:**
- Check file name spelling
- Make sure you're in the correct directory
- Use full file path if needed

### Problem: "No changes made"
**Solution:**
- Check modifications.json has fixtures array
- Verify JSON syntax is correct (commas, brackets)
- Make sure file has at least one fixture entry

---

## 📁 File Structure

```
your-project/
├── move_fixtures.py           ← The Python script (DO NOT EDIT usually)
├── modifications.json         ← Edit this to move fixtures
├── YOUR-INPUT-FILE.dxf       ← Your original DXF
└── YOUR-OUTPUT-FILE.dxf      ← Generated after running script
```

---

## 🎓 Advanced Usage

### Move ALL fixtures of a specific type:

1. Find all fixtures:
```bash
python3 -c "
import ezdxf
doc = ezdxf.readfile('YOUR-FILE.dxf')
for e in doc.modelspace():
    if e.dxftype() == 'INSERT' and e.dxf.name == 'Chair':
        print(f'[\"{e.dxf.name}\", [{e.dxf.insert.x}, {e.dxf.insert.y}]],')
"
```

2. Copy output to modifications.json and add new positions manually

---

## 📞 Support

For issues or questions:
1. Check your modifications.json syntax
2. Verify file paths are correct
3. Run the finder script to confirm fixture exists
4. Check that ezdxf is installed: `pip3 install ezdxf`

---

## 📜 License

Free to use for any project. Modify as needed.

**Created by:** GitHub Copilot  
**Version:** 1.0  
**Compatible with:** AutoCAD 2026, ezdxf 1.4.2+
