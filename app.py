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
STICKER_DIR = os.path.join(STATIC_DIR, "stickers")
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(COLLAGE_DIR, exist_ok=True)
os.makedirs(STICKER_DIR, exist_ok=True)

camera = cv2.VideoCapture(0)
latest_frame = None

session_data = {
    "photos": [],
    "edited": [],
    "selected_stickers": {},
    "current_photo": None,
    "puzzle_image": None,
    "puzzle_order": [],
    "puzzle_solved": False
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

def make_pil_preview(path, stickers):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    for item in stickers:
        kind = item.get("kind", "emoji")
        text = item.get("text", "✨")
        x = int(item.get("x", w // 2))
        y = int(item.get("y", h // 2))
        size = int(item.get("size", 64))

        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()

        if kind == "emoji":
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        elif kind == "text":
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

def save_tiles_preview(tiles, order, grid=3):
    tile_w, tile_h = tiles[0].size
    canvas_img = Image.new("RGB", (tile_w * grid, tile_h * grid), (255, 240, 247))
    for idx, tile_index in enumerate(order):
        r = idx // grid
        c = idx % grid
        canvas_img.paste(tiles[tile_index], (c * tile_w, r * tile_h))
    preview_path = os.path.join(COLLAGE_DIR, "puzzle_preview.jpg")
    canvas_img.save(preview_path)
    return preview_path

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
    global latest_frame, session_data
    if latest_frame is None:
        return jsonify({"ok": False, "msg": "No camera frame yet"})

    photo_id = str(uuid.uuid4())[:8]
    path = os.path.join(CAPTURE_DIR, f"{photo_id}.jpg")
    cv2.imwrite(path, latest_frame)

    session_data["current_photo"] = "/" + path.replace("\\", "/")
    session_data["photos"].append(session_data["current_photo"])
    session_data["selected_stickers"][session_data["current_photo"]] = []

    return jsonify({"ok": True, "msg": "Photo captured!", "path": session_data["current_photo"]})

@app.route("/add_sticker", methods=["POST"])
def add_sticker():
    data = request.get_json()
    path = data.get("path")
    sticker = {
        "kind": data.get("kind", "emoji"),
        "text": data.get("text", "✨"),
        "x": data.get("x", 100),
        "y": data.get("y", 100),
        "size": data.get("size", 64)
    }
    if path not in session_data["selected_stickers"]:
        session_data["selected_stickers"][path] = []
    session_data["selected_stickers"][path].append(sticker)
    return jsonify({"ok": True, "stickers": session_data["selected_stickers"][path]})

@app.route("/approve_photo", methods=["POST"])
def approve_photo():
    data = request.get_json()
    path = data.get("path")
    if not path:
        return jsonify({"ok": False, "msg": "No image path"})

    file_path = path.lstrip("/")
    if not os.path.exists(file_path):
        return jsonify({"ok": False, "msg": "File not found"})

    stickers = session_data["selected_stickers"].get(path, [])
    preview = make_pil_preview(file_path, stickers)
    edited_id = str(uuid.uuid4())[:8]
    edited_path = os.path.join(CAPTURE_DIR, f"{edited_id}_edited.jpg")
    preview.save(edited_path)
    edited_public = "/" + edited_path.replace("\\", "/")

    session_data["edited"].append(edited_public)
    session_data["current_photo"] = edited_public

    return jsonify({"ok": True, "msg": "Approved!", "edited_path": edited_public})

@app.route("/make_puzzle", methods=["POST"])
def make_puzzle():
    data = request.get_json()
    path = data.get("path")
    if not path:
        return jsonify({"ok": False, "msg": "No image path"})

    file_path = path.lstrip("/")
    if not os.path.exists(file_path):
        return jsonify({"ok": False, "msg": "File not found"})

    img = Image.open(file_path).convert("RGB").resize((600, 600))
    tiles = split_tiles(img, 3)
    order = list(range(9))
    np.random.shuffle(order)
    preview_path = save_tiles_preview(tiles, order, 3)

    session_data["puzzle_image"] = {
        "source": path,
        "tiles": tiles,
        "order": order,
        "solution": list(range(9)),
        "preview": "/" + preview_path.replace("\\", "/"),
        "solved": False
    }

    return jsonify({
        "ok": True,
        "msg": "Puzzle created!",
        "preview": session_data["puzzle_image"]["preview"],
        "order": order
    })

@app.route("/puzzle_state")
def puzzle_state():
    p = session_data.get("puzzle_image")
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
    p = session_data.get("puzzle_image")
    if not p:
        return jsonify({"ok": False})

    if a >= 0 and b >= 0 and a < len(p["order"]) and b < len(p["order"]):
        p["order"][a], p["order"][b] = p["order"][b], p["order"][a]

    solved = p["order"] == p["solution"]
    p["solved"] = solved
    return jsonify({"ok": True, "solved": solved, "order": p["order"]})

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    images = data.get("images", [])
    pdf_path = os.path.join(COLLAGE_DIR, f"collage_{uuid.uuid4().hex[:8]}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    page_w, page_h = A4

    c.setTitle("Kawaii Photo Collage")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, page_h - 50, "Kawaii Photo Collage")

    x = 40
    y = page_h - 170
    box_w = 160
    box_h = 160
    gap = 18

    for idx, img_path in enumerate(images[:4]):
        file_path = img_path.lstrip("/")
        if os.path.exists(file_path):
            img = Image.open(file_path).convert("RGB")
            img = ImageOps.fit(img, (box_w, box_h))
            temp_path = os.path.join(COLLAGE_DIR, f"tmp_{idx}.jpg")
            img.save(temp_path)
            c.drawImage(ImageReader(temp_path), x, y, width=box_w, height=box_h)
            c.rect(x, y, box_w, box_h)
            x += box_w + gap
            if x + box_w > page_w - 40:
                x = 40
                y -= box_h + 40

    c.showPage()
    c.save()

    return jsonify({"ok": True, "pdf": "/" + pdf_path.replace("\\", "/")})

if __name__ == "__main__":
    app.run(debug=True)