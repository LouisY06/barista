#!/usr/bin/env python3
"""
Stereo Camera Recalibration Tool
==================================
Captures chessboard pairs and generates calibration matrices in CSV format.

Usage:
    python recalibrate_stereo.py --left 0 --right 1 --cols 9 --rows 6 --square 25.0

Press 'c' to capture a pair (need at least 8 pairs)
Press 'q' to quit and calibrate
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys

# Output directory
CALIB_DIR = Path(__file__).parent / "app" / "vision" / "data" / "calib"
CALIB_DIR.mkdir(parents=True, exist_ok=True)
CAPTURES_DIR = CALIB_DIR / "recalib_captures"
CAPTURES_DIR.mkdir(exist_ok=True)


def find_chessboard(gray, pattern_size):
    """Find chessboard corners."""
    ret, corners = cv2.findChessboardCorners(
        gray, pattern_size,
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK
    )
    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    return ret, corners


def capture_pairs(cam_left, cam_right, cols, rows, square_mm):
    """Interactive capture of stereo pairs."""
    print("\n" + "=" * 80)
    print("STEREO CALIBRATION - CAPTURE MODE")
    print("=" * 80)
    print(f"📸 Cameras: {cam_left} (left) and {cam_right} (right)")
    print(f"📐 Chessboard: {cols}x{rows} inner corners, {square_mm}mm squares")
    print("\nInstructions:")
    print("  • Position chessboard so BOTH cameras can see it clearly")
    print("  • Move chessboard to different positions/angles")
    print("  • Press 'c' to capture a pair (need at least 8 pairs)")
    print("  • Press 'q' to quit and run calibration")
    print("=" * 80 + "\n")
    
    cap_left = cv2.VideoCapture(cam_left)
    cap_right = cv2.VideoCapture(cam_right)
    
    if not cap_left.isOpened() or not cap_right.isOpened():
        print("❌ Could not open cameras")
        return []
    
    # Warm up
    for _ in range(10):
        cap_left.read()
        cap_right.read()
    
    pattern_size = (cols, rows)
    pair_count = 0
    
    while True:
        ret_left, img_left = cap_left.read()
        ret_right, img_right = cap_right.read()
        
        if not (ret_left and ret_right):
            print("⚠️  Failed to grab frames")
            break
        
        # Find corners
        gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)
        
        retL, cornersL = find_chessboard(gray_left, pattern_size)
        retR, cornersR = find_chessboard(gray_right, pattern_size)
        
        # Draw corners
        img_left_disp = img_left.copy()
        img_right_disp = img_right.copy()
        
        if retL:
            cv2.drawChessboardCorners(img_left_disp, pattern_size, cornersL, retL)
        if retR:
            cv2.drawChessboardCorners(img_right_disp, pattern_size, cornersR, retR)
        
        # Show status
        status = "✓ READY" if (retL and retR) else "✗ Move chessboard"
        cv2.putText(img_left_disp, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if (retL and retR) else (0, 0, 255), 2)
        cv2.putText(img_left_disp, f"Pairs: {pair_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Display
        both = cv2.hconcat([img_left_disp, img_right_disp])
        cv2.imshow("Stereo Calibration (Press 'c' to capture, 'q' to quit)", both)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c'):
            if retL and retR:
                # Save pair
                timestamp = int(cv2.getTickCount())
                left_path = CAPTURES_DIR / f"pair_{timestamp}_L.jpg"
                right_path = CAPTURES_DIR / f"pair_{timestamp}_R.jpg"
                
                cv2.imwrite(str(left_path), img_left)
                cv2.imwrite(str(right_path), img_right)
                
                # Save corner data
                left_json = CAPTURES_DIR / f"pair_{timestamp}_L.json"
                right_json = CAPTURES_DIR / f"pair_{timestamp}_R.json"
                
                import json
                left_data = {
                    "cols": cols, "rows": rows, "square_mm": square_mm,
                    "image_path": str(left_path),
                    "image_size_xy": [img_left.shape[1], img_left.shape[0]],
                    "corners_xy": cornersL.reshape(-1, 2).tolist()
                }
                right_data = {
                    "cols": cols, "rows": rows, "square_mm": square_mm,
                    "image_path": str(right_path),
                    "image_size_xy": [img_right.shape[1], img_right.shape[0]],
                    "corners_xy": cornersR.reshape(-1, 2).tolist()
                }
                
                left_json.write_text(json.dumps(left_data, indent=2))
                right_json.write_text(json.dumps(right_data, indent=2))
                
                pair_count += 1
                print(f"✓ Captured pair #{pair_count}")
            else:
                print("⚠️  Chessboard not visible in both cameras")
    
    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()
    
    # Collect all pairs
    left_jsons = sorted(CAPTURES_DIR.glob("pair_*_L.json"))
    right_jsons = sorted(CAPTURES_DIR.glob("pair_*_R.json"))
    
    return left_jsons, right_jsons


def run_calibration(left_jsons, right_jsons):
    """Run stereo calibration and save matrices as CSV."""
    print("\n" + "=" * 80)
    print("RUNNING STEREO CALIBRATION")
    print("=" * 80)
    
    if len(left_jsons) < 8 or len(right_jsons) < 8:
        print(f"❌ Need at least 8 pairs, got {len(left_jsons)}")
        return False
    
    import json
    
    # Load first pair to get parameters
    meta0 = json.loads(left_jsons[0].read_text())
    cols, rows, square_mm = meta0["cols"], meta0["rows"], meta0["square_mm"]
    image_size = tuple(meta0["image_size_xy"])
    
    print(f"📐 Chessboard: {cols}x{rows}, square={square_mm}mm")
    print(f"📏 Image size: {image_size}")
    
    # Prepare object points
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= square_mm
    
    # Match pairs by timestamp
    def get_timestamp(path):
        return int(path.stem.split("_")[1])
    
    left_map = {get_timestamp(p): p for p in left_jsons}
    right_map = {get_timestamp(p): p for p in right_jsons}
    common_timestamps = sorted(set(left_map.keys()) & set(right_map.keys()))
    
    if len(common_timestamps) < 8:
        print(f"❌ Need at least 8 matched pairs, got {len(common_timestamps)}")
        return False
    
    print(f"✓ Using {len(common_timestamps)} matched pairs")
    
    # Collect object and image points
    objpoints = []
    imgpoints1 = []
    imgpoints2 = []
    
    for ts in common_timestamps:
        left_data = json.loads(left_map[ts].read_text())
        right_data = json.loads(right_map[ts].read_text())
        
        cornersL = np.array(left_data["corners_xy"], np.float32).reshape(-1, 1, 2)
        cornersR = np.array(right_data["corners_xy"], np.float32).reshape(-1, 1, 2)
        
        objpoints.append(objp)
        imgpoints1.append(cornersL)
        imgpoints2.append(cornersR)
    
    # Run stereo calibration
    print("\n🔄 Running stereo calibration...")
    K1, K2 = np.eye(3), np.eye(3)
    D1, D2 = np.zeros((5, 1)), np.zeros((5, 1))
    criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 100, 1e-6)
    
    rms, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints1, imgpoints2,
        K1, D1, K2, D2,
        image_size, criteria=criteria
    )
    
    print(f"✓ RMS reprojection error: {rms:.4f} pixels")
    
    # Compute rectification
    print("\n🔄 Computing rectification matrices...")
    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
        K1, D1, K2, D2, image_size, R, T,
        flags=cv2.CALIB_ZERO_DISPARITY,
        alpha=0
    )
    
    print("✓ Rectification computed")
    
    # Save as CSV files (matching the format expected by calibrated depth script)
    print("\n💾 Saving calibration matrices...")
    
    matrices = {
        'K1': K1,
        'K2': K2,
        'D1': D1.reshape(-1),
        'D2': D2.reshape(-1),
        'R': R,
        'T': T.reshape(-1),
        'R1': R1,
        'R2': R2,
        'P1': P1,
        'P2': P2,
        'Q': Q
    }
    
    for name, matrix in matrices.items():
        filepath = CALIB_DIR / f"calib_{name}.csv"
        df = pd.DataFrame(matrix)
        df.to_csv(filepath, header=False, index=False)
        print(f"  ✓ Saved {name} -> {filepath}")
    
    # Also save as NPZ for convenience
    npz_path = CALIB_DIR / "calib.npz"
    np.savez(npz_path, **{k: v for k, v in matrices.items()})
    print(f"  ✓ Saved NPZ -> {npz_path}")
    
    # Save summary
    summary = {
        "rms_error": float(rms),
        "pairs_used": len(common_timestamps),
        "image_size": image_size,
        "chessboard": {"cols": cols, "rows": rows, "square_mm": square_mm}
    }
    import json
    summary_path = CALIB_DIR / "calib_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"  ✓ Saved summary -> {summary_path}")
    
    print("\n" + "=" * 80)
    print("✅ CALIBRATION COMPLETE!")
    print("=" * 80)
    print(f"\nRMS Error: {rms:.4f} pixels (lower is better, < 1.0 is excellent)")
    print(f"Pairs used: {len(common_timestamps)}")
    print("\nMatrices saved to:")
    print(f"  {CALIB_DIR}")
    print("\nYou can now run:")
    print("  python stereo_depth_calibrated.py 0 1")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Stereo camera recalibration")
    parser.add_argument("--left", type=int, default=0, help="Left camera index")
    parser.add_argument("--right", type=int, default=1, help="Right camera index")
    parser.add_argument("--cols", type=int, default=9, help="Chessboard inner corners (columns)")
    parser.add_argument("--rows", type=int, default=6, help="Chessboard inner corners (rows)")
    parser.add_argument("--square", type=float, default=25.0, help="Square size in mm")
    parser.add_argument("--skip-capture", action="store_true", help="Skip capture, only run calibration on existing pairs")
    
    args = parser.parse_args()
    
    if not args.skip_capture:
        # Capture pairs
        left_jsons, right_jsons = capture_pairs(
            args.left, args.right, args.cols, args.rows, args.square
        )
    else:
        # Use existing pairs
        left_jsons = sorted(CAPTURES_DIR.glob("pair_*_L.json"))
        right_jsons = sorted(CAPTURES_DIR.glob("pair_*_R.json"))
        print(f"📁 Found {len(left_jsons)} existing pairs")
    
    if len(left_jsons) == 0:
        print("\n❌ No pairs captured. Exiting.")
        return
    
    # Run calibration
    success = run_calibration(left_jsons, right_jsons)
    
    if not success:
        print("\n❌ Calibration failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

