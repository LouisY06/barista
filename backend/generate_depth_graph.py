#!/usr/bin/env python3
"""
Generate depth graph from stereo cameras using feature matching.
Works with current camera setup without requiring pre-calibration.
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path

def capture_stereo_images(cam_left=0, cam_right=1):
    """Capture images from two cameras."""
    print(f"Capturing from cameras {cam_left} and {cam_right}...")
    
    cap_left = cv2.VideoCapture(cam_left)
    cap_right = cv2.VideoCapture(cam_right)
    
    if not cap_left.isOpened() or not cap_right.isOpened():
        print("Error: Could not open cameras")
        return None, None
    
    # Warm up cameras
    for _ in range(5):
        cap_left.read()
        cap_right.read()
    
    ret_left, img_left = cap_left.read()
    ret_right, img_right = cap_right.read()
    
    cap_left.release()
    cap_right.release()
    
    if not ret_left or not ret_right:
        return None, None
    
    print(f"✓ Captured images: {img_left.shape}")
    return img_left, img_right


def detect_and_match_features(img1, img2, max_features=10000):
    """Detect and match features between two images."""
    print("Detecting features with SIFT...")
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # CLAHE for better feature detection
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray1 = clahe.apply(gray1)
    gray2 = clahe.apply(gray2)
    
    # Detect features
    sift = cv2.SIFT_create(nfeatures=max_features)
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)
    
    print(f"Found {len(kp1)} keypoints in image 1")
    print(f"Found {len(kp2)} keypoints in image 2")
    
    # Match features
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    matches = bf.knnMatch(des1, des2, k=2)
    
    # Lowe's ratio test
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)
    
    print(f"Found {len(good_matches)} good matches")
    
    return kp1, kp2, good_matches


def estimate_depth_from_features(img1, img2, kp1, kp2, matches, baseline_estimate=100):
    """
    Estimate depth using triangulation from Camera 0's viewpoint.
    
    The 3D point cloud is generated in Camera 0's coordinate system:
    - Origin: Camera 0's optical center
    - Z-axis: Points away from camera (into the scene)
    - Larger Z = farther from camera
    
    Args:
        baseline_estimate: Approximate distance between cameras in mm
                          (Measure this physically for accurate depth!)
    """
    if len(matches) < 8:
        print("Not enough matches for depth estimation")
        return None, None
    
    # Extract matched points
    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])
    
    # Estimate fundamental matrix
    F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 3.0, 0.99)
    
    if F is None:
        print("Could not estimate fundamental matrix")
        return None, None
    
    # Filter matches using mask
    pts1 = pts1[mask.ravel() == 1]
    pts2 = pts2[mask.ravel() == 1]
    matches_filtered = [m for i, m in enumerate(matches) if mask[i]]
    
    print(f"After RANSAC: {len(pts1)} inlier matches")
    
    # Compute disparity (horizontal difference between matched points)
    disparity = np.abs(pts1[:, 0] - pts2[:, 0])
    
    # Estimate camera intrinsics (approximate)
    h, w = img1.shape[:2]
    focal_length = w * 0.7  # Approximate focal length
    
    # Simple depth estimation: depth = (baseline * focal_length) / disparity
    # Filter out very small disparities
    valid_mask = disparity > 1.0
    pts1_valid = pts1[valid_mask]
    pts2_valid = pts2[valid_mask]
    disparity_valid = disparity[valid_mask]
    
    depth = (baseline_estimate * focal_length) / (disparity_valid + 1e-6)
    
    # Create 3D points (image coordinates + depth)
    points_3d = np.zeros((len(pts1_valid), 3))
    points_3d[:, 0] = pts1_valid[:, 0] - w/2  # X (centered)
    points_3d[:, 1] = pts1_valid[:, 1] - h/2  # Y (centered)
    points_3d[:, 2] = depth  # Z (depth)
    
    print(f"Generated {len(points_3d)} 3D points")
    print(f"Depth range: {depth.min():.1f} to {depth.max():.1f} mm")
    
    return points_3d, pts1_valid


def create_depth_visualization(img1, img2, points_3d, pts_2d, output_file='depth_graph.png'):
    """Create comprehensive depth visualization."""
    
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Original images
    ax1 = fig.add_subplot(2, 4, 1)
    ax1.imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    ax1.set_title('Camera 0 (Left View)')
    ax1.axis('off')
    
    ax2 = fig.add_subplot(2, 4, 2)
    ax2.imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    ax2.set_title('Camera 1 (Right View)')
    ax2.axis('off')
    
    # 2. Depth overlay on image
    ax3 = fig.add_subplot(2, 4, 3)
    ax3.imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    
    # Create depth-colored overlay
    depths = points_3d[:, 2]
    depth_normalized = (depths - depths.min()) / (depths.max() - depths.min() + 1e-6)
    
    scatter = ax3.scatter(pts_2d[:, 0], pts_2d[:, 1], 
                          c=depths, cmap='jet', s=50, alpha=0.6, edgecolors='white', linewidth=0.5)
    ax3.set_title('Depth Overlay\n(Blue=Close, Red=Far)')
    ax3.axis('off')
    plt.colorbar(scatter, ax=ax3, label='Depth (mm)', fraction=0.046)
    
    # 3. Depth histogram
    ax4 = fig.add_subplot(2, 4, 4)
    ax4.hist(depths, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    ax4.axvline(np.median(depths), color='red', linestyle='--', linewidth=2, label=f'Median: {np.median(depths):.1f}mm')
    ax4.set_xlabel('Distance from Camera (mm)')
    ax4.set_ylabel('Number of Points')
    ax4.set_title('Distance Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 4. Top-down view (X-Z)
    ax5 = fig.add_subplot(2, 4, 5)
    scatter2 = ax5.scatter(points_3d[:, 0], points_3d[:, 2], 
                           c=depths, cmap='jet', s=5, alpha=0.5)
    ax5.set_xlabel('X Position (pixels from center)')
    ax5.set_ylabel('Depth from Camera 0 (mm)')
    ax5.set_title('Top-Down View (Bird\'s Eye)\nViewed from Camera 0')
    ax5.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='Camera position')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)
    plt.colorbar(scatter2, ax=ax5, label='Depth (mm)')
    
    # 5. Side view (Y-Z)
    ax6 = fig.add_subplot(2, 4, 6)
    scatter3 = ax6.scatter(points_3d[:, 1], points_3d[:, 2], 
                           c=depths, cmap='jet', s=5, alpha=0.5)
    ax6.set_xlabel('Y Position (pixels from center)')
    ax6.set_ylabel('Depth from Camera 0 (mm)')
    ax6.set_title('Side View\nViewed from Camera 0')
    ax6.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='Camera position')
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3)
    plt.colorbar(scatter3, ax=ax6, label='Depth (mm)')
    
    # 6. 3D scatter plot
    ax7 = fig.add_subplot(2, 4, 7, projection='3d')
    # Subsample for cleaner 3D view
    subsample_idx = np.random.choice(len(points_3d), min(1000, len(points_3d)), replace=False)
    points_sub = points_3d[subsample_idx]
    depths_sub = depths[subsample_idx]
    
    scatter4 = ax7.scatter(points_sub[:, 0], points_sub[:, 1], points_sub[:, 2],
                           c=depths_sub, cmap='jet', s=10, alpha=0.6)
    ax7.set_xlabel('X (pixels)')
    ax7.set_ylabel('Y (pixels)')
    ax7.set_zlabel('Depth (mm)')
    ax7.set_title('3D Point Cloud\n(Camera 0 Coordinate System)')
    plt.colorbar(scatter4, ax=ax7, shrink=0.5, label='Depth (mm)')
    
    # 7. Depth statistics
    ax8 = fig.add_subplot(2, 4, 8)
    ax8.axis('off')
    
    stats_text = f"""
