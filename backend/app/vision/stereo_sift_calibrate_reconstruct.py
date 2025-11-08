#!/usr/bin/env python3
"""
Stereo SIFT + Calibration + 3D Reconstruction
================================================

What this script does
---------------------
1) Stereo capture for chessboard images (for calibration).
2) Mono intrinsics for each camera, then stereo calibration to get R, T, E, F.
3) SIFT feature detection & FLANN matching between a *pair* of images.
4) Essential matrix pose recovery and linear triangulation to a 3D point cloud.
5) Rectification, disparity (optional) and PLY export.

Your provided baseline distortion for camera 1 is used as an initial guess:
    dist_cam1 = np.array([[0.152, -0.475, 0.000137, -0.00147, 0.481]])
You can set --d1-init "0.152,-0.475,0.000137,-0.00147,0.481" to lock or seed calibration.

Usage examples
--------------
# Capture chessboard images from two cameras (IDs 0 and 1)
python stereo_sift_calibrate_reconstruct.py capture --cam-left 0 --cam-right 1 --cb-cols 9 --cb-rows 6 --square 0.024 --out data/calib --every 10

# Calibrate using images in data/calib (will save YAML + NPZ + CSVs)
python stereo_sift_calibrate_reconstruct.py calibrate --calib-dir data/calib --cb-cols 9 --cb-rows 6 --square 0.024 --out data/calib/calib.yaml \
    --d1-init 0.152,-0.475,0.000137,-0.00147,0.481

# Run SIFT matching and triangulate a pair
python stereo_sift_calibrate_reconstruct.py reconstruct --calib data/calib/calib.yaml \
    --left data/pairs/left.png --right data/pairs/right.png --ply out.ply

# Live rectified view (optional)
python stereo_sift_calibrate_reconstruct.py live --calib data/calib/calib.yaml --cam-left 0 --cam-right 1

Notes
-----
- Requires OpenCV (>=4.5) with xfeatures2d/SIFT (cv2.SIFT_create exists by default in new OpenCV).
- Install: pip install opencv-python numpy pyyaml
- Chessboard pattern: internal corners count (cols x rows) and square size in meters.

"""
import argparse
import os
import glob
import yaml
import time
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import cv2 as cv


# -----------------------------
# Dataclasses
# -----------------------------
@dataclass
class StereoIntrinsics:
    K1: np.ndarray
    D1: np.ndarray
    K2: np.ndarray
    D2: np.ndarray

@dataclass
class StereoExtrinsics:
    R: np.ndarray
    T: np.ndarray
    E: np.ndarray
    F: np.ndarray

@dataclass
class Rectification:
    R1: np.ndarray
    R2: np.ndarray
    P1: np.ndarray
    P2: np.ndarray
    Q: np.ndarray
    map1x: np.ndarray
    map1y: np.ndarray
    map2x: np.ndarray
    map2y: np.ndarray


# -----------------------------
# Helpers
# -----------------------------
DEF_D1_BASELINE = np.array([[0.152, -0.475, 0.000137, -0.00147, 0.481]], dtype=np.float64)

def parse_kc_list(s: str) -> np.ndarray:
    vals = [float(x.strip()) for x in s.split(',') if x.strip()]
    return np.array([vals], dtype=np.float64)


def draw_matches(imgL, kpL, imgR, kpR, matches, max_draw=200):
    matches = sorted(matches, key=lambda m: m.distance)[:max_draw]
    return cv.drawMatches(imgL, kpL, imgR, kpR, matches, None, flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)


