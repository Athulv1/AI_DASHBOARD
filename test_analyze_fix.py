"""Test the analyze endpoint fix for EURO_CENTRE fixtures"""
import re

# Simulate the fixtures
fixtures = [
    {'name': 'EURO_CENTRE_1', 'x': 7354.17, 'y': -3065.74, 'rotation': 90.00},
    {'name': 'EURO_CENTRE_2', 'x': 7354.17, 'y': -2017.74, 'rotation': 90.00},
    {'name': 'EURO_CENTRE_3', 'x': 7354.17, 'y': -969.74, 'rotation': 90.00},
    {'name': 'EURO_CENTRE_4', 'x': 7354.17, 'y': 78.26, 'rotation': 90.00},
]

# Test commands
test_commands = [
    "Rotate EURO_CENTRE_2 by 45 degrees",
    "Rotate all EURO_CENTRE by 45 degrees",
    "Move EURO_CENTRE right by 1000mm",
]

for user_command in test_commands:
    print(f"\n🔍 Testing: '{user_command}'")
    print("=" * 60)
    
    # Pattern 1: Move/Rotate <fixture> <direction/action>
    fixture_name_pattern = r'(?:Move|move|Rotate|rotate)\s+([A-Za-z0-9\-_\s]+?)(?:\s+at|\s+right|\s+left|\s+up|\s+down|\s+by)'
    match = re.search(fixture_name_pattern, user_command)
    
    fixture_type = None
    # Pattern 2: If pattern 1 fails, try to get everything after Move/Rotate until prepositions
    if not match:
        fixture_name_pattern2 = r'(?:Move|move|Rotate|rotate)\s+(all\s+)?([A-Za-z0-9\-_]+)'
        match = re.search(fixture_name_pattern2, user_command)
        if match:
            match_groups = match.groups()
            fixture_type = match_groups[1] if len(match_groups) > 1 else match_groups[0]
    
    matching_fixtures = []
    
    if match:
        if not fixture_type:
            fixture_type = match.group(1).strip()
        else:
            fixture_type = fixture_type.strip()
        
        # Remove "all" prefix if present
        if fixture_type.lower().startswith('all '):
            fixture_type = fixture_type[4:].strip()
        
        print(f"  Extracted fixture type: '{fixture_type}'")
        
        # Find all matching fixtures - use smarter matching
        for f in fixtures:
            fixture_name = f['name']
            # Exact match
            if fixture_name.lower() == fixture_type.lower():
                matching_fixtures.append(f)
                print(f"  ✅ EXACT match: {fixture_name}")
            # Partial match (fixture_type is substring of fixture name)
            elif fixture_type.lower() in fixture_name.lower():
                matching_fixtures.append(f)
                print(f"  ✅ PARTIAL match: {fixture_name}")
            # Base name match (remove trailing numbers/underscores)
            else:
                # Extract base name: EURO_CENTRE_2 -> EURO_CENTRE
                base_fixture = re.sub(r'_\d+$', '', fixture_name)
                base_search = re.sub(r'_\d+$', '', fixture_type)
                if base_fixture.lower() == base_search.lower():
                    matching_fixtures.append(f)
                    print(f"  ✅ BASE match: {fixture_name} (base: {base_fixture})")
    
    # Check for "all"
    if 'all' in user_command.lower() and fixture_type:
        print(f"\n  'all' keyword detected, finding all {fixture_type} fixtures")
    
    print(f"\n  📊 Total matches: {len(matching_fixtures)}")
    print(f"  🎯 Needs selection: {len(matching_fixtures) > 1 and 'all' not in user_command.lower()}")
    
    for i, f in enumerate(matching_fixtures, 1):
        print(f"    {i}. {f['name']}")
