#!/usr/bin/env python3
"""
Test Bounding Box Calculation
Demonstrates how X,Y points are extracted and connected to form bounding boxes
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, Arc, Polygon
import numpy as np

def visualize_block_bounding_box(block_name, block_data):
    """
    Visualize how bounding box is calculated from actual geometry
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Collect all points
    all_points = []
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    # Plot 1: Show actual geometry
    ax1.set_title(f'Actual Geometry: {block_name}', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    for entity in block_data.get('entities', []):
        entity_type = entity['dxf_type']
        
        if entity_type == 'LINE':
            start = entity['start'][:2]
            end = entity['end'][:2]
            ax1.plot([start[0], end[0]], [start[1], end[1]], 'b-', linewidth=1)
            all_points.extend([start, end])
            
            for x, y in [start, end]:
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)
        
        elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
            points = entity.get('points', [])
            if points:
                pts = np.array([p[:2] if len(p) > 2 else p for p in points])
                if entity.get('closed', False):
                    pts = np.vstack([pts, pts[0]])
                ax1.plot(pts[:, 0], pts[:, 1], 'g-', linewidth=1)
                all_points.extend(pts.tolist())
                
                for x, y in pts:
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)
        
        elif entity_type == 'CIRCLE':
            center = entity['center'][:2]
            radius = entity['radius']
            circle = Circle(center, radius, fill=False, color='red', linewidth=1)
            ax1.add_patch(circle)
            
            min_x = min(min_x, center[0] - radius)
            max_x = max(max_x, center[0] + radius)
            min_y = min(min_y, center[1] - radius)
            max_y = max(max_y, center[1] + radius)
            
            # Show extreme points
            ax1.plot([center[0] - radius, center[0] + radius], [center[1], center[1]], 'r--', alpha=0.3)
            ax1.plot([center[0], center[0]], [center[1] - radius, center[1] + radius], 'r--', alpha=0.3)
        
        elif entity_type == 'SPLINE':
            control_points = entity.get('control_points', [])
            fit_points = entity.get('fit_points', [])
            points = control_points if control_points else fit_points
            
            if points:
                pts = np.array([p[:2] if len(p) > 2 else p for p in points])
                ax1.plot(pts[:, 0], pts[:, 1], 'm-', linewidth=1, label='SPLINE')
                ax1.scatter(pts[:, 0], pts[:, 1], c='magenta', s=20, zorder=5)
                
                for x, y in pts:
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)
    
    # Plot 2: Show bounding box calculation
    ax2.set_title(f'Bounding Box Calculation', fontsize=14, fontweight='bold')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Draw the same geometry (lighter)
    for entity in block_data.get('entities', []):
        entity_type = entity['dxf_type']
        
        if entity_type == 'LINE':
            start, end = entity['start'][:2], entity['end'][:2]
            ax2.plot([start[0], end[0]], [start[1], end[1]], 'lightblue', linewidth=0.5, alpha=0.5)
        elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
            points = entity.get('points', [])
            if points:
                pts = np.array([p[:2] if len(p) > 2 else p for p in points])
                if entity.get('closed', False):
                    pts = np.vstack([pts, pts[0]])
                ax2.plot(pts[:, 0], pts[:, 1], 'lightgreen', linewidth=0.5, alpha=0.5)
        elif entity_type == 'CIRCLE':
            center, radius = entity['center'][:2], entity['radius']
            circle = Circle(center, radius, fill=False, color='pink', linewidth=0.5, alpha=0.5)
            ax2.add_patch(circle)
    
    # Draw bounding box
    if min_x != float('inf'):
        width = max_x - min_x
        height = max_y - min_y
        
        # Show corner points
        corners = [
            (min_x, min_y), (max_x, min_y),
            (max_x, max_y), (min_x, max_y)
        ]
        ax2.scatter([c[0] for c in corners], [c[1] for c in corners], 
                   c='red', s=100, zorder=10, marker='o', label='Corner Points')
        
        # Draw bounding box
        bbox = Rectangle((min_x, min_y), width, height, 
                        fill=False, edgecolor='red', linewidth=3, 
                        linestyle='--', label='Bounding Box')
        ax2.add_patch(bbox)
        
        # Add annotations
        ax2.text(min_x + width/2, max_y + height*0.05, 
                f'Width: {width:.1f} mm', 
                ha='center', fontsize=10, fontweight='bold', color='red')
        ax2.text(max_x + width*0.05, min_y + height/2, 
                f'Height: {height:.1f} mm', 
                ha='left', va='center', fontsize=10, fontweight='bold', color='red', rotation=90)
        
        # Show min/max lines
        ax2.axvline(min_x, color='orange', linestyle=':', alpha=0.5, label='min_x')
        ax2.axvline(max_x, color='orange', linestyle=':', alpha=0.5, label='max_x')
        ax2.axhline(min_y, color='purple', linestyle=':', alpha=0.5, label='min_y')
        ax2.axhline(max_y, color='purple', linestyle=':', alpha=0.5, label='max_y')
        
        ax2.legend(loc='upper right', fontsize=8)
    
    plt.tight_layout()
    return fig, (min_x, min_y, max_x, max_y, max_x - min_x, max_y - min_y)


