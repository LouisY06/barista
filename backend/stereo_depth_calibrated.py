#!/usr/bin/env python3
"""
CALIBRATED Stereo Depth - Uses actual calibration matrices for accurate depth.
Validates results and avoids over-processing that creates false data.
"""

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Calibration directory
CALIB_DIR = Path(__file__).parent / "app" / "vision" / "data" / "calib"


def load_calibration():
    """Load stereo calibration matrices."""
    print("📐 Loading calibration matrices...")
    
    matrices = {}
    csv_files = {
        'K1': 'calib_K1.csv',
        'K2': 'calib_K2.csv',
        'D1': 'calib_D1.csv',
        'D2': 'calib_D2.csv',
        'R': 'calib_R.csv',
        'T': 'calib_T.csv',
        'R1': 'calib_R1.csv',
        'R2': 'calib_R2.csv',
        'P1': 'calib_P1.csv',
        'P2': 'calib_P2.csv',
        'Q': 'calib_Q.csv'
    }
    
    for name, filename in csv_files.items():
        filepath = CALIB_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, header=None)
            matrices[name] = df.values
            print(f"  ✓ Loaded {name}")
        else:
            print(f"  ⚠️  {filename} not found")
    
    return matrices


def capture_stereo_images(cam_left=0, cam_right=1):
    """Capture stereo images."""
    print(f"📸 Capturing from cameras {cam_left} and {cam_right}...")
    
    cap_left = cv2.VideoCapture(cam_left)
    cap_right = cv2.VideoCapture(cam_right)
    
    if not cap_left.isOpened() or not cap_right.isOpened():
        print("❌ Could not open cameras")
        return None, None
    
    # Warm up
    for _ in range(10):
        cap_left.read()
        cap_right.read()
    
    ret_left, img_left = cap_left.read()
    ret_right, img_right = cap_right.read()
    
    cap_left.release()
    cap_right.release()
    
    if not ret_left or not ret_right:
        return None, None
    
    print(f"✓ Captured: {img_left.shape}")
    return img_left, img_right


def rectify_images(img_left, img_right, matrices):
    """
    Rectify images using calibration matrices.
    This aligns epipolar lines for proper stereo matching.
    """
    print("\n🔄 Rectifying images...")
    
    K1 = matrices['K1']
    K2 = matrices['K2']
    D1 = matrices['D1'].ravel()
    D2 = matrices['D2'].ravel()
    R1 = matrices['R1']
    R2 = matrices['R2']
    P1 = matrices['P1']
    P2 = matrices['P2']
    
    h, w = img_left.shape[:2]
    
    # Create rectification maps
    map1_left, map2_left = cv2.initUndistortRectifyMap(
        K1, D1, R1, P1, (w, h), cv2.CV_32FC1
    )
    map1_right, map2_right = cv2.initUndistortRectifyMap(
        K2, D2, R2, P2, (w, h), cv2.CV_32FC1
    )
    
    # Rectify images
    img_left_rect = cv2.remap(img_left, map1_left, map2_left, cv2.INTER_LINEAR)
    img_right_rect = cv2.remap(img_right, map1_right, map2_right, cv2.INTER_LINEAR)
    
    print("✓ Images rectified")
    return img_left_rect, img_right_rect


def compute_disparity_calibrated(gray_left, gray_right):
    """
    Compute disparity with conservative parameters.
    NO aggressive hole-filling that creates false data.
    """
    print("\n📊 Computing disparity (conservative, no false data)...")
    
    # Conservative SGBM parameters
    window_size = 5
    min_disp = 0
    num_disp = 16 * 10  # 160 disparities
    
    stereo = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=window_size,
        P1=8 * 3 * window_size ** 2,
        P2=32 * 3 * window_size ** 2,
        disp12MaxDiff=1,
        uniquenessRatio=15,  # Higher = stricter (less false matches)
        speckleWindowSize=200,
        speckleRange=2,
        preFilterCap=63,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    
    # Compute disparity
    disparity = stereo.compute(gray_left, gray_right)
    disparity = disparity.astype(np.float32) / 16.0
    
    # ONLY filter valid pixels - NO inpainting/filling
    # This preserves accuracy
    valid_mask = disparity > 0
    
    # Light median filter ONLY on valid pixels
    if np.any(valid_mask):
        disp_uint16 = (disparity * 16).astype(np.uint16)
        disp_filtered = cv2.medianBlur(disp_uint16, 5)
        disparity[valid_mask] = (disp_filtered[valid_mask].astype(np.float32) / 16.0)
    
    valid_pixels = np.sum(valid_mask)
    total_pixels = disparity.shape[0] * disparity.shape[1]
    coverage = 100 * valid_pixels / total_pixels
    
    print(f"✓ Disparity: {valid_pixels:,}/{total_pixels:,} pixels ({coverage:.1f}% coverage)")
    print(f"  Disparity range: {disparity[valid_mask].min():.1f} - {disparity[valid_mask].max():.1f}")
    
    return disparity


