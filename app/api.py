# api.py
# FastAPI backend - frontend uchun alohida kirish nuqtasi.
# main.py'dan mustaqil ishlaydi: `uvicorn app.api:app --reload`
#
# Endpoints:
#   GET  /products      - bazadagi barcha nomlar ro'yxati
#   POST /info          - obyekt haqida ma'lumot (kesh yoki Gemini orqali)
#   WS   /ws/stream      - webcam oqimi + aniqlangan obyektlar (JSON + base64 JPEG)

import base64
import io

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from app.database import find_match, get_info, list_items, save_info
from app.detector import detect_objects
from app.embedder import get_embedding
from app.gemini_info import get_object_info

app = FastAPI(title="Mahsulot Detektor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/products")
def get_products():
    return {"products": list_items()}


@app.post("/info")
async def post_info(
    name: str = Form(...),
    guess_label: str = Form(...),
    image: UploadFile = File(...),
):
    cached = get_info(name)
    if cached:
        return {"name": name, "info": cached, "cached": True}

    image_bytes = await image.read()
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_array = np.array(pil_image)

    info_text = get_object_info(image_array, guess_label)
    save_info(name, info_text)

    return {"name": name, "info": info_text, "cached": False}


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await websocket.send_json({"error": "Kameraga ulanib bo'lmadi"})
        await websocket.close()
        return

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            detections = detect_objects(frame)
            objects = []
            for det in detections:
                embedding = get_embedding(frame, det["box"])
                if embedding is None:
                    continue

                match = find_match(embedding)
                name = match["name"] if match else det["label"]

                objects.append({
                    "box": det["box"],
                    "name": name,
                    "matched": match is not None,
                })

            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                continue
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            await websocket.send_json({
                "frame": frame_b64,
                "objects": objects,
            })
    except WebSocketDisconnect:
        pass
    finally:
        cap.release()