def save_yaml(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump({k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in data.items()}, f)


def save_npz_and_csvs(yaml_path: str, mats: dict):
    base, _ = os.path.splitext(yaml_path)
    npz_path = base + '.npz'
    np.savez(npz_path, **mats)
    # individual CSVs
    for name, val in mats.items():
        if isinstance(val, np.ndarray):
            np.savetxt(base + f'_{name}.csv', val, delimiter=',')


def pretty_print_mats(mats: dict):
    """Pretty console output for calibration matrices"""
    for k in ['K1','D1','K2','D2','R','T','E','F','R1','R2','P1','P2','Q']:
        if k in mats:
            print(f"\n[{k}]")
            print(mats[k])


def load_yaml(path: str) -> dict:
    with open(path, 'r') as f:
        d = yaml.safe_load(f)
    # Convert lists back to np arrays where appropriate
    for k, v in list(d.items()):
        if isinstance(v, list):
            d[k] = np.array(v, dtype=np.float64)
    return d


# -----------------------------
# Calibration Routines
# -----------------------------

def collect_chessboards(calib_dir: str) -> Tuple[List[str], List[str]]:
    left = sorted(glob.glob(os.path.join(calib_dir, 'left_*.png')) + glob.glob(os.path.join(calib_dir, 'left_*.jpg')))
    right = sorted(glob.glob(os.path.join(calib_dir, 'right_*.png')) + glob.glob(os.path.join(calib_dir, 'right_*.jpg')))
    if len(left) != len(right):
        print(f"[WARN] Left/right counts differ: {len(left)} vs {len(right)}")
    n = min(len(left), len(right))
    return left[:n], right[:n]


def mono_calibrate(img_paths: List[str], cb_cols: int, cb_rows: int, square: float,
                   d_init: np.ndarray | None = None) -> Tuple[np.ndarray, np.ndarray]:
    objp = np.zeros((cb_rows * cb_cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cb_cols, 0:cb_rows].T.reshape(-1, 2)
    objp *= square

    objpoints = []
    imgpoints = []
    img_size = None

    for p in img_paths:
        img = cv.imread(p, cv.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img_size = (img.shape[1], img.shape[0])
        ret, corners = cv.findChessboardCorners(img, (cb_cols, cb_rows))
        if not ret:
            continue
        corners = cv.cornerSubPix(img, corners, (11, 11), (-1, -1),
                                  criteria=(cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 1e-4))
        objpoints.append(objp)
        imgpoints.append(corners)

    if not objpoints:
        raise RuntimeError("No chessboards detected for mono calibration.")

    flags = 0
    if d_init is not None:
        # Seed distortion and fix 3rd 4th 5th only if you want, otherwise let it optimize
        D = d_init.astype(np.float64)
        K = np.eye(3, dtype=np.float64)
        ret, K, D, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, img_size, K, D, None, None, flags)
    else:
        ret, K, D, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, img_size, None, None)

    return K, D


def stereo_calibrate(left_paths: List[str], right_paths: List[str], cb_cols: int, cb_rows: int, square: float,
                     d1_init: np.ndarray | None = None) -> Tuple[StereoIntrinsics, StereoExtrinsics, Rectification]:
    assert len(left_paths) == len(right_paths) and len(left_paths) > 0

    # Prepare object points
    objp = np.zeros((cb_rows * cb_cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cb_cols, 0:cb_rows].T.reshape(-1, 2)
    objp *= square

    objpoints = []
    imgpointsL = []
    imgpointsR = []

    img_size = None
    for lp, rp in zip(left_paths, right_paths):
        imgL = cv.imread(lp, cv.IMREAD_GRAYSCALE)
        imgR = cv.imread(rp, cv.IMREAD_GRAYSCALE)
        if imgL is None or imgR is None:
            continue
        img_size = (imgL.shape[1], imgL.shape[0])
        retL, cornersL = cv.findChessboardCorners(imgL, (cb_cols, cb_rows))
        retR, cornersR = cv.findChessboardCorners(imgR, (cb_cols, cb_rows))
        if not (retL and retR):
            continue
        cornersL = cv.cornerSubPix(imgL, cornersL, (11, 11), (-1, -1),
                                   (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 1e-4))
        cornersR = cv.cornerSubPix(imgR, cornersR, (11, 11), (-1, -1),
                                   (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 1e-4))
        objpoints.append(objp)
        imgpointsL.append(cornersL)
        imgpointsR.append(cornersR)

    if not objpoints:
        raise RuntimeError("No valid stereo chessboards detected.")

    # Mono init
    K1, D1 = mono_calibrate(left_paths, cb_cols, cb_rows, square, d_init=d1_init)
    K2, D2 = mono_calibrate(right_paths, cb_cols, cb_rows, square)

    # Stereo calibration
    flags = cv.CALIB_FIX_INTRINSIC  # keep intrinsics from mono-cal
    criteria = (cv.TERM_CRITERIA_MAX_ITER + cv.TERM_CRITERIA_EPS, 100, 1e-5)
    ret, K1, D1, K2, D2, R, T, E, F = cv.stereoCalibrate(
        objpoints, imgpointsL, imgpointsR,
        K1, D1, K2, D2, img_size,
        criteria=criteria, flags=flags)

    # Rectification
    R1, R2, P1, P2, Q, roi1, roi2 = cv.stereoRectify(K1, D1, K2, D2, img_size, R, T, flags=cv.CALIB_ZERO_DISPARITY)
    map1x, map1y = cv.initUndistortRectifyMap(K1, D1, R1, P1, img_size, cv.CV_32FC1)
    map2x, map2y = cv.initUndistortRectifyMap(K2, D2, R2, P2, img_size, cv.CV_32FC1)

    intr = StereoIntrinsics(K1, D1, K2, D2)
    extr = StereoExtrinsics(R, T, E, F)
    rect = Rectification(R1, R2, P1, P2, Q, map1x, map1y, map2x, map2y)
    return intr, extr, rect


# -----------------------------
# SIFT + Triangulation
# -----------------------------

def sift_match(imgL_gray: np.ndarray, imgR_gray: np.ndarray,
               ratio: float = 0.75) -> Tuple[List[cv.KeyPoint], List[cv.KeyPoint], List[cv.DMatch]]:
    sift = cv.SIFT_create()
    kp1, des1 = sift.detectAndCompute(imgL_gray, None)
    kp2, des2 = sift.detectAndCompute(imgR_gray, None)
    index_params = dict(algorithm=1, trees=5)  # FLANN KDTree
    search_params = dict(checks=50)
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < ratio * n.distance:
            good.append(m)
    return kp1, kp2, good


def normalize_points(pts: np.ndarray, K: np.ndarray) -> np.ndarray:
    # pts Nx2 -> homogeneous, then K^-1
    pts_h = cv.convertPointsToHomogeneous(pts).reshape(-1, 3).T
    Kinv = np.linalg.inv(K)
    x = Kinv @ pts_h
    return (x[:2] / x[2]).T  # Nx2


def triangulate_from_matches(kp1, kp2, matches, K1, K2, R, T) -> Tuple[np.ndarray, np.ndarray]:
    if len(matches) < 8:
        raise RuntimeError("Not enough matches to triangulate")

    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

    # Build projection matrices P1 = K1[I|0], P2 = K2[R|T]
    P1 = K1 @ np.hstack([np.eye(3), np.zeros((3, 1))])
    P2 = K2 @ np.hstack([R, T.reshape(3, 1)])

    pts4d = cv.triangulatePoints(P1, P2, pts1.T, pts2.T)  # 4xN
    pts3d = (pts4d[:3] / pts4d[3]).T  # Nx3
    return pts3d, pts1


def write_ply(path: str, pts3d: np.ndarray, colors: np.ndarray | None = None):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write('ply\nformat ascii 1.0\n')
        n = len(pts3d)
        if colors is None:
            f.write(f'element vertex {n}\n')
            f.write('property float x\nproperty float y\nproperty float z\n')
            f.write('end_header\n')
            for p in pts3d:
                f.write(f"{p[0]} {p[1]} {p[2]}\n")
        else:
            f.write(f'element vertex {n}\n')
            f.write('property float x\nproperty float y\nproperty float z\n')
            f.write('property uchar red\nproperty uchar green\nproperty uchar blue\n')
            f.write('end_header\n')
            for p, c in zip(pts3d, colors):
                f.write(f"{p[0]} {p[1]} {p[2]} {int(c[2])} {int(c[1])} {int(c[0])}\n")


# -----------------------------
# Capture utilities
# -----------------------------

def capture_chessboards(cam_left: int, cam_right: int, out_dir: str, every: int = 10,
                        width: int | None = None, height: int | None = None):
    os.makedirs(out_dir, exist_ok=True)
    capL = cv.VideoCapture(cam_left)
    capR = cv.VideoCapture(cam_right)
    if width and height:
        capL.set(cv.CAP_PROP_FRAME_WIDTH, width)
        capL.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        capR.set(cv.CAP_PROP_FRAME_WIDTH, width)
        capR.set(cv.CAP_PROP_FRAME_HEIGHT, height)

    i = 0
    saved = 0
    print("[INFO] Press 'q' to quit. Capturing every", every, "frames.")
    while True:
        retL, frameL = capL.read()
        retR, frameR = capR.read()
        if not (retL and retR):
            print("[ERR] Failed to grab frames")
            break
        vis = np.hstack([frameL, frameR])
        cv.imshow('stereo', vis)
        if i % every == 0:
            pathL = os.path.join(out_dir, f'left_{saved:04d}.png')
            pathR = os.path.join(out_dir, f'right_{saved:04d}.png')
            cv.imwrite(pathL, frameL)
            cv.imwrite(pathR, frameR)
            print(f"[SAVE] {pathL} | {pathR}")
            saved += 1
        i += 1
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    capL.release()
    capR.release()
    cv.destroyAllWindows()


# -----------------------------
# CLI Entrypoints
# -----------------------------

def cmd_calibrate(args):
    left_paths, right_paths = collect_chessboards(args.calib_dir)
    d1_init = parse_kc_list(args.d1_init) if args.d1_init else DEF_D1_BASELINE
    print("[INFO] Using D1 init:", d1_init)

    intr, extr, rect = stereo_calibrate(left_paths, right_paths, args.cb_cols, args.cb_rows, args.square, d1_init)

    data = {
        'K1': intr.K1, 'D1': intr.D1,
        'K2': intr.K2, 'D2': intr.D2,
        'R': extr.R, 'T': extr.T, 'E': extr.E, 'F': extr.F,
        'R1': rect.R1, 'R2': rect.R2, 'P1': rect.P1, 'P2': rect.P2, 'Q': rect.Q
    }
    save_yaml(args.out, data)
    save_npz_and_csvs(args.out, data)
    print(f"[OK] Saved calibration to {args.out} and {os.path.splitext(args.out)[0]}.npz plus per-matrix CSVs")
    pretty_print_mats(data)


    intr, extr, rect = stereo_calibrate(left_paths, right_paths, args.cb_cols, args.cb_rows, args.square, d1_init)

    data = {
        'K1': intr.K1, 'D1': intr.D1,
        'K2': intr.K2, 'D2': intr.D2,
        'R': extr.R, 'T': extr.T, 'E': extr.E, 'F': extr.F,
        'R1': rect.R1, 'R2': rect.R2, 'P1': rect.P1, 'P2': rect.P2, 'Q': rect.Q
    }
    save_yaml(args.out, data)
    print(f"[OK] Saved calibration to {args.out}")


def cmd_reconstruct(args):
    cfg = load_yaml(args.calib)
    K1, D1 = cfg['K1'], cfg['D1']
    K2, D2 = cfg['K2'], cfg['D2']
    R, T = cfg['R'], cfg['T']

    imgL = cv.imread(args.left)
    imgR = cv.imread(args.right)
    if imgL is None or imgR is None:
        raise FileNotFoundError("Left or right image not found")

    # Optional undistort-rectify if matrices exist
    if all(k in cfg for k in ['R1', 'R2', 'P1', 'P2']):
        R1, R2, P1, P2 = cfg['R1'], cfg['R2'], cfg['P1'], cfg['P2']
        map1x, map1y = cv.initUndistortRectifyMap(K1, D1, R1, P1, (imgL.shape[1], imgL.shape[0]), cv.CV_32FC1)
        map2x, map2y = cv.initUndistortRectifyMap(K2, D2, R2, P2, (imgR.shape[1], imgR.shape[0]), cv.CV_32FC1)
        imgL = cv.remap(imgL, map1x, map1y, cv.INTER_LINEAR)
        imgR = cv.remap(imgR, map2x, map2y, cv.INTER_LINEAR)

    grayL = cv.cvtColor(imgL, cv.COLOR_BGR2GRAY)
    grayR = cv.cvtColor(imgR, cv.COLOR_BGR2GRAY)

    kp1, kp2, good = sift_match(grayL, grayR, ratio=args.ratio)
    print(f"[INFO] Good matches: {len(good)}")

    # Recover pose (sanity check) using essential matrix
    pts1 = np.float32([kp1[m.queryIdx].pt for m in good])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good])
    E, mask = cv.findEssentialMat(pts1, pts2, K1, method=cv.RANSAC, threshold=1.0, prob=0.999)
    _, R_est, T_est, mask_pose = cv.recoverPose(E, pts1, pts2, K1)
    print("[POSE] From E: inliers=", int(mask_pose.sum()))

    # Triangulate using calibrated R,T (prefer calibrated baseline)
    pts3d, _ = triangulate_from_matches(kp1, kp2, good, K1, K2, R, T)

    # Optional coloring from left image
    colors = []
    for m in good:
        u, v = map(int, round(kp1[m.queryIdx].pt[0])), map(int, round(kp1[m.queryIdx].pt[1]))
        u = int(kp1[m.queryIdx].pt[0])
        v = int(kp1[m.queryIdx].pt[1])
        if 0 <= v < imgL.shape[0] and 0 <= u < imgL.shape[1]:
            colors.append(imgL[v, u])
        else:
            colors.append((255, 255, 255))
    colors = np.array(colors)

    if args.ply:
        write_ply(args.ply, pts3d, colors)
        print(f"[OK] Wrote point cloud: {args.ply} ({len(pts3d)} points)")

    # Visualization of matches
    vis = draw_matches(grayL, kp1, grayR, kp2, good, max_draw=min(300, len(good)))
    cv.imshow('SIFT matches', vis)
    cv.waitKey(0)
    cv.destroyAllWindows()


