from flask import Blueprint, request, jsonify
from pathlib import Path
import cv2, json, time, base64
import numpy as np

bp_stereo = Blueprint("stereo", __name__, url_prefix="/api")

CALIB_DIR = Path("data/calib"); CALIB_DIR.mkdir(parents=True, exist_ok=True)
PAIRS_DIR = CALIB_DIR / "stereo_pairs"; PAIRS_DIR.mkdir(exist_ok=True)
STEREO_JSON = CALIB_DIR / "stereo.json"

def _decode_img(field):
    if field is None: return None
    if hasattr(field, "read"):
        arr = np.frombuffer(field.read(), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    s = field
    if "," in s: s = s.split(",")[1]
    try:
        arr = np.frombuffer(base64.b64decode(s), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None

def _find_corners(gray, pattern):
    ret, corners = cv2.findChessboardCorners(
        gray, pattern,
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK
    )
    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
    return ret, corners

@bp_stereo.get("/stereo-ping")
def stereo_ping():
    return jsonify({"ok": True, "service": "stereo"})

@bp_stereo.post("/stereo/collect-pair")
def stereo_collect_pair():
    cols = int(request.args.get("cols", 9))
    rows = int(request.args.get("rows", 6))
    square_mm = float(request.args.get("square_mm", 25.0))

    if "left" in request.files and "right" in request.files:
        imgL = _decode_img(request.files["left"])
        imgR = _decode_img(request.files["right"])
    else:
        return jsonify({"ok": False, "error": "Provide 'left' and 'right'"}), 400

    if imgL is None or imgR is None:
        return jsonify({"ok": False, "error": "Invalid images"}), 400

    retL, cornersL = _find_corners(cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY), (cols, rows))
    retR, cornersR = _find_corners(cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY), (cols, rows))
    if not (retL and retR):
        return jsonify({"ok": False, "error": "Chessboard not found in both"}), 400

    ts = int(time.time() * 1000)
    Lp = PAIRS_DIR / f"pair_{ts}_L.jpg"
    Rp = PAIRS_DIR / f"pair_{ts}_R.jpg"
    Lj = PAIRS_DIR / f"pair_{ts}_L.json"
    Rj = PAIRS_DIR / f"pair_{ts}_R.json"
    cv2.imwrite(str(Lp), imgL)
    cv2.imwrite(str(Rp), imgR)

    meta = lambda side, path, corners: {
        "cols": cols, "rows": rows, "square_mm": square_mm,
        "image_path": str(path),
        "image_size_xy": [imgL.shape[1], imgL.shape[0]],
        "corners_xy": corners.reshape(-1, 2).tolist(),
        "pair_ts": ts, "side": side
    }
    Lj.write_text(json.dumps(meta("L", Lp, cornersL), indent=2))
    Rj.write_text(json.dumps(meta("R", Rp, cornersR), indent=2))

    return jsonify({"ok": True, "pair_ts": ts, "left": str(Lp), "right": str(Rp)})

@bp_stereo.post("/stereo/calibrate")
def stereo_calibrate():
    Ls = sorted(PAIRS_DIR.glob("pair_*_L.json"))
    Rs = sorted(PAIRS_DIR.glob("pair_*_R.json"))
    if not Ls or not Rs:
        return jsonify({"ok": False, "error": "No pairs found"}), 400

    def ts(p): return int(p.stem.split("_")[1])
    Lm = {ts(p): json.loads(p.read_text()) for p in Ls}
    Rm = {ts(p): json.loads(p.read_text()) for p in Rs}
    common = sorted(set(Lm) & set(Rm))
    if len(common) < 8:
        return jsonify({"ok": False, "error": f"Need at least 8 pairs, got {len(common)}"}), 400

    m0 = Lm[common[0]]
    cols, rows, square_mm = m0["cols"], m0["rows"], m0["square_mm"]
    image_size = tuple(m0["image_size_xy"])
    objp = np.zeros((rows*cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= square_mm

    objpoints, imgpoints1, imgpoints2 = [], [], []
    for t in common:
        cL = np.array(Lm[t]["corners_xy"], np.float32).reshape(-1,1,2)
        cR = np.array(Rm[t]["corners_xy"], np.float32).reshape(-1,1,2)
        objpoints.append(objp)
        imgpoints1.append(cL)
        imgpoints2.append(cR)

    K1, K2 = np.eye(3), np.eye(3)
    D1, D2 = np.zeros((5,1)), np.zeros((5,1))
    criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 100, 1e-6)
    rms, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints1, imgpoints2,
        K1, D1, K2, D2,
        image_size, criteria=criteria
    )

    out = {
        "rms": float(rms),
        "pairs_used": len(common),
        "image_size": image_size,
        "K1": K1.tolist(), "D1": D1.reshape(-1).tolist(),
        "K2": K2.tolist(), "D2": D2.reshape(-1).tolist(),
        "R": R.tolist(), "T": T.reshape(3).tolist()
    }
    STEREO_JSON.write_text(json.dumps(out, indent=2))
    return jsonify({"ok": True, "saved_to": str(STEREO_JSON), "rms": float(rms)})

