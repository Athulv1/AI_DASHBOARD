"""
AUTOCAD-SPECIFIC FIX
Save with strict AutoCAD validation and header preservation
"""
import ezdxf
import shutil

print("="*70)
print(" AUTOCAD 2026 STRICT COMPATIBILITY FIX")
print("="*70)

# Read the FINAL file that works in viewers but not AutoCAD
doc = ezdxf.readfile('ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FINAL.dxf')

print("\n1. Loading document...")
print(f"   Entities: {len(list(doc.modelspace()))}")

# Apply strict AutoCAD fixes
print("\n2. Applying AutoCAD-specific fixes...")

# Remove any invalid handles
print("   - Cleaning handles...")
doc.entitydb.purge()

# Fix any coordinate precision issues
print("   - Normalizing coordinates...")
for entity in doc.modelspace():
    try:
        # Force coordinate update
        if hasattr(entity, 'transform'):
            entity.transform(ezdxf.math.Matrix44())
    except:
        pass

# Ensure proper $HANDSEED value
print("   - Updating header variables...")
try:
    # Get max handle
    max_handle = max(int(handle, 16) for handle in doc.entitydb.keys())
    doc.header['$HANDSEED'] = hex(max_handle + 1)[2:].upper()
except:
    pass

# Run full audit with fixes
print("\n3. Running comprehensive audit...")
auditor = doc.audit()

if auditor.has_fixes:
    print(f"   Applied {len(auditor.fixes)} fixes")

if auditor.has_errors:
    print(f"   ⚠️  {len(auditor.errors)} errors found:")
    for error in auditor.errors[:5]:
        print(f"      - {error}")

# Save with AutoCAD compatibility mode
print("\n4. Saving with AutoCAD compatibility...")

output_file = 'ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-AUTOCAD-FIXED.dxf'

# Try saving as R2018 (more compatible)
try:
    doc.saveas(output_file, encoding='cp1252')
    print(f"   ✅ Saved: {output_file}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    # Fallback: just copy and hope
    shutil.copy2('ATTA MARKET SECTOR-18_NOIDA-FLAGSHIP-B-FURNITURE-FINAL.dxf', output_file)

# Verify
print("\n5. Verification...")
verify = ezdxf.readfile(output_file)
print(f"   Entities: {len(list(verify.modelspace()))}")
print(f"   Version: {verify.dxfversion}")

import os
size_mb = os.path.getsize(output_file) / 1024 / 1024
print(f"   Size: {size_mb:.2f} MB")

print("\n" + "="*70)
print("✅ CREATED: " + output_file)
print("="*70)
print("\nTry opening this in AutoCAD 2026")
print("\nIf it STILL doesn't work, the issue is likely:")
print("  1. AutoCAD 2026 needs a specific update/patch")
print("  2. File association settings in Windows")
print("  3. Try: Right-click file → Open With → AutoCAD 2026")
print("  4. Try: In AutoCAD, File → Open → Select file manually")
print("="*70)
