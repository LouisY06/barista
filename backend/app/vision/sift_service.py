# backend/app/vision/sift_service.py
from flask import Blueprint, jsonify

# >>> must exist at module top level <<<
bp_sift = Blueprint("sift", __name__, url_prefix="/api/vision")

@bp_sift.get("/sift-ping")
def sift_ping():
    return jsonify({"ok": True, "service": "sift"})
