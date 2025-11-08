#!/usr/bin/env python3
"""
Live stereo pair capture client.
Press 'c' to capture (sends both frames to /api/stereo/collect-pair)
Press 'q' to quit.
"""

import cv2
import requests
import base64
import argparse

def encode_img(img):
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()

def send_pair(left_img, right_img, cols, rows, square_mm):
    url = f"http://localhost:5001/api/stereo/collect-pair?cols={cols}&rows={rows}&square_mm={square_mm}"
    files = {
        "left": ("left.jpg", encode_img(left_img), "image/jpeg"),
        "right": ("right.jpg", encode_img(right_img), "image/jpeg")
    }
    try:
        r = requests.post(url, files=files)
        print(r.json())
    except Exception as e:
        print("POST error:", e)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--left", type=int, default=0, help="Left camera index")
    ap.add_argument("--right", type=int, default=1, help="Right camera index")
    ap.add_argument("--cols", type=int, default=9)
    ap.add_argument("--rows", type=int, default=6)
    ap.add_argument("--square-mm", type=float, default=25.0)
    args = ap.parse_args()

    capL = cv2.VideoCapture(args.left)
    capR = cv2.VideoCapture(args.right)
    if not capL.isOpened() or not capR.isOpened():
        print("Could not open one or both cameras.")
        return

    print("Press 'c' to capture -> POST /stereo/collect-pair, 'q' to quit.")

    while True:
        okL, frameL = capL.read()
        okR, frameR = capR.read()
        if not (okL and okR):
            print("Frame grab failed.")
            break

        both = cv2.hconcat([frameL, frameR])
        cv2.imshow("Stereo Pair (L|R)", both)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            print("Capturing and sending pair...")
            send_pair(frameL, frameR, args.cols, args.rows, args.square_mm)

    capL.release()
    capR.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

