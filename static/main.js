let capturedPath = null;
let selectedSticker = "✨";
let stickerMode = false;
let currentStickerPath = null;
let capturedPhotos = [];

async function capturePhoto() {
  const res = await fetch("/capture", { method: "POST" });
  const data = await res.json();

  document.getElementById("status").textContent = data.msg || "Captured!";
  if (data.ok) {
    capturedPath = data.path;
    currentStickerPath = data.path;
    document.getElementById("modal").classList.remove("hidden");
    addPhotoPreview(data.path);
  }
}

function retakePhoto() {
  document.getElementById("modal").classList.add("hidden");
  document.getElementById("status").textContent = "Okay, retake it again!";
}

function pickSticker(sticker) {
  selectedSticker = sticker;
  stickerMode = true;
  document.getElementById("status").textContent = `Sticker selected: ${sticker}.`;
}

async function okayPhoto() {
  document.getElementById("modal").classList.add("hidden");

  const res = await fetch("/approve_photo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: capturedPath })
  });

  const data = await res.json();
  if (data.ok) {
    document.getElementById("status").textContent = "Approved! Now making puzzle...";
    currentStickerPath = data.edited_path;
    capturedPhotos.push(data.edited_path);
    renderPuzzleFromApproved();
  }
}

async function addStickerToPhoto(path, x = 120, y = 120) {
  await fetch("/add_sticker", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      path: path,
      text: selectedSticker,
      x: x,
      y: y,
      size: 72
    })
  });
}

function addPhotoPreview(path) {
  const list = document.getElementById("photoList");
  const box = document.createElement("div");
  box.className = "photo-item";

  const img = document.createElement("img");
  img.src = path;
  img.onclick = async () => {
    if (stickerMode) {
      await addStickerToPhoto(path);
    }
  };

  box.appendChild(img);
  list.prepend(box);
}

async function renderPuzzleFromApproved() {
  const res = await fetch("/make_puzzle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: currentStickerPath })
  });

  const data = await res.json();
  document.getElementById("status").textContent = data.msg || "Puzzle ready!";
  renderPuzzle();
}

async function renderPuzzle() {
  const res = await fetch("/puzzle_state");
  const data = await res.json();

  const board = document.getElementById("puzzleBoard");
  board.innerHTML = "";

  if (!data.active) return;

  const order = data.order || [];
  let selected = null;

  order.forEach((tileValue, idx) => {
    const tile = document.createElement("div");
    tile.className = "tile";
    tile.textContent = tileValue + 1;
    tile.onclick = async () => {
      if (selected === null) {
        selected = idx;
        tile.style.outline = "3px solid #ff69ad";
        return;
      }
      await swapTiles(selected, idx);
      selected = null;
    };
    board.appendChild(tile);
  });
}

async function swapTiles(a, b) {
  const res = await fetch("/swap_tile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ a, b })
  });

  const data = await res.json();
  await renderPuzzle();

  if (data.solved) {
    document.getElementById("status").textContent = "Yayyy! Puzzle solved!";
  }
}

async function exportPDF() {
  const res = await fetch("/export_pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ images: capturedPhotos.slice(0, 4) })
  });

  const data = await res.json();
  if (data.ok) {
    const link = document.getElementById("pdfLink");
    link.href = data.pdf;
    link.style.display = "inline-block";
    link.textContent = "Open PDF";
    document.getElementById("status").textContent = "PDF ready!";
    window.open(data.pdf, "_blank");
  }
}

function resetSession() {
  capturedPath = null;
  currentStickerPath = null;
  capturedPhotos = [];
  document.getElementById("photoList").innerHTML = "";
  document.getElementById("puzzleBoard").innerHTML = "";
  document.getElementById("status").textContent = "Session reset. Ready again!";
  document.getElementById("modal").classList.add("hidden");
}

setInterval(renderPuzzle, 1200);