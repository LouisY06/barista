#!/usr/bin/env python3
"""
Visualize object distances from camera using stereo calibration matrices.

Uses the Q matrix (disparity-to-depth reprojection) to compute 3D coordinates
in a homogeneous coordinate system from stereo disparity.
"""

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Paths
CALIB_DIR = Path(__file__).parent / "app" / "vision" / "data" / "calib"

def load_calibration_matrices():
    """Load all calibration matrices from CSV files."""
    matrices = {}
    
    # Load all CSV files
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
        'Q': 'calib_Q.csv',
        'E': 'calib_E.csv',
        'F': 'calib_F.csv'
    }
    
    for name, filename in csv_files.items():
        filepath = CALIB_DIR / filename
        if filepath.exists():
            # Read CSV without header
            df = pd.read_csv(filepath, header=None)
            matrices[name] = df.values
            print(f"Loaded {name}: shape {matrices[name].shape}")
        else:
            print(f"Warning: {filename} not found")
    
    return matrices


def capture_stereo_pair(camera_left=0, camera_right=1):
    """Capture images from two cameras."""
    cap_left = cv2.VideoCapture(camera_left)
    cap_right = cv2.VideoCapture(camera_right)
    
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
    
    return img_left, img_right


def compute_disparity(img_left, img_right, matrices):
    """
    Compute disparity map from rectified stereo images.
    """
    # Get calibration matrices
    K1 = matrices['K1']
    K2 = matrices['K2']
    D1 = matrices['D1'].ravel()
    D2 = matrices['D2'].ravel()
    R1 = matrices['R1']
    R2 = matrices['R2']
    P1 = matrices['P1']
    P2 = matrices['P2']
    
    h, w = img_left.shape[:2]
    
    # Compute rectification maps
    map1_left, map2_left = cv2.initUndistortRectifyMap(
        K1, D1, R1, P1, (w, h), cv2.CV_32FC1
    )
    map1_right, map2_right = cv2.initUndistortRectifyMap(
        K2, D2, R2, P2, (w, h), cv2.CV_32FC1
    )
    
    # Rectify images
    img_left_rect = cv2.remap(img_left, map1_left, map2_left, cv2.INTER_LINEAR)
    img_right_rect = cv2.remap(img_right, map1_right, map2_right, cv2.INTER_LINEAR)
    
    # Convert to grayscale
    gray_left = cv2.cvtColor(img_left_rect, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(img_right_rect, cv2.COLOR_BGR2GRAY)
    
    # Create stereo matcher (SGBM for better quality)
    window_size = 5
    min_disp = 0
    num_disp = 16 * 10  # Must be divisible by 16
    
    stereo = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=window_size,
        P1=8 * 3 * window_size ** 2,
        P2=32 * 3 * window_size ** 2,
        disp12MaxDiff=1,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32,
        preFilterCap=63,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    
    # Compute disparity
    print("Computing disparity map...")
    disparity = stereo.compute(gray_left, gray_right)
    
    # Convert to float and normalize
    disparity = disparity.astype(np.float32) / 16.0
    
    return disparity, img_left_rect, img_right_rect


def reproject_to_3d(disparity, Q_matrix):
    """
    Reproject disparity to 3D using Q matrix (homogeneous coordinates).
    
    The Q matrix transforms [x, y, disparity, 1]ᵀ to [X, Y, Z, W]ᵀ
    Real 3D coordinates: (X/W, Y/W, Z/W)
    """
    print("Reprojecting to 3D using Q matrix...")
    
    # Use cv2.reprojectImageTo3D which applies Q matrix
    points_3d = cv2.reprojectImageTo3D(disparity, Q_matrix)
    
    # Filter out invalid points (infinite or too far)
    mask = disparity > 0
    
    # Extract valid points
    points_3d_valid = points_3d[mask]
    
    # Check if we have any valid points
    if len(points_3d_valid) == 0:
        print("⚠️  No valid 3D points found!")
        print("This likely means:")
        print("  - Stereo matching failed (no disparity computed)")
        print("  - Cameras might be the same or too similar")
        print("  - Scene lacks texture for matching")
        return np.array([]), points_3d, mask
    
    # Check Z values (depth)
    z_values = points_3d_valid[:, 2]
    print(f"Z values (depth) range BEFORE filtering: {z_values.min():.2f} to {z_values.max():.2f}")
    print(f"Z values mean: {z_values.mean():.2f}, median: {np.median(z_values):.2f}")
    print(f"Number of positive Z: {np.sum(z_values > 0)}, negative Z: {np.sum(z_values < 0)}")
    
    # Less aggressive filtering - just remove extreme outliers and negatives
    z_abs = np.abs(z_values)
    z_median = np.median(z_abs)
    z_99 = np.percentile(z_abs, 99)
    
    # Keep positive Z values within reasonable range
    valid_mask = (z_values > 0) & (z_abs < z_99 * 2)
    points_3d_filtered = points_3d_valid[valid_mask]
    
    print(f"Total valid 3D points AFTER filtering: {len(points_3d_filtered)}")
    if len(points_3d_filtered) > 0:
        print(f"Depth range: {points_3d_filtered[:, 2].min():.2f} to {points_3d_filtered[:, 2].max():.2f}")
    else:
        print("⚠️  All points filtered out (likely all negative Z values)")
        print("Returning unfiltered points for visualization...")
        # Use absolute values if all Z are negative
        if np.all(z_values < 0):
            points_3d_valid[:, 2] = np.abs(points_3d_valid[:, 2])
            print("Converted negative Z to positive (absolute values)")
        points_3d_filtered = points_3d_valid
    
    return points_3d_filtered, points_3d, mask


def visualize_depth_graph(points_3d, disparity, points_3d_full, img_left):
    """
    Create multiple visualizations of depth/distance.
    
    Args:
        points_3d: Filtered 3D points (Nx3 array)
        disparity: Disparity map (HxW)
        points_3d_full: Full 3D point cloud (HxWx3)
        img_left: Left camera image
    """
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Disparity map (pseudo-depth)
    ax1 = fig.add_subplot(2, 3, 1)
    disp_vis = np.copy(disparity)
    disp_vis[disparity <= 0] = 0
    ax1.imshow(disp_vis, cmap='jet')
    ax1.set_title('Disparity Map\n(Inverse depth: closer = higher disparity)')
    ax1.set_xlabel('X (pixels)')
    ax1.set_ylabel('Y (pixels)')
    plt.colorbar(ax1.imshow(disp_vis, cmap='jet'), ax=ax1, label='Disparity (pixels)')
    
    # 2. Depth map (actual distance from Q matrix)
    ax2 = fig.add_subplot(2, 3, 2)
    # Extract depth (Z) from full 3D points
    depth_map = points_3d_full[:, :, 2].copy()
    # Take absolute value if needed and filter
    depth_map = np.abs(depth_map)
    depth_map[disparity <= 0] = 0
    
    # Visualize depth
    depth_vis = np.copy(depth_map)
    depth_vis[depth_map <= 0] = np.nan
    im2 = ax2.imshow(depth_vis, cmap='jet_r')  # jet_r so red = close, blue = far
    ax2.set_title('Depth Map\n(Actual distance: closer = red, farther = blue)')
    ax2.set_xlabel('X (pixels)')
    ax2.set_ylabel('Y (pixels)')
    plt.colorbar(im2, ax=ax2, label='Depth (mm)')
    
    # 3. Histogram of distances
    ax3 = fig.add_subplot(2, 3, 3)
    if len(points_3d) > 0:
        valid_depths = points_3d[:, 2]
        ax3.hist(valid_depths, bins=50, edgecolor='black', alpha=0.7)
        ax3.set_xlabel('Distance from camera (mm)')
        ax3.set_ylabel('Number of points')
        ax3.set_title(f'Distance Distribution\nMedian: {np.median(valid_depths):.1f}mm')
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No valid points', ha='center', va='center')
        ax3.set_title('Distance Distribution')
    
    # 4. Top-down view (X-Z plane) - Bird's eye view
    ax4 = fig.add_subplot(2, 3, 4)
    if len(points_3d) > 0:
        # Subsample for visualization
        subsample = points_3d[::10] if len(points_3d) > 10 else points_3d
        scatter = ax4.scatter(subsample[:, 0], subsample[:, 2], 
                              c=subsample[:, 2], cmap='jet_r', s=1, alpha=0.5)
        ax4.set_xlabel('X (horizontal, mm)')
        ax4.set_ylabel('Z (depth/distance from camera, mm)')
        ax4.set_title('Top-Down View (Bird\'s Eye)')
        ax4.axhline(y=0, color='r', linestyle='--', label='Camera position')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax4, label='Depth (mm)')
    else:
        ax4.text(0.5, 0.5, 'No valid points', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Top-Down View')
    
    # 5. Side view (Y-Z plane)
    ax5 = fig.add_subplot(2, 3, 5)
    if len(points_3d) > 0:
        subsample = points_3d[::10] if len(points_3d) > 10 else points_3d
        scatter2 = ax5.scatter(subsample[:, 1], subsample[:, 2], 
                               c=subsample[:, 2], cmap='jet_r', s=1, alpha=0.5)
        ax5.set_xlabel('Y (vertical, mm)')
        ax5.set_ylabel('Z (depth/distance from camera, mm)')
        ax5.set_title('Side View')
        ax5.axhline(y=0, color='r', linestyle='--', label='Camera position')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        plt.colorbar(scatter2, ax=ax5, label='Depth (mm)')
    else:
        ax5.text(0.5, 0.5, 'No valid points', ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title('Side View')
    
    # 6. 3D scatter plot
    ax6 = fig.add_subplot(2, 3, 6, projection='3d')
    if len(points_3d) > 0:
        subsample = points_3d[::50] if len(points_3d) > 50 else points_3d  # More aggressive subsampling for 3D
        scatter3 = ax6.scatter(subsample[:, 0], subsample[:, 1], subsample[:, 2],
                               c=subsample[:, 2], cmap='jet_r', s=1, alpha=0.3)
        ax6.set_xlabel('X (mm)')
        ax6.set_ylabel('Y (mm)')
        ax6.set_zlabel('Z - Depth (mm)')
        ax6.set_title('3D Point Cloud\n(Homogeneous coordinates)')
        plt.colorbar(scatter3, ax=ax6, label='Depth (mm)', shrink=0.5)
    else:
        ax6.text2D(0.5, 0.5, 'No valid points', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('3D Point Cloud')
    
    plt.tight_layout()
    plt.savefig('depth_visualization.png', dpi=150, bbox_inches='tight')
    print("\nSaved depth_visualization.png")
    plt.close(fig)


def main():
    print("=" * 60)
    print("Stereo Depth Visualization using Calibration Matrices")
    print("=" * 60)
    
    # Load calibration matrices
    print("\n1. Loading calibration matrices from CSV...")
    matrices = load_calibration_matrices()
    
    if 'Q' not in matrices:
        print("Error: Q matrix not found. Cannot reproject to 3D.")
        return
    
    print(f"\nQ matrix (disparity-to-depth reprojection):")
    print(matrices['Q'])
    
    # Capture stereo pair
    print("\n2. Capturing stereo images...")
    img_left, img_right = capture_stereo_pair(camera_left=0, camera_right=1)
    
    if img_left is None or img_right is None:
        print("Error: Could not capture images")
        return
    
    print(f"Captured images: {img_left.shape}")
    
    # Compute disparity
    print("\n3. Computing disparity (stereo matching)...")
    disparity, img_left_rect, img_right_rect = compute_disparity(img_left, img_right, matrices)
    
    valid_disparity = np.sum(disparity > 0)
    total_pixels = disparity.shape[0] * disparity.shape[1]
    print(f"Valid disparity pixels: {valid_disparity}/{total_pixels} ({100*valid_disparity/total_pixels:.1f}%)")
    
    # Save intermediate images for debugging
    cv2.imwrite('debug_left_rectified.jpg', img_left_rect)
    cv2.imwrite('debug_right_rectified.jpg', img_right_rect)
    print(f"Saved debug_left_rectified.jpg and debug_right_rectified.jpg")
    
    # Reproject to 3D using Q matrix
    print("\n4. Reprojecting to 3D homogeneous coordinates...")
    points_3d, points_3d_full, mask = reproject_to_3d(disparity, matrices['Q'])
    
    # Check if we have valid points
    if len(points_3d) == 0:
        print("\n⚠️  No valid 3D points - cannot create depth visualization")
        print("\nPossible issues:")
        print("  1. Are you using TWO different cameras (not the same camera twice)?")
        print("  2. Do the cameras have baseline separation (side-by-side)?")
        print("  3. Is there texture in the scene for stereo matching?")
        print("\nTip: Check debug_left_rectified.jpg and debug_right_rectified.jpg")
        print("     They should show DIFFERENT views of the same scene.")
        return
    
    # Visualize
    print("\n5. Creating visualizations...")
    visualize_depth_graph(points_3d, disparity, points_3d_full, img_left_rect)
    
    print("\n" + "=" * 60)
    print("✅ Complete! Check depth_visualization.png")
    print("=" * 60)
    
    # Print statistics
    print("\nDepth Statistics:")
    print(f"  Min distance: {points_3d[:, 2].min():.2f} mm")
    print(f"  Max distance: {points_3d[:, 2].max():.2f} mm")
    print(f"  Mean distance: {points_3d[:, 2].mean():.2f} mm")
    print(f"  Median distance: {np.median(points_3d[:, 2]):.2f} mm")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

