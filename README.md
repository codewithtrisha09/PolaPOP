```markdown
# 📸 PolaPOP

A kawaii-themed webcam photo booth built with Flask + OpenCV — capture photos, sticker them up, turn them into polaroids, solve a drag-and-drop photo puzzle, and export a printable PDF collage.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.10-blue)
![Flask](https://img.shields.io/badge/flask-3.x-black)

## ✨ Features

- **Live webcam feed** streamed via Flask (MJPEG) using OpenCV
- **Capture → Retake / Approve** flow with a confirmation modal
- **Sticker overlay** — pick an emoji sticker, click anywhere on a captured photo to stamp it
- **Polaroid export** — wraps any captured photo in a classic white-border polaroid frame with an optional caption, generated server-side with Pillow
- **Photo puzzle** — approved photos are auto-sliced into a 3×3 grid of *real image tiles* (not placeholders) and shuffled
- **Drag-and-drop puzzle solving** — native HTML5 drag events, no click-to-select
- **PDF export** — bundles up to 4 captured photos into a printable collage PDF via ReportLab
- **Session reset** — clear photos, puzzle state, and captures to start fresh

## 🛠️ Tech Stack

- **Backend:** Flask, OpenCV (`cv2`), NumPy, Pillow, ReportLab
- **Frontend:** Vanilla JS, HTML5 Drag & Drop API, CSS Grid
- **No database** — session state is kept in-memory (`session_data` dict) for simplicity

## 📁 Project Structure

```

PolaPop_puzzle/
├── app.py
├── static/
│   ├── main.js
│   ├── style.css
│   ├── captures/
│   ├── collages/
│   └── polaroids/
└── templates/
    ├── index.html
    └── booth.html

````

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A working webcam

### Installation

```bash
git clone https://github.com/codewithtrisha09/PolaPOP.git
cd PolaPOP

pip install flask opencv-python numpy pillow reportlab
````

### Run

```bash
python app.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser. Move your mouse on the welcome screen to enter the booth.

> ⚠️ Close any other app (Zoom, Teams, Windows Camera) using your webcam first — `cv2.VideoCapture(0)` can't share the camera.

## 🎮 How to Use

1. Land on the welcome screen, move your mouse to enter the booth
2. Click **📸 Capture** to take a photo
3. In the confirmation modal, choose:
   - **Retake** — discard and try again
   - **Okay** — approve the photo, which auto-generates a 3×3 puzzle
   - **🖼️ Polaroid** — frame the photo as a polaroid with an optional caption
4. Pick a sticker and click on any captured photo to stamp it
5. Drag and drop puzzle tiles to reassemble the photo
6. Click **Download PDF** to export your captured photos as a collage

## 🔮 Roadmap

- [ ] Random tile rotation for a "tossed on a table" polaroid look
- [ ] Stack/fan layout for the photo list instead of a grid
- [ ] Configurable puzzle grid size (4×4, 5×5)
- [ ] Deploy-ready config (env-based camera index, production WSGI server)

## 📄 License

MIT

```

Want me to also add a live-demo GIF placeholder or badges linking to your actual repo/issues once it's pushed?