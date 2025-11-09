#!/usr/bin/env python3
"""
Run comprehensive depth analysis on user-provided images.
Usage: python run_depth_on_images.py <left_image.jpg> <right_image.jpg>
"""

import cv2
import numpy as np
import sys
import os

# Add current directory to path
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
    print("DEPTH ANALYSIS ON USER-PROVIDED IMAGES")
    print("=" * 70)
    
    # Get image paths from command line arguments or use defaults
    if len(sys.argv) >= 3:
        img_left_path = sys.argv[1]
        img_right_path = sys.argv[2]
    else:
        # Try common locations - prioritize test_image_left/right
        possible_left = [
            'test_image_left.jpg',  # Primary name
            'test_image_left.jpeg',  # JPEG variant
            'user_image_left.jpg',
            'left.jpg',
            'image1.jpg',
            'uploads/left.jpg',
            'uploads/image1.jpg'
        ]
        possible_right = [
            'test_image_right.jpg',  # Primary name
            'test_image_right.jpeg',  # JPEG variant
            'user_image_right.jpg',
            'right.jpg',
            'image2.jpg',
            'uploads/right.jpg',
            'uploads/image2.jpg'
        ]
        
        img_left_path = None
        img_right_path = None
        
        for path in possible_left:
            if os.path.exists(path):
                img_left_path = path
                break
        
        for path in possible_right:
            if os.path.exists(path):
                img_right_path = path
                break
        
        if not img_left_path or not img_right_path:
            print("\n❌ Could not find image files!")
            print("\n📸 Please save your uploaded images as:")
            print("  1. test_image_left.jpg  (first image)")
            print("  2. test_image_right.jpg (second image)")
            print("\nThen run: python run_depth_on_images.py")
            print("\nOr specify paths directly:")
            print("  python run_depth_on_images.py <left.jpg> <right.jpg>")
            return
    
    print(f"\nLoading images...")
    print(f"  Left:  {img_left_path}")
    print(f"  Right: {img_right_path}")
    
    img_left = cv2.imread(img_left_path)
    img_right = cv2.imread(img_right_path)
    
    if img_left is None:
        print(f"❌ Could not load left image: {img_left_path}")
        return
    
    if img_right is None:
        print(f"❌ Could not load right image: {img_right_path}")
        return
    
    print(f"✓ Loaded images: {img_left.shape}")
    
    # Save copies for reference
    cv2.imwrite('captured_left.jpg', img_left)
    cv2.imwrite('captured_right.jpg', img_right)
    print("Saved copies as captured_left.jpg and captured_right.jpg")
    
    # Run comprehensive depth analysis
    print("\n[1/4] Computing dense disparity...")
    disparity = compute_dense_disparity(img_left, img_right)
    
    valid_pixels = np.sum(disparity > 0)
    total_pixels = disparity.shape[0] * disparity.shape[1]
    print(f"Coverage: {100*valid_pixels/total_pixels:.1f}%")
    
    if valid_pixels < 1000:
        print("\n⚠️  WARNING: Very few valid depth pixels!")
        print("💡 This might mean:")
        print("   - Images are from very different viewpoints")
        print("   - Not enough texture/features for matching")
        print("   - Lighting issues")
        print("\nContinuing anyway...")
    
    print("\n[2/4] Converting disparity to depth...")
    depth_map = disparity_to_depth(disparity, baseline_mm=100, img_width=img_left.shape[1])
    
    valid_depths = depth_map[depth_map > 0]
    if len(valid_depths) == 0:
        print("❌ No valid depth computed")
        return
    
    print(f"✓ Depth range: {valid_depths.min():.1f} to {valid_depths.max():.1f} mm")
    print(f"  Median depth: {np.median(valid_depths):.1f} mm ({np.median(valid_depths)/10:.1f} cm)")
    
    print("\n[3/4] Creating 3D point cloud...")
    points_3d, colors = create_3d_point_cloud(depth_map, img_left, subsample=3)
    
    print("\n[4/4] Detecting surfaces...")
    surfaces, surface_labels = detect_surfaces(points_3d, colors)
    
    print("\nCreating comprehensive visualization...")
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
    print("📁 Source images saved as: captured_left.jpg, captured_right.jpg")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

