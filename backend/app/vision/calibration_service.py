from flask import Blueprint, request, jsonify
from pathlib import Path
import cv2, json, time, base64
import numpy as np

# Top-level blueprint (name and url_prefix must match what main.py imports/uses)
bp_calib = Blueprint("calibration", __name__, url_prefix="/api")

CALIB_DIR = Path("data/calib"); CALIB_DIR.mkdir(parents=True, exist_ok=True)
CAPTURES = CALIB_DIR / "captures"; CAPTURES.mkdir(exist_ok=True)
CAMERA_JSON = CALIB_DIR / "camera_intrinsics.json"

def _find_corners(gray, pattern_size):
    ret, corners = cv2.findChessboardCorners(
        gray, pattern_size,
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK
    )
    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
    return ret, corners

def _decode_image(req):
    # multipart 'image'
    if "image" in req.files:
        arr = np.frombuffer(req.files["image"].read(), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    # JSON base64 'image'
    if req.is_json and "image" in (req.json or {}):
        b64 = req.json["image"]
        if "," in b64: b64 = b64.split(",")[1]
        arr = np.frombuffer(base64.b64decode(b64), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return None

@bp_calib.get("/calib-ping")
def calib_ping():
    return jsonify({"ok": True, "service": "calibration"})

@bp_calib.post("/camera/collect-calib")
def camera_collect_calib():
    """
    Upload one chessboard image (multipart 'image' or JSON base64 'image').
    Query params: ?cols=9&rows=6&square_mm=25  (inner corners!)
    """
    cols = int(request.args.get("cols", 9))
    rows = int(request.args.get("rows", 6))
    square_mm = float(request.args.get("square_mm", 25.0))

    img = _decode_image(request)
    if img is None:
        return jsonify({"ok": False, "error": "Provide image (multipart 'image' or JSON base64 'image')"}), 400

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = _find_corners(gray, (cols, rows))
    if not ret:
        return jsonify({"ok": False, "error": "Chessboard not found"}), 400

    ts = int(time.time() * 1000)
    img_p = CAPTURES / f"calib_{ts}.jpg"
    json_p = CAPTURES / f"calib_{ts}.json"
    cv2.imwrite(str(img_p), img)

    with open(json_p, "w") as f:
        json.dump({
            "cols": cols, "rows": rows, "square_mm": square_mm,
            "image_path": str(img_p),
            "image_size_xy": [img.shape[1], img.shape[0]],
            "corners_xy": corners.reshape(-1,2).tolist()
        }, f, indent=2)

    return jsonify({"ok": True, "saved": str(img_p), "corner_count": int(corners.shape[0])})

@bp_calib.post("/camera/calibrate")
def camera_calibrate():
    """Run calibration using captures in data/calib/captures -> writes camera_intrinsics.json"""
    jsons = sorted(CAPTURES.glob("*.json"))
    if len(jsons) < 8:
        return jsonify({"ok": False, "error": "Need at least 8 captures"}), 400

    meta0 = json.loads(jsons[0].read_text())
    cols, rows = int(meta0["cols"]), int(meta0["rows"])
    square_mm = float(meta0["square_mm"])

    objp = np.zeros((rows*cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= square_mm

    objpoints, imgpoints, image_size = [], [], None
    for j in jsons:
        m = json.loads(j.read_text())
        corners = np.array(m["corners_xy"], np.float32).reshape(-1,1,2)
        objpoints.append(objp)
        imgpoints.append(corners)
        if image_size is None:
            image_size = tuple(m["image_size_xy"])

    ret, K, D, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, image_size, None, None)
    if not ret:
        return jsonify({"ok": False, "error": "Calibration failed"}), 500

    out = {
        "image_width": int(image_size[0]),
        "image_height": int(image_size[1]),
        "camera_matrix": K.tolist(),
        "dist_coeffs": D.reshape(-1).tolist(),
        "reprojection_error": float(ret),
        "board": {"cols": cols, "rows": rows, "square_mm": square_mm},
        "captures_used": len(jsons),
    }
    CAMERA_JSON.write_text(json.dumps(out, indent=2))

    # visual sanity check
    img0 = cv2.imread(meta0["image_path"])
    und = cv2.undistort(img0, K, D)
    cv2.imwrite(str(CALIB_DIR / "undist_example.jpg"), und)

    return jsonify({"ok": True, "saved_to": str(CAMERA_JSON), "reprojection_error": float(ret)})
