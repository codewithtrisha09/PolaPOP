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
POLAROID_DIR = os.path.join(STATIC_DIR, "polaroids")
STRIP_DIR = os.path.join(STATIC_DIR, "strips")
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(COLLAGE_DIR, exist_ok=True)
os.makedirs(POLAROID_DIR, exist_ok=True)
os.makedirs(STRIP_DIR, exist_ok=True)

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


def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
            )
        except Exception:
            return ImageFont.load_default()


def make_preview_with_stickers(path, stickers):
    img = Image.open(path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    for s in stickers:
        x = int(s.get("x", 120))
        y = int(s.get("y", 120))
        text = s.get("text", "✨")
        size = int(s.get("size", 64))
        font = load_font(size)
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    merged = Image.alpha_composite(img, overlay).convert("RGB")
    return merged


def make_polaroid(path, caption=""):
    img = Image.open(path).convert("RGB")

    target_w = 600
    ratio = target_w / img.width
    img = img.resize((target_w, int(img.height * ratio)))

    border = 28
    bottom_strip = 110

    frame_w = img.width + border * 2
    frame_h = img.height + border + bottom_strip

    frame = Image.new("RGB", (frame_w, frame_h), (255, 255, 255))
    frame.paste(img, (border, border))

    draw = ImageDraw.Draw(frame)
    if caption:
        font = load_font(28)
        text_w = draw.textlength(caption, font=font)
        text_x = (frame_w - text_w) / 2
        text_y = img.height + border + (bottom_strip - 28) / 2
        draw.text((text_x, text_y), caption, font=font, fill=(70, 55, 80))

    out_name = f"{uuid.uuid4().hex[:8]}_polaroid.jpg"
    out_abs = os.path.join(POLAROID_DIR, out_name)
    frame.save(out_abs, quality=92)
    return out_abs


def make_strip(abs_paths, caption=""):
    border = 24
    gap = 14
    strip_w = 480
    bottom_strip = 90

    imgs = []
    for p in abs_paths[:4]:
        img = Image.open(p).convert("RGB")
        ratio = strip_w / img.width
        img = img.resize((strip_w, int(img.height * ratio)))
        imgs.append(img)

    if not imgs:
        return None

    content_h = sum(im.height for im in imgs) + gap * (len(imgs) - 1)
    frame_w = strip_w + border * 2
    frame_h = content_h + border * 2 + bottom_strip

    frame = Image.new("RGB", (frame_w, frame_h), (255, 255, 255))
    y = border
    for im in imgs:
        frame.paste(im, (border, y))
        y += im.height + gap

    draw = ImageDraw.Draw(frame)
    if caption:
        font = load_font(26)
        text_w = draw.textlength(caption, font=font)
        text_x = (frame_w - text_w) / 2
        text_y = content_h + border + (bottom_strip - 26) / 2
        draw.text((text_x, text_y), caption, font=font, fill=(70, 55, 80))

    out_name = f"{uuid.uuid4().hex[:8]}_strip.jpg"
    out_abs = os.path.join(STRIP_DIR, out_name)
    frame.save(out_abs, quality=92)
    return out_abs


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


@app.route("/make_polaroid", methods=["POST"])
def make_polaroid_route():
    data = request.get_json()
    path = data.get("path")
    caption = data.get("caption", "")

    if not path:
        return jsonify({"ok": False, "msg": "Missing path"})

    abs_path = os.path.join(BASE_DIR, path.lstrip("/"))
    if not os.path.exists(abs_path):
        return jsonify({"ok": False, "msg": "Image not found"})

    out_abs = make_polaroid(abs_path, caption)
    out_public = public_path_from_abs(out_abs)

    return jsonify({"ok": True, "msg": "Polaroid ready!", "path": out_public})


@app.route("/make_strip", methods=["POST"])
def make_strip_route():
    data = request.get_json()
    images = data.get("images", [])
    caption = data.get("caption", "")

    abs_paths = []
    for img_path in images[:4]:
        abs_img = os.path.join(BASE_DIR, img_path.lstrip("/"))
        if os.path.exists(abs_img):
            abs_paths.append(abs_img)

    if len(abs_paths) < 1:
        return jsonify({"ok": False, "msg": "No valid photos to strip"})

    out_abs = make_strip(abs_paths, caption)
    if out_abs is None:
        return jsonify({"ok": False, "msg": "Strip generation failed"})

    out_public = public_path_from_abs(out_abs)
    return jsonify({"ok": True, "msg": "Strip ready!", "path": out_public})


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

    base_name = f"{uuid.uuid4().hex[:8]}_puzzlebase.jpg"
    base_abs = os.path.join(CAPTURE_DIR, base_name)
    img.save(base_abs, quality=92)
    base_public = public_path_from_abs(base_abs)

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
        "base": base_public,
        "solved": False
    }

    return jsonify({
        "ok": True,
        "msg": "Puzzle created!",
        "preview": preview_public,
        "base": base_public,
        "order": order
    })


@app.route("/puzzle_state")
def puzzle_state():
    p = session_data.get("puzzle")
    if not p:
        return jsonify({"active": False})
    return jsonify({
        "active": True,
        "order": p["order"],
        "preview": p["preview"],
        "base": p["base"],
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