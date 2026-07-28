# PolaPOP 📸

A computer vision–powered photo booth web app — capture a webcam photo, customize it with stickers, and watch it transform into an interactive image-tile puzzle you can solve and export as a PDF collage.

## Features

- **Live webcam preview** with a guided capture flow (Retake / Confirm before committing a shot)
- **Sticker overlay support** for customizing the final photo
- **Interactive puzzle generation** — the approved photo is dynamically sliced into image tiles to solve
- **PDF export** of the final collage using ReportLab

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | Python, Flask, OpenCV, Pillow, NumPy, ReportLab |
| Frontend | HTML, CSS, JavaScript |

## Project Structure

```text
PolaPOP/
├─ app.py
├─ requirements.txt
├─ README.md
├─ templates/
│  ├─ index.html
│  └─ booth.html
├─ static/
│  ├─ style.css
│  ├─ main.js
│  ├─ captures/
│  └─ collages/
```

## Getting Started

### Prerequisites

- Python 3.8+
- A webcam-enabled device

### Installation

1. Clone the repository and navigate into the project directory:
```bash
   git clone https://github.com/codewithtrisha09/PolaPOP.git
   cd PolaPOP
```
2. Install dependencies:
```bash
   pip install -r requirements.txt
```
   *(or manually: `pip install flask opencv-python pillow reportlab numpy`)*
3. Run the application:
```bash
   python app.py
```
4. Open the local server URL shown in your terminal in a web browser.

## How It Works

1. The webcam preview streams live via OpenCV until you capture a frame
2. You review the shot with a Retake/Confirm step, then optionally add stickers
3. The approved image is sliced into tiles server-side to generate a playable puzzle
4. Once solved (or exported), the final image is compiled into a PDF collage with ReportLab

## Usage Notes

- Captured images are stored in `static/captures/`
- Generated collages are stored in `static/collages/`
- Puzzle tiles are generated dynamically from the approved photo — nothing is pre-baked

## Roadmap

- [ ] Drag-and-drop sticker placement
- [ ] Enhanced puzzle animations and transitions
- [ ] Sound effects and audio feedback
- [ ] Additional collage layout styles
- [ ] Face-detection-based photo mode
- [ ] Screenshots and a demo walkthrough in this README

