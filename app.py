from flask import Flask, render_template, request, jsonify, Response
import cv2
import numpy as np
import os
import uuid
from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CAPTURE_DIR = os.path.join(STATIC_DIR, "captures")
COLLAGE_DIR = os.path.join(STATIC_DIR, "collages")
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(COLLAGE_DIR, exist_ok=True)

camera = cv2.VideoCapture(0)
latest_frame = None

session_data = {
    "photos": [],
    "stickers": {},
    "current_photo": None,
    "puzzle": None
}

def gen_frames():
    global latest_frame
    while True:
        ok, frame = camera.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)
        latest_frame = frame.copy()
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

def public_path_from_abs(abs_path):
    rel = os.path.relpath(abs_path, BASE_DIR)
    return "/" + rel.replace("\\", "/")

def make_preview_with_stickers(path, stickers):
    img = Image.open(path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    for s in stickers:
        x = int(s.get("x", 120))
        y = int(s.get("y", 120))
        text = s.get("text", "✨")
        size = int(s.get("size", 64))
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    merged = Image.alpha_composite(img, overlay).convert("RGB")
    return merged

def split_tiles(pil_img, grid=3):
    w, h = pil_img.size
    tile_w = w // grid
    tile_h = h // grid
    tiles = []
    for r in range(grid):
        for c in range(grid):
            box = (c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h)
            tiles.append(pil_img.crop(box))
    return tiles

def save_puzzle_preview(tiles, order, grid=3):
    tw, th = tiles[0].size
    board = Image.new("RGB", (tw * grid, th * grid), (255, 240, 247))
    for idx, tile_idx in enumerate(order):
        r = idx // grid
        c = idx % grid
        board.paste(tiles[tile_idx], (c * tw, r * th))
    out_path = os.path.join(COLLAGE_DIR, "puzzle_preview.jpg")
    board.save(out_path)
    return out_path

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/booth")
def booth():
    return render_template("booth.html")

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/capture", methods=["POST"])
def capture():
    global latest_frame
    if latest_frame is None:
        return jsonify({"ok": False, "msg": "No frame available"})

    photo_id = uuid.uuid4().hex[:8]
    abs_path = os.path.join(CAPTURE_DIR, f"{photo_id}.jpg")
    cv2.imwrite(abs_path, latest_frame)

    public = public_path_from_abs(abs_path)
    session_data["current_photo"] = public
    session_data["photos"].append(public)
    session_data["stickers"][public] = []

    return jsonify({"ok": True, "msg": "Photo captured!", "path": public})

@app.route("/add_sticker", methods=["POST"])
def add_sticker():
    data = request.get_json()
    path = data.get("path")
    sticker = {
        "text": data.get("text", "✨"),
        "x": data.get("x", 120),
        "y": data.get("y", 120),
        "size": data.get("size", 64)
    }
    if path not in session_data["stickers"]:
        session_data["stickers"][path] = []
    session_data["stickers"][path].append(sticker)
    return jsonify({"ok": True, "stickers": session_data["stickers"][path]})

@app.route("/approve_photo", methods=["POST"])
def approve_photo():
    data = request.get_json()
    path = data.get("path")
    if not path:
        return jsonify({"ok": False, "msg": "Missing path"})

    abs_path = os.path.join(BASE_DIR, path.lstrip("/"))
    if not os.path.exists(abs_path):
        return jsonify({"ok": False, "msg": "Image not found"})

    stickers = session_data["stickers"].get(path, [])
    merged = make_preview_with_stickers(abs_path, stickers)
    edited_name = f"{uuid.uuid4().hex[:8]}_edited.jpg"
    edited_abs = os.path.join(CAPTURE_DIR, edited_name)
    merged.save(edited_abs)

    edited_public = public_path_from_abs(edited_abs)
    session_data["current_photo"] = edited_public
    session_data["photos"].append(edited_public)

    return jsonify({"ok": True, "msg": "Approved!", "edited_path": edited_public})

@app.route("/make_puzzle", methods=["POST"])
def make_puzzle():
    data = request.get_json()
    path = data.get("path")
    if not path:
        return jsonify({"ok": False, "msg": "Missing path"})

    abs_path = os.path.join(BASE_DIR, path.lstrip("/"))
    if not os.path.exists(abs_path):
        return jsonify({"ok": False, "msg": "File not found"})

    img = Image.open(abs_path).convert("RGB").resize((600, 600))
    tiles = split_tiles(img, 3)
    order = list(range(9))
    np.random.shuffle(order)

    preview_abs = save_puzzle_preview(tiles, order, 3)
    preview_public = public_path_from_abs(preview_abs)

    session_data["puzzle"] = {
        "tiles": tiles,
        "order": order,
        "solution": list(range(9)),
        "preview": preview_public,
        "solved": False
    }

    return jsonify({"ok": True, "msg": "Puzzle created!", "preview": preview_public, "order": order})

@app.route("/puzzle_state")
def puzzle_state():
    p = session_data.get("puzzle")
    if not p:
        return jsonify({"active": False})
    return jsonify({
        "active": True,
        "order": p["order"],
        "preview": p["preview"],
        "solved": p["solved"]
    })

@app.route("/swap_tile", methods=["POST"])
def swap_tile():
    data = request.get_json()
    a = int(data.get("a", -1))
    b = int(data.get("b", -1))
    p = session_data.get("puzzle")
    if not p:
        return jsonify({"ok": False})

    if 0 <= a < len(p["order"]) and 0 <= b < len(p["order"]):
        p["order"][a], p["order"][b] = p["order"][b], p["order"][a]

    solved = p["order"] == p["solution"]
    p["solved"] = solved
    return jsonify({"ok": True, "solved": solved, "order": p["order"]})

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    images = data.get("images", [])
    pdf_name = f"collage_{uuid.uuid4().hex[:8]}.pdf"
    pdf_abs = os.path.join(COLLAGE_DIR, pdf_name)

    c = canvas.Canvas(pdf_abs, pagesize=A4)
    page_w, page_h = A4
    c.setTitle("Kawaii Photo Collage")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, page_h - 50, "Kawaii Photo Collage")

    x, y = 40, page_h - 200
    box_w, box_h = 160, 160
    gap = 18

    for i, img_path in enumerate(images[:4]):
        abs_img = os.path.join(BASE_DIR, img_path.lstrip("/"))
        if os.path.exists(abs_img):
            img = Image.open(abs_img).convert("RGB")
            img = ImageOps.fit(img, (box_w, box_h))
            tmp = os.path.join(COLLAGE_DIR, f"tmp_{i}.jpg")
            img.save(tmp)
            c.drawImage(ImageReader(tmp), x, y, width=box_w, height=box_h)
            c.rect(x, y, box_w, box_h)
            x += box_w + gap
            if x + box_w > page_w - 40:
                x = 40
                y -= box_h + 40

    c.showPage()
    c.save()

    return jsonify({"ok": True, "pdf": public_path_from_abs(pdf_abs)})

if __name__ == "__main__":
    app.run(debug=True)