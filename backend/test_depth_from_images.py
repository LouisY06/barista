#!/usr/bin/env python3
"""
Test comprehensive depth mapping on provided images.
"""

import cv2
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_comprehensive_depth import (
    compute_dense_disparity,
    disparity_to_depth,
    create_3d_point_cloud,
    detect_surfaces,
    create_comprehensive_visualization
)

def main():
    print("=" * 70)
    print("TESTING DEPTH ALGORITHM ON PROVIDED IMAGES")
    print("=" * 70)
    
    # Load the two images from the user
    print("\nLoading images...")
    
    # Try to load user-provided images, fall back to most recent captures
    img_left = cv2.imread('test_image_left.jpg')
    img_right = cv2.imread('test_image_right.jpg')
    
    if img_left is None or img_right is None:
        print("No test images found, using most recent captured images...")
        img_left = cv2.imread('captured_left.jpg')
        img_right = cv2.imread('captured_right.jpg')
    
    if img_left is None or img_right is None:
        print("❌ Could not load test images")
        print("Please ensure test_image_left.jpg and test_image_right.jpg exist")
        return
    
    print(f"✓ Loaded images: {img_left.shape}")
    
    # Run the comprehensive depth algorithm
    print("\n[1/4] Computing dense disparity...")
    disparity = compute_dense_disparity(img_left, img_right)
    
    valid_pixels = np.sum(disparity > 0)
    total_pixels = disparity.shape[0] * disparity.shape[1]
    print(f"Coverage: {100*valid_pixels/total_pixels:.1f}%")
    
    print("\n[2/4] Converting disparity to depth...")
    depth_map = disparity_to_depth(disparity, baseline_mm=100, img_width=img_left.shape[1])
    
    valid_depths = depth_map[depth_map > 0]
    if len(valid_depths) == 0:
        print("❌ No valid depth computed")
        return
    
    print(f"✓ Depth range: {valid_depths.min():.1f} to {valid_depths.max():.1f} mm")
    
    print("\n[3/4] Creating 3D point cloud...")
    points_3d, colors = create_3d_point_cloud(depth_map, img_left, subsample=3)
    
    print("\n[4/4] Detecting surfaces...")
    surfaces, surface_labels = detect_surfaces(points_3d, colors)
    
    print("\nCreating visualization...")
    create_comprehensive_visualization(
        img_left, img_right, depth_map, points_3d, colors, surfaces, surface_labels
    )
    
    print("\n" + "=" * 70)
    print("✅ DEPTH ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  Dense coverage: {100*len(valid_depths)/depth_map.size:.1f}%")
    print(f"  3D points: {len(points_3d):,}")
    print(f"  Surfaces: {len(surfaces) if surfaces else 0}")
    print(f"  Depth range: {valid_depths.min():.1f} - {valid_depths.max():.1f} mm")
    print(f"  Median depth: {np.median(valid_depths):.1f} mm ({np.median(valid_depths)/10:.1f} cm)")
    
    print("\n📊 Output: comprehensive_depth_graph.png")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

