# embedder.py
# Crop qilingan obyekt rasmini "barmoq izi" vektoriga aylantiradi (CLIP model).
# Bir xil narsaning rasmlari deyarli bir xil vektor beradi, shuning uchun
# bu vektorlar orqali "bu narsani avval ko'rganmizmi?" degan savolga javob
# topish mumkin (database.py shu vektorlarni solishtiradi).

import numpy as np
import torch
from PIL import Image
import open_clip

_model = None
_preprocess = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def load_model():
    """CLIP modelini bir marta yuklaydi. Birinchi ishga tushirishda
    og'irliklar internetdan avtomatik yuklab olinadi."""
    global _model, _preprocess
    if _model is None:
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        _model.to(_device)
        _model.eval()
    return _model, _preprocess


def get_embedding(frame_bgr: np.ndarray, box) -> np.ndarray | None:
    """Kadrning berilgan box qismini kesib olib, CLIP orqali vektorga aylantiradi.

    frame_bgr: to'liq kadr (OpenCV BGR formatida)
    box: (x1, y1, x2, y2)

    Qaytaradi: normallashtirilgan vektor (numpy array) yoki crop bo'sh bo'lsa None.
    """
    model, preprocess = load_model()

    x1, y1, x2, y2 = box
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    crop_rgb = crop[:, :, ::-1]  # BGR -> RGB
    image = Image.fromarray(crop_rgb)
    tensor = preprocess(image).unsqueeze(0).to(_device)

    with torch.no_grad():
        embedding = model.encode_image(tensor)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)

    return embedding.cpu().numpy()[0]