def cmd_live(args):
    cfg = load_yaml(args.calib)
    K1, D1 = cfg['K1'], cfg['D1']
    K2, D2 = cfg['K2'], cfg['D2']
    R1, R2, P1, P2 = cfg['R1'], cfg['R2'], cfg['P1'], cfg['P2']

    capL = cv.VideoCapture(args.cam_left)
    capR = cv.VideoCapture(args.cam_right)

    if args.width and args.height:
        capL.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
        capL.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)
        capR.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
        capR.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    map1x, map1y = cv.initUndistortRectifyMap(K1, D1, R1, P1, (int(capL.get(3)) or 640, int(capL.get(4)) or 480), cv.CV_32FC1)
    map2x, map2y = cv.initUndistortRectifyMap(K2, D2, R2, P2, (int(capR.get(3)) or 640, int(capR.get(4)) or 480), cv.CV_32FC1)

    print("[INFO] Press 'q' to quit")
    while True:
        r1, f1 = capL.read()
        r2, f2 = capR.read()
        if not (r1 and r2):
            print("[ERR] Grab failed")
            break
        r1r = cv.remap(f1, map1x, map1y, cv.INTER_LINEAR)
        r2r = cv.remap(f2, map2x, map2y, cv.INTER_LINEAR)
        stacked = np.hstack([r1r, r2r])
        # draw epipolar lines guide
        h = stacked.shape[0]
        for y in range(0, h, 40):
            cv.line(stacked, (0, y), (stacked.shape[1]-1, y), (0, 255, 0), 1)
        cv.imshow('Rectified Live (L|R)', stacked)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    capL.release()
    capR.release()
    cv.destroyAllWindows()


