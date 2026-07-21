# gemini_info.py
# Gemini API orqali obyekt haqida qisqacha ma'lumot olish.
# Natija database.py'da keshlanadi (save_info/get_info) - shu sabab bu funksiya
# har safar emas, faqat yangi/keshlanmagan obyektlar uchun chaqiriladi.

import os

import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
_MODEL_NAME = "gemini-3.5-flash"

_model = None


def _load_model():
    global _model
    if _model is None:
        if not _GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY .env faylida topilmadi")
        genai.configure(api_key=_GEMINI_API_KEY)
        _model = genai.GenerativeModel(_MODEL_NAME)
    return _model


def get_object_info(image: np.ndarray, label: str) -> str:
    """Berilgan rasm (numpy, BGR yoki RGB) va taxminiy nom (label) asosida
    Gemini'dan obyekt haqida qisqacha o'zbekcha ma'lumot so'raydi.

    Internet yo'q, kvota tugagan yoki boshqa xatolik bo'lsa, dasturni
    to'xtatmaydi - o'rniga tushunarli xato matnini qaytaradi."""
    try:
        model = _load_model()

        pil_image = Image.fromarray(image)  # `image` RGB tartibida deb kutiladi

        prompt = (
            f"Look carefully at the image. A rough automatic guess suggested this "
            f"object might be '{label}', but that guess may be wrong — verify it "
            "against what you actually see in the image and correct it if needed. "
            "Then, in Uzbek, give a short (3-4 sentence) description of the object "
            "you actually identified: what it is and what it's typically used for."
        )

        response = model.generate_content([prompt, pil_image])
        return response.text.strip()

    except Exception as e:
        return f"Ma'lumot olishda xatolik yuz berdi: {e}"
