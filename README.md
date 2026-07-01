# PolaPOP

A cute computer vision photo booth web app that captures webcam photos, adds stickers, and turns them into a fun image puzzle.

## Features

- Live webcam preview
- Cute welcome screen
- Photo capture with Retake / Okay flow
- Sticker support
- Real image-tile puzzle board
- PDF export for the final collage

## Tech Stack

- Python
- Flask
- OpenCV
- Pillow
- NumPy
- ReportLab
- HTML, CSS, JavaScript

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

## How to Run

1. Install dependencies:
   ```bash
   pip install flask opencv-python pillow reportlab numpy
   ```

2. Run the app:
   ```bash
   python app.py
   ```

3. Open the local server in your browser.

## Notes

- Captured images are saved in the `static/captures/` folder.
- Puzzle tiles are generated from the approved photo.
- This README will be updated later with screenshots, setup details, and demo info.

## Future Improvements

- Drag-and-drop stickers
- Better puzzle animations
- Sound effects
- More collage styles
- Face-based photo mode