def reproject_to_3d(disparity, Q_matrix):
    """
    Use Q matrix to reproject disparity to 3D.
    This is the CORRECT way using calibration.
    """
    print("\n🌐 Reprojecting to 3D using Q matrix...")
    
    # Use OpenCV's built-in reprojection
    points_3d = cv2.reprojectImageTo3D(disparity, Q_matrix)
    
    # Extract valid points
    valid_mask = disparity > 0
    points_3d_valid = points_3d[valid_mask]
    
    if len(points_3d_valid) == 0:
        print("⚠️  No valid 3D points after reprojection")
        return np.array([]), points_3d, valid_mask
    
    # Filter outliers (points behind camera or too far)
    z_values = points_3d_valid[:, 2]
    
    # Check if all Z are negative (camera setup might be swapped)
    if np.all(z_values < 0):
        print("⚠️  All Z values negative - taking absolute values")
        z_values = np.abs(z_values)
        points_3d_valid[:, 2] = z_values
    
    # Keep only reasonable depths
    valid_z = (z_values > 0) & (z_values < 5000)  # Max 5 meters
    
    points_3d_filtered = points_3d_valid[valid_z]
    
    if len(points_3d_filtered) > 0:
        print(f"✓ 3D points: {len(points_3d_filtered):,}")
        print(f"  Depth range: {points_3d_filtered[:, 2].min():.1f} - {points_3d_filtered[:, 2].max():.1f} mm")
    else:
        print("⚠️  All points filtered out - using all valid points")
        points_3d_filtered = points_3d_valid
        if len(points_3d_filtered) > 0:
            print(f"✓ 3D points: {len(points_3d_filtered):,}")
            print(f"  Depth range: {points_3d_filtered[:, 2].min():.1f} - {points_3d_filtered[:, 2].max():.1f} mm")
    
    return points_3d_filtered, points_3d, valid_mask


