import cv2, requests, base64, argparse, sys
import numpy as np

URL = "http://localhost:5001/api/camera/collect-calib"  # your existing endpoint

def open_cam(idx):
    cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)  # macOS-friendly
    if not cap.isOpened():
        cap = cv2.VideoCapture(idx)
    return cap

def post_frame(img_bgr, cols, rows, square_mm):
    ok, buf = cv2.imencode(".jpg", img_bgr)
    if not ok: return {"error":"encode failed"}
    files = {"image": ("frame.jpg", buf.tobytes(), "image/jpeg")}
    params = dict(cols=cols, rows=rows, square_mm=square_mm)
    r = requests.post(URL, files=files, params=params, timeout=10)
    return r.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--cols", type=int, default=9)       # inner corners
    ap.add_argument("--rows", type=int, default=6)
    ap.add_argument("--square-mm", type=float, default=25.0)
    args = ap.parse_args()

    cap = open_cam(args.cam)
    if not cap.isOpened():
        print("Could not open camera", file=sys.stderr); return

    print("Live view. Press 'c' to capture -> POST /collect-calib, 'q' to quit.")
    while True:
        ok, frame = cap.read()
        if not ok: break
        cv2.putText(frame, "Press 'c' to CAPTURE, 'q' to quit",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imshow("Calibrate cam", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        if k == ord('c'):
            resp = post_frame(frame, args.cols, args.rows, args.square_mm)
            print(resp)

    cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
