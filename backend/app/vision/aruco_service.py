from flask import Blueprint, request, jsonify
from pathlib import Path
import cv2, json, base64
import numpy as np

bp_aruco = Blueprint("aruco", __name__, url_prefix="/api/vision")

STEREO_JSON = Path("data/calib/stereo.json")

def _decode_img_from_field(field):
    if field is None:
        return None
    # file object
    if hasattr(field, "read"):
        return cv2.imdecode(np.frombuffer(field.read(), np.uint8), cv2.IMREAD_COLOR)
    # base64 string
    s = field
    if "," in s:
        s = s.split(",")[1]
    return cv2.imdecode(np.frombuffer(base64.b64decode(s), np.uint8), cv2.IMREAD_COLOR)

def _detect_aruco(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    dct = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    det = cv2.aruco.ArucoDetector(dct, cv2.aruco.DetectorParameters())
    corners, ids, _ = det.detectMarkers(gray)
    out = {}
    if ids is not None:
        for i, c in zip(ids.flatten(), corners):
            ctr = c.reshape(-1, 2).mean(axis=0).tolist()
            out[int(i)] = {"center": ctr, "corners": c.reshape(4, 2).tolist()}
    return out

def _triangulate(pt1, pt2, K1, D1, K2, D2, R, T):
    p1n = cv2.undistortPoints(np.array([[pt1]], np.float32), K1, D1)
    p2n = cv2.undistortPoints(np.array([[pt2]], np.float32), K2, D2)
    P1 = np.hstack([np.eye(3, np.float32), np.zeros((3, 1), np.float32)])
    P2 = np.hstack([R.astype(np.float32), T.astype(np.float32)])
    Xh = cv2.triangulatePoints(P1, P2, p1n.reshape(2,1), p2n.reshape(2,1))
    X = (Xh[:3] / Xh[3]).reshape(3)
    return X

@bp_aruco.get("/aruco-ping")
def aruco_ping():
    return jsonify({"ok": True, "service": "aruco"})

@bp_aruco.post("/aruco-2d")
def aruco_2d():
    """Upload one image (multipart 'image' or JSON 'image') and get markers {id: center,corners}."""
    img = None
    if "image" in request.files:
        img = _decode_img_from_field(request.files["image"])
    elif request.is_json and "image" in (request.json or {}):
        img = _decode_img_from_field(request.json["image"])
    if img is None:
        return jsonify({"error": "Provide image"}), 400
    return jsonify({"markers": _detect_aruco(img)})

@bp_aruco.post("/aruco-3d")
def aruco_3d():
    """
    Provide left+right images and marker IDs; return 3D for ee and obj (and rel = obj - ee).
    Multipart: 'left','right' OR JSON: 'left','right' (base64).
    Body/args: 'arm_id', 'obj_id' (ints). Requires data/calib/stereo.json (K1,D1,K2,D2,R,T).
    """
    if not STEREO_JSON.exists():
        return jsonify({"error": "No stereo.json found in data/calib"}), 400

    calib = json.loads(STEREO_JSON.read_text())
    K1 = np.array(calib["K1"], np.float32); D1 = np.array(calib["D1"], np.float32).reshape(-1,1)
    K2 = np.array(calib["K2"], np.float32); D2 = np.array(calib["D2"], np.float32).reshape(-1,1)
    R  = np.array(calib["R"],  np.float32); T  = np.array(calib["T"],  np.float32).reshape(3,1)

    # read images
    if "left" in request.files and "right" in request.files:
        imgL = _decode_img_from_field(request.files["left"])
        imgR = _decode_img_from_field(request.files["right"])
    elif request.is_json and "left" in (request.json or {}) and "right" in request.json:
        imgL = _decode_img_from_field(request.json["left"])
        imgR = _decode_img_from_field(request.json["right"])
    else:
        return jsonify({"error": "Provide 'left' and 'right' images"}), 400

    # ids via form, query, or JSON
    arm_id = request.form.get("arm_id") or request.args.get("arm_id") or (request.json or {}).get("arm_id")
    obj_id = request.form.get("obj_id") or request.args.get("obj_id") or (request.json or {}).get("obj_id")
    arm_id = int(arm_id) if arm_id is not None else 0
    obj_id = int(obj_id) if obj_id is not None else 1

    detL = _detect_aruco(imgL)
    detR = _detect_aruco(imgR)

    if arm_id not in detL or arm_id not in detR or obj_id not in detL or obj_id not in detR:
        return jsonify({"error": "Required IDs not visible in both views",
                        "present_left": list(detL.keys()), "present_right": list(detR.keys())}), 400

    armL = detL[arm_id]["center"]; armR = detR[arm_id]["center"]
    objL = detL[obj_id]["center"]; objR = detR[obj_id]["center"]

    X_arm = _triangulate(armL, armR, K1, D1, K2, D2, R, T)
    X_obj = _triangulate(objL, objR, K1, D1, K2, D2, R, T)
    rel = (X_obj - X_arm).tolist()

    return jsonify({"ok": True, "arm_id": arm_id, "obj_id": obj_id,
                    "ee_xyz": X_arm.tolist(), "obj_xyz": X_obj.tolist(),
                    "rel_xyz": rel, "frame": "camera1"})