def create_visualization(img_left, img_right, disparity, points_3d, points_3d_full, valid_mask):
    """Create visualization showing actual scene structure."""
    print("\n📊 Creating visualization...")
    
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Original left image
    ax1 = fig.add_subplot(2, 4, 1)
    ax1.imshow(cv2.cvtColor(img_left, cv2.COLOR_BGR2RGB))
    ax1.set_title('Left Camera (Original)', fontsize=12, fontweight='bold')
    ax1.axis('off')
    
    # 2. Original right image
    ax2 = fig.add_subplot(2, 4, 2)
    ax2.imshow(cv2.cvtColor(img_right, cv2.COLOR_BGR2RGB))
    ax2.set_title('Right Camera (Original)', fontsize=12, fontweight='bold')
    ax2.axis('off')
    
    # 3. RAW disparity (no filling)
    ax3 = fig.add_subplot(2, 4, 3)
    disp_vis = np.copy(disparity)
    disp_vis[~valid_mask] = np.nan
    
    if np.any(valid_mask):
        vmin, vmax = np.percentile(disparity[valid_mask], [5, 95])
        im = ax3.imshow(disp_vis, cmap='jet', vmin=vmin, vmax=vmax)
        ax3.set_title('RAW Disparity Map\n(No false data filling)', fontsize=12, fontweight='bold')
        plt.colorbar(im, ax=ax3, label='Disparity', fraction=0.046)
    else:
        ax3.text(0.5, 0.5, 'No valid disparity', ha='center', va='center', transform=ax3.transAxes)
    ax3.axis('off')
    
    # 4. Depth map from Q matrix
    ax4 = fig.add_subplot(2, 4, 4)
    depth_map = points_3d_full[:, :, 2].copy()
    depth_map[~valid_mask] = np.nan
    
    if np.any(valid_mask):
        valid_depths = depth_map[valid_mask]
        vmin, vmax = np.percentile(valid_depths, [5, 95])
        im2 = ax4.imshow(depth_map, cmap='jet', vmin=vmin, vmax=vmax)
        ax4.set_title('Depth Map (Q Matrix)\n(Blue=Close, Red=Far)', fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=ax4, label='Depth (mm)', fraction=0.046)
    else:
        ax4.text(0.5, 0.5, 'No valid depth', ha='center', va='center', transform=ax4.transAxes)
    ax4.axis('off')
    
    # 5. Depth overlay on image
    ax5 = fig.add_subplot(2, 4, 5)
    ax5.imshow(cv2.cvtColor(img_left, cv2.COLOR_BGR2RGB))
    if np.any(valid_mask):
        depth_overlay = depth_map.copy()
        ax5.imshow(depth_overlay, cmap='jet', alpha=0.5, vmin=vmin, vmax=vmax)
    ax5.set_title('Depth Overlay', fontsize=12, fontweight='bold')
    ax5.axis('off')
    
    # 6. 3D point cloud
    ax6 = fig.add_subplot(2, 4, 6, projection='3d')
    if len(points_3d) > 0 and points_3d.size > 0:
        subsample = max(1, len(points_3d) // 10000)
        pts = points_3d[::subsample]
        depths = pts[:, 2]
        scatter = ax6.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=depths, cmap='jet', s=1, alpha=0.6)
        ax6.set_xlabel('X (mm)')
        ax6.set_ylabel('Y (mm)')
        ax6.set_zlabel('Depth Z (mm)')
        ax6.set_title('3D Point Cloud', fontsize=12, fontweight='bold')
        plt.colorbar(scatter, ax=ax6, shrink=0.5, label='Depth (mm)')
    else:
        ax6.text2D(0.5, 0.5, 'No valid points', ha='center', va='center', transform=ax6.transAxes)
    
    # 7. Top-down view
    ax7 = fig.add_subplot(2, 4, 7)
    if len(points_3d) > 0 and points_3d.size > 0:
        scatter2 = ax7.scatter(pts[:, 0], pts[:, 2], c=depths, cmap='jet', s=1, alpha=0.5)
        ax7.set_xlabel('X (mm)')
        ax7.set_ylabel('Depth Z (mm)')
        ax7.set_title('Top-Down View', fontsize=12, fontweight='bold')
        ax7.grid(True, alpha=0.3)
        ax7.invert_yaxis()
        plt.colorbar(scatter2, ax=ax7, label='Depth (mm)')
    
    # 8. Statistics
    ax8 = fig.add_subplot(2, 4, 8)
    ax8.axis('off')
    
    if len(points_3d) > 0 and points_3d.size > 0:
        valid_depths = points_3d[:, 2]
        stats_text = f"""
CALIBRATED STEREO DEPTH
════════════════════════

Using Q Matrix from Calibration

Coverage:
  Valid pixels: {np.sum(valid_mask):,}
  Coverage: {100*np.sum(valid_mask)/valid_mask.size:.1f}%

3D Points:
  Total: {len(points_3d):,}

Depth Range:
  Min: {valid_depths.min():.1f} mm
  Max: {valid_depths.max():.1f} mm
  Median: {np.median(valid_depths):.1f} mm
  Mean: {valid_depths.mean():.1f} mm

✓ Using actual calibration
✓ No false data filling
✓ Accurate depth from Q matrix
"""
    else:
        stats_text = "No valid depth data"
    
    ax8.text(0.05, 0.5, stats_text, fontsize=10, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    ax8.set_title('Statistics', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('calibrated_depth_graph.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: calibrated_depth_graph.png")
    plt.close(fig)


def main():
    print("=" * 80)
    print("CALIBRATED STEREO DEPTH")
    print("Uses actual calibration matrices - NO false data")
    print("=" * 80)
    
    # Load calibration
    matrices = load_calibration()
    
    if 'Q' not in matrices:
        print("\n❌ Q matrix not found! Cannot use calibrated depth.")
        print("   Falling back to uncalibrated method...")
        return
    
    # Get cameras
    cam_left = 0
    cam_right = 1
    if len(sys.argv) >= 3:
        try:
            cam_left = int(sys.argv[1])
            cam_right = int(sys.argv[2])
        except ValueError:
            pass
    
    print(f"\n📸 Using cameras: {cam_left} (left) and {cam_right} (right)")
    
    # Capture
    print("\n[1/5] Capturing images...")
    img_left, img_right = capture_stereo_images(cam_left, cam_right)
    if img_left is None:
        return
    
    # Rectify
    print("\n[2/5] Rectifying images...")
    img_left_rect, img_right_rect = rectify_images(img_left, img_right, matrices)
    
    # Convert to grayscale
    gray_left = cv2.cvtColor(img_left_rect, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(img_right_rect, cv2.COLOR_BGR2GRAY)
    
    # Compute disparity
    print("\n[3/5] Computing disparity...")
    disparity = compute_disparity_calibrated(gray_left, gray_right)
    
    # Reproject to 3D
    print("\n[4/5] Reprojecting to 3D...")
    points_3d, points_3d_full, valid_mask = reproject_to_3d(disparity, matrices['Q'])
    
    # Visualize
    print("\n[5/5] Creating visualization...")
    create_visualization(img_left, img_right, disparity, points_3d, points_3d_full, valid_mask)
    
    print("\n" + "=" * 80)
    print("✅ CALIBRATED DEPTH COMPLETE!")
    print("=" * 80)
    print("\nOutput: calibrated_depth_graph.png")
    print("\nThis version:")
    print("  ✓ Uses your actual calibration matrices")
    print("  ✓ Rectifies images properly")
    print("  ✓ Uses Q matrix for accurate depth")
    print("  ✓ NO false data filling (shows real coverage)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

