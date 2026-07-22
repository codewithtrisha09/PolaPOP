# PolaPOP

PolaPOP is a computer vision–powered photo booth web application. It captures webcam photos, allows sticker customization, and transforms the final image into an interactive puzzle experience.

## Features

- Live webcam preview
- Guided capture flow with Retake / Confirm options
- Sticker overlay support
- Interactive image-tile puzzle generation
- PDF export of the final collage

## Tech Stack

**Backend:** Python, Flask, OpenCV, Pillow, NumPy, ReportLab
**Frontend:** HTML, CSS, JavaScript

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

1. Clone the repository and navigate to the project directory.

2. Install dependencies:
   ```bash
   pip install flask opencv-python pillow reportlab numpy
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open the local server URL displayed in your terminal in a web browser.

## Usage Notes

- Captured images are stored in `static/captures/`.
- Puzzle tiles are generated dynamically from the approved photo.
- Documentation will be expanded to include screenshots, configuration details, and a demo walkthrough.

## Roadmap

- Drag-and-drop sticker placement
- Enhanced puzzle animations and transitions
- Sound effects and audio feedback
- Additional collage layout styles
- Face-detection-based photo mode

