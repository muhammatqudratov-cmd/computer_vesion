# api.py
# FastAPI backend - frontend uchun alohida kirish nuqtasi.
# main.py'dan mustaqil ishlaydi: `uvicorn app.api:app --reload`
#
# Endpoints:
#   POST /auth/signup    - ro'yxatdan o'tish (username + parol) -> JWT
#   POST /auth/login     - kirish (username + parol) -> JWT
#   GET  /auth/me         - joriy foydalanuvchi (himoyalangan)
#   GET  /history          - joriy foydalanuvchi tarixi (himoyalangan)
#   GET  /products      - bazadagi barcha nomlar ro'yxati (himoyalangan)
#   POST /info          - obyekt haqida ma'lumot (kesh yoki Gemini orqali) (himoyalangan)
#   POST /scan           - butun kadrni Gemini'ga yuborib mustaqil aniqlash
#                           (YOLO'ning 80 COCO toifasidan qat'iy nazar) (himoyalangan)
#   POST /info/expand     - mavjud qisqa ma'lumotni kengaytirilgan tavsifga
#                            almashtiradi ("Ko'proq ma'lumot" tugmasi) (himoyalangan)
#   WS   /ws/stream      - webcam oqimi + aniqlangan obyektlar (JSON + base64 JPEG) (himoyalangan)

import base64
import io

import cv2
import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import find_match, get_info, list_items, save_info, save_item
from app.detector import detect_objects
from app.embedder import get_embedding
from app.gemini_info import get_expanded_info, get_object_info, identify_and_describe
from app.users_db import add_history_entry, create_user, get_history_for_user, get_user_by_username

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


class SignupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/signup")
def signup(payload: SignupRequest):
    hashed = hash_password(payload.password)
    try:
        create_user(payload.username, hashed)
    except ValueError:
        raise HTTPException(status_code=400, detail="Bu username allaqachon band")

    token = create_access_token({"sub": payload.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = get_user_by_username(payload.username)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Username yoki parol noto'g'ri")

    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"]}


@app.get("/history")
def read_history(current_user: dict = Depends(get_current_user)):
    return {"history": get_history_for_user(current_user["id"])}


@app.get("/products")
def get_products(current_user: dict = Depends(get_current_user)):
    return {"products": list_items(user_id=str(current_user["id"]))}


@app.post("/info")
async def post_info(
    name: str = Form(...),
    guess_label: str = Form(...),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["id"])

    cached = get_info(name, user_id=user_id)
    if cached:
        return {"name": name, "info": cached, "cached": True}

    image_bytes = await image.read()
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_array = np.array(pil_image)

    info_text = get_object_info(image_array, guess_label)
    save_info(name, info_text, user_id=user_id)
    add_history_entry(current_user["id"], name, guess_label, info_text)

    return {"name": name, "info": info_text, "cached": False}


@app.post("/scan")
async def scan_object(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Butun kadrni (YOLO'ning cheklangan 80 ta COCO toifasidan qat'iy nazar)
    to'g'ridan-to'g'ri Gemini'ga yuboradi: obyektni mustaqil aniqlaydi va
    tavsif beradi, natijani (nom + CLIP vektori + ma'lumot) shu foydalanuvchiga
    tegishli holda saqlaydi va tarixga qo'shadi."""
    user_id = str(current_user["id"])

    image_bytes = await image.read()
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_array = np.array(pil_image)

    result = identify_and_describe(image_array)
    name = result["name"]
    info_text = result["info"]

    frame_bgr = image_array[:, :, ::-1]
    height, width = frame_bgr.shape[:2]
    embedding = get_embedding(frame_bgr, (0, 0, width, height))
    if embedding is not None:
        save_item(name, embedding, guess_label="", user_id=user_id)

    save_info(name, info_text, user_id=user_id)
    add_history_entry(current_user["id"], name, "", info_text)

    return {"name": name, "info": info_text}


@app.post("/info/expand")
async def expand_info(
    name: str = Form(...),
    image: UploadFile | None = File(None),
    current_user: dict = Depends(get_current_user),
):
    """Mavjud qisqa ma'lumotni Gemini orqali kengaytirilgan tavsifga
    almashtiradi. Agar bu nom uchun hali hech qanday ma'lumot keshlanmagan
    bo'lsa, rasm talab qilinadi (avval qisqa tavsif olinadi, so'ng shuning
    ustiga kengaytiriladi)."""
    user_id = str(current_user["id"])
    existing_info = get_info(name, user_id=user_id)

    if not existing_info:
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Bu obyekt uchun avvalgi ma'lumot topilmadi - rasm yuborish kerak",
            )
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(pil_image)
        existing_info = get_object_info(image_array, name)

    expanded = get_expanded_info(name, existing_info)
    save_info(name, expanded, user_id=user_id)

    return {"name": name, "info": expanded}


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket, current_user: dict = Depends(get_current_user)):
    await websocket.accept()
    user_id = str(current_user["id"])

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

                match = find_match(embedding, user_id=user_id)
                name = match["name"] if match else det["label"]

                objects.append({
                    "box": det["box"],
                    "name": name,
                    "guess_label": det["label"],
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
