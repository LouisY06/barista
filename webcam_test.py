import time
import argparse
import cv2
from ultralytics import YOLO

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="yolo11n.pt", help="Path to .pt weights (or yolo11n.pt)")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--device", default="cpu")  # set to "0" if you have a GPU
    p.add_argument("--camera", type=int, default=0)  # try 0 or 1
    p.add_argument("--backend", type=str, default="auto", choices=["auto","avf","cvdefault"])
    return p.parse_args()

def open_cam(index: int, backend: str):
    if backend == "avf":
        return cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)  # macOS
    elif backend == "cvdefault":
        return cv2.VideoCapture(index)  # OpenCV default
    else:
        # Try AVFoundation first on macOS, otherwise fallback
        cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            cap = cv2.VideoCapture(index)
        return cap

def draw_fps(frame, fps):
    txt = f"{fps:.1f} FPS"
    cv2.putText(frame, txt, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 3, cv2.LINE_AA)
    cv2.putText(frame, txt, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)

def main():
    args = parse_args()
    print("Loading model:", args.model)
    model = YOLO(args.model)  # will auto-download pretrained weights if needed

    cap = open_cam(args.camera, args.backend)
    if not cap.isOpened():
        raise SystemExit("Could not open camera. Try --camera 1 or --backend cvdefault")

    last = time.time()
    frames = 0
    fps = 0.0

    print("Press q to quit, s to save a frame.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # Inference (stream=True gives you results generator)
        results = model.predict(
            source=frame,
            imgsz=args.imgsz,
            conf=args.conf,
            device=args.device,
            verbose=False
        )

        # results is a list with one item for this frame
        r = results[0]
        annotated = r.plot()  # draw boxes/masks/labels on a copy

        # FPS
        frames += 1
        now = time.time()
        if now - last >= 0.5:
            fps = frames / (now - last)
            frames = 0
            last = now
        draw_fps(annotated, fps)

        cv2.imshow("YOLO Webcam Test", annotated)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            cv2.imwrite(f"frame_{int(time.time())}.jpg", annotated)
            print("Saved frame.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