DEPTH STATISTICS
═══════════════════════════
Coordinate System:
  Origin: Camera 0 optical center
  Z-axis: Into the scene
  Blue: Close | Red: Far

Total 3D Points: {len(points_3d):,}

Depth Range (from Camera 0):
  Min: {depths.min():.1f} mm ({depths.min()/10:.1f} cm)
  Max: {depths.max():.1f} mm ({depths.max()/10:.1f} cm)
  Range: {depths.max() - depths.min():.1f} mm

Central Tendency:
  Mean: {depths.mean():.1f} mm
  Median: {np.median(depths):.1f} mm
  Std Dev: {depths.std():.1f} mm

Percentiles:
  25th: {np.percentile(depths, 25):.1f} mm
  50th: {np.percentile(depths, 50):.1f} mm
  75th: {np.percentile(depths, 75):.1f} mm
  95th: {np.percentile(depths, 95):.1f} mm

⚠ CALIBRATION NOTE:
Depth accuracy depends on baseline!
Current: 100mm estimate
Measure actual camera separation
and adjust baseline_estimate in code.
    """
    
    ax8.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    ax8.set_title('Statistics', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved depth visualization to: {output_file}")
    plt.close(fig)


def main():
    print("=" * 70)
    print("STEREO DEPTH GRAPH GENERATOR")
    print("=" * 70)
    
    # 1. Capture stereo images
    print("\n[1/4] Capturing stereo images...")
    img_left, img_right = capture_stereo_images(cam_left=0, cam_right=1)
    
    if img_left is None or img_right is None:
        print("❌ Failed to capture images")
        return
    
    # Save captured images
    cv2.imwrite('captured_left.jpg', img_left)
    cv2.imwrite('captured_right.jpg', img_right)
    print("Saved captured_left.jpg and captured_right.jpg")
    
    # 2. Detect and match features
    print("\n[2/4] Detecting and matching features...")
    kp1, kp2, matches = detect_and_match_features(img_left, img_right)
    
    if len(matches) < 8:
        print("❌ Not enough feature matches found")
        print("\n💡 Try these improvements:")
        print("  1. Improve lighting - add more light to the scene")
        print("  2. Increase texture - add objects with patterns/details")
        print("  3. Reduce motion blur - ensure cameras are stable")
        print("  4. Position cameras closer together with more overlap")
        return
    
    # Warning for low match count
    if len(matches) < 20:
        print(f"\n⚠️  WARNING: Only {len(matches)} feature matches found")
        print("   This will result in a SPARSE depth map with few 3D points.")
        print("\n💡 TO IMPROVE DEPTH MAP QUALITY:")
        print("   1. 💡 Adjust lighting - ensure scene is well-lit and evenly illuminated")
        print("   2. 💡 Avoid overexposure or dark shadows")
        print("   3. Add more textured objects to the scene")
        print("   4. Ensure good overlap between camera views")
        print("   5. Check that both cameras are in focus")
        print("\n   Continuing with current matches...\n")
    
    # 3. Estimate depth
    print("\n[3/4] Estimating depth from stereo matching...")
    print("Note: Using approximate baseline of 100mm (adjust if needed)")
    points_3d, pts_2d = estimate_depth_from_features(
        img_left, img_right, kp1, kp2, matches, baseline_estimate=100
    )
    
    if points_3d is None or len(points_3d) == 0:
        print("❌ Failed to estimate depth")
        return
    
    # 4. Create visualization
    print("\n[4/4] Creating depth visualization...")
    create_depth_visualization(img_left, img_right, points_3d, pts_2d)
    
    print("\n" + "=" * 70)
    print("✅ DEPTH GRAPH GENERATION COMPLETE!")
    print("=" * 70)
    print("\nOutput files:")
    print("  - depth_graph.png (main visualization)")
    print("  - captured_left.jpg (left camera view)")
    print("  - captured_right.jpg (right camera view)")
    
    # Print summary
    depths = points_3d[:, 2]
    print(f"\n📊 Depth Summary (from Camera 0's viewpoint):")
    print(f"  3D Points: {len(points_3d):,}")
    print(f"  Depth Range: {depths.min():.1f} - {depths.max():.1f} mm ({depths.min()/10:.1f} - {depths.max()/10:.1f} cm)")
    print(f"  Median Depth: {np.median(depths):.1f} mm ({np.median(depths)/10:.1f} cm)")
    
    print(f"\n📏 HOW TO VERIFY DEPTH ACCURACY:")
    print(f"  1. Measure the physical distance between your two cameras (center to center)")
    print(f"  2. Edit this script and set baseline_estimate to that value in mm")
    print(f"  3. Place a known object at a known distance from Camera 0")
    print(f"  4. Compare the measured depth to the actual distance")
    print(f"  5. Adjust baseline_estimate until depths match reality")
    print(f"\n  Current baseline: 100mm (ESTIMATED - measure yours!)")
    print(f"\n  Example: If cameras are 150mm apart, change line 310 to:")
    print(f"           baseline_estimate=150")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

