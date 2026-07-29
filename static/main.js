let capturedPath = null;
let selectedSticker = "✨";
let stickerMode = false;
let currentStickerPath = null;
let capturedPhotos = [];
let puzzleBase = null;
let puzzlePollTimer = null;

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

async function makePolaroid(path) {
  if (!path) return;
  const caption = prompt("Caption for this polaroid (optional):", "") || "";

  const res = await fetch("/make_polaroid", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, caption })
  });

  const data = await res.json();
  if (data.ok) {
    document.getElementById("status").textContent = "Polaroid ready!";
    capturedPhotos.push(data.path);
    addPhotoPreview(data.path);
  } else {
    document.getElementById("status").textContent = data.msg || "Polaroid failed.";
  }
}

async function renderPuzzleFromApproved() {
  const res = await fetch("/make_puzzle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: currentStickerPath })
  });

  const data = await res.json();
  document.getElementById("status").textContent = data.msg || "Puzzle ready!";
  puzzleBase = data.base;
  renderPuzzle();
  startPuzzlePolling();
}

function startPuzzlePolling() {
  if (puzzlePollTimer) clearInterval(puzzlePollTimer);
  puzzlePollTimer = setInterval(renderPuzzle, 1200);
}

async function renderPuzzle() {
  const res = await fetch("/puzzle_state");
  const data = await res.json();

  const board = document.getElementById("puzzleBoard");

  if (!data.active) {
    board.innerHTML = "";
    return;
  }

  puzzleBase = data.base;
  const order = data.order || [];
  const grid = 3;

  board.innerHTML = "";

  order.forEach((tileValue, idx) => {
    const tile = document.createElement("div");
    tile.className = "tile";
    tile.draggable = true;
    tile.dataset.idx = idx;

    const row = Math.floor(tileValue / grid);
    const col = tileValue % grid;

    tile.style.backgroundImage = `url(${puzzleBase})`;
    tile.style.backgroundSize = `${grid * 100}% ${grid * 100}%`;
    tile.style.backgroundPosition = `${(col * 100) / (grid - 1)}% ${(row * 100) / (grid - 1)}%`;

    tile.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", idx);
      tile.classList.add("dragging");
    });

    tile.addEventListener("dragend", () => {
      tile.classList.remove("dragging");
    });

    tile.addEventListener("dragover", (e) => {
      e.preventDefault();
      tile.classList.add("drag-over");
    });

    tile.addEventListener("dragleave", () => {
      tile.classList.remove("drag-over");
    });

    tile.addEventListener("drop", async (e) => {
      e.preventDefault();
      tile.classList.remove("drag-over");
      const fromIdx = parseInt(e.dataTransfer.getData("text/plain"), 10);
      const toIdx = idx;
      if (fromIdx !== toIdx && !Number.isNaN(fromIdx)) {
        await swapTiles(fromIdx, toIdx);
      }
    });

    board.appendChild(tile);
  });

  if (data.solved && puzzlePollTimer) {
    clearInterval(puzzlePollTimer);
    puzzlePollTimer = null;
  }
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
  puzzleBase = null;
  if (puzzlePollTimer) {
    clearInterval(puzzlePollTimer);
    puzzlePollTimer = null;
  }
  document.getElementById("photoList").innerHTML = "";
  document.getElementById("puzzleBoard").innerHTML = "";
  document.getElementById("status").textContent = "Session reset. Ready again!";
  document.getElementById("modal").classList.add("hidden");
}