def cmd_capture(args):
    capture_chessboards(args.cam_left, args.cam_right, args.out, every=args.every, width=args.width, height=args.height)


# -----------------------------
# Main
# -----------------------------

def main():
    ap = argparse.ArgumentParser(description='Stereo SIFT + Calibration + 3D Reconstruction')
    sub = ap.add_subparsers(dest='cmd', required=True)

    # capture
    ap_cap = sub.add_parser('capture', help='Capture chessboard frames from two cameras')
    ap_cap.add_argument('--cam-left', type=int, default=0)
    ap_cap.add_argument('--cam-right', type=int, default=1)
    ap_cap.add_argument('--out', type=str, required=True)
    ap_cap.add_argument('--every', type=int, default=10)
    ap_cap.add_argument('--width', type=int, default=None)
    ap_cap.add_argument('--height', type=int, default=None)
    ap_cap.set_defaults(func=cmd_capture)

    # calibrate
    ap_cal = sub.add_parser('calibrate', help='Calibrate stereo from saved chessboard images')
    ap_cal.add_argument('--calib-dir', type=str, required=True)
    ap_cal.add_argument('--cb-cols', type=int, required=True, help='Internal corners along columns')
    ap_cal.add_argument('--cb-rows', type=int, required=True, help='Internal corners along rows')
    ap_cal.add_argument('--square', type=float, required=True, help='Square size in meters')
    ap_cal.add_argument('--out', type=str, required=True)
    ap_cal.add_argument('--d1-init', type=str, default=None, help='Comma list for initial D1 (k1,k2,p1,p2,k3)')
    ap_cal.set_defaults(func=cmd_calibrate)

    # reconstruct
    ap_rec = sub.add_parser('reconstruct', help='SIFT match + triangulate a stereo pair')
    ap_rec.add_argument('--calib', type=str, required=True)
    ap_rec.add_argument('--left', type=str, required=True)
    ap_rec.add_argument('--right', type=str, required=True)
    ap_rec.add_argument('--ratio', type=float, default=0.75)
    ap_rec.add_argument('--ply', type=str, default='out.ply')
    ap_rec.set_defaults(func=cmd_reconstruct)

    # live
    ap_live = sub.add_parser('live', help='Show live rectified stereo stream')
    ap_live.add_argument('--calib', type=str, required=True)
    ap_live.add_argument('--cam-left', type=int, default=0)
    ap_live.add_argument('--cam-right', type=int, default=1)
    ap_live.add_argument('--width', type=int, default=None)
    ap_live.add_argument('--height', type=int, default=None)
    ap_live.set_defaults(func=cmd_live)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