def main():
    # Load the fixture analysis
    with open('image_F4bz1Dn_processed_W1BgANF_MODIFIED (1)_FIXTURE_ANALYSIS.json', 'r') as f:
        data = json.load(f)
    
    blocks = data['block_definitions']
    
    print("=" * 80)
    print("BOUNDING BOX VISUALIZATION TEST")
    print("=" * 80)
    print()
    
    # Test with first 3 blocks that have interesting geometry
    test_blocks = list(blocks.items())[:3]
    
    for block_name, block_data in test_blocks:
        print(f"\n📦 Block: {block_name}")
        print(f"   Reported size: {block_data['width']:.1f} × {block_data['height']:.1f} mm")
        
        # Check if it has the 'lines' structure (from analysis) or 'entities' structure (from DXF)
        if 'lines' in block_data:
            # Convert analysis format to entity format for visualization
            entities = []
            for line in block_data['lines']:
                if line['type'] == 'LINE':
                    entities.append({
                        'dxf_type': 'LINE',
                        'start': line['start'],
                        'end': line['end']
                    })
                elif line['type'] == 'LWPOLYLINE':
                    entities.append({
                        'dxf_type': 'LWPOLYLINE',
                        'points': line['points'],
                        'closed': line.get('closed', False)
                    })
                elif line['type'] == 'CIRCLE':
                    entities.append({
                        'dxf_type': 'CIRCLE',
                        'center': line.get('center', [0, 0, 0]),
                        'radius': line.get('radius', 0)
                    })
            
            block_data['entities'] = entities
        
        try:
            fig, bounds = visualize_block_bounding_box(block_name, block_data)
            min_x, min_y, max_x, max_y, width, height = bounds
            print(f"   Calculated bounds:")
            print(f"      X: {min_x:.2f} to {max_x:.2f} (width: {width:.2f} mm)")
            print(f"      Y: {min_y:.2f} to {max_y:.2f} (height: {height:.2f} mm)")
            
            # Save figure
            filename = f"bounding_box_{block_name.replace(' ', '_')}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"   ✅ Saved visualization: {filename}")
            plt.close()
        except Exception as e:
            print(f"   ❌ Error visualizing: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
The bounding box is calculated by:
1. Extracting ALL X,Y coordinates from each entity:
   - LINE: start and end points
   - POLYLINE: all vertex points
   - CIRCLE: center ± radius in both X and Y
   - ARC: center ± radius (could be improved for actual arc bounds)
   - SPLINE: control points or fit points

2. Finding extremes:
   - min_x = minimum X coordinate across all points
   - max_x = maximum X coordinate across all points
   - min_y = minimum Y coordinate across all points
   - max_y = maximum Y coordinate across all points

3. Calculating size:
   - width = max_x - min_x
   - height = max_y - min_y

This creates the tightest axis-aligned bounding box around the fixture!
""")


if __name__ == '__main__':
    main()
