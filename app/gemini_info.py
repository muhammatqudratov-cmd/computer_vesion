# gemini_info.py
# Gemini API orqali obyekt haqida qisqacha ma'lumot olish.
# Natija database.py'da keshlanadi (save_info/get_info) - shu sabab bu funksiya
# har safar emas, faqat yangi/keshlanmagan obyektlar uchun chaqiriladi.

import os
import re

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


_NOM_RE = re.compile(r"NOM\s*:\s*(.+)", re.IGNORECASE)
_INFO_RE = re.compile(r"MA.LUMOT\s*:\s*(.+)", re.IGNORECASE | re.DOTALL)


def _parse_identify_response(text: str) -> tuple[str, str]:
    name_match = _NOM_RE.search(text)
    info_match = _INFO_RE.search(text)

    name = name_match.group(1).splitlines()[0].strip() if name_match else ""
    info = info_match.group(1).strip() if info_match else ""

    if not info:
        # Model kutilgan formatda javob bermagan bo'lsa, butun matnni
        # tavsif sifatida ishlatamiz - hech narsa yo'qotilmasin.
        info = text.strip()
    if not name:
        name = "Noma'lum obyekt"

    return name, info


def identify_and_describe(image: np.ndarray) -> dict:
    """Butun kadrni (YOLO'ning 80 ta COCO toifasidan qat'iy nazar) Gemini'ga
    yuboradi: obyektni mustaqil aniqlaydi va u haqida qisqacha tavsif beradi -
    bittagina Gemini chaqiruvida.

    `image` RGB tartibida deb kutiladi (get_object_info bilan bir xil
    konventsiya). Qaytaradi: {"name": str, "info": str}."""
    try:
        model = _load_model()

        pil_image = Image.fromarray(image)

        prompt = (
            "Look carefully at the image and identify the main object/product in "
            "it - do not limit yourself to any fixed category list, describe "
            "whatever you actually see. Respond in Uzbek, in exactly this format "
            "and nothing else:\n"
            "NOM: <qisqa nom, 1-3 so'z>\n"
            "MA'LUMOT: <3-4 gapli qisqacha tavsif - bu nima va odatda nima uchun "
            "ishlatiladi>"
        )

        response = model.generate_content([prompt, pil_image])
        name, info = _parse_identify_response(response.text.strip())
        return {"name": name, "info": info}

    except Exception as e:
        return {
            "name": "Noma'lum obyekt",
            "info": f"Ma'lumot olishda xatolik yuz berdi: {e}",
        }


def get_expanded_info(name: str, existing_info: str) -> str:
    """Berilgan nom va avvalgi qisqa ma'lumot asosida Gemini'dan kengaytirilgan,
    batafsilroq tavsif so'raydi (faqat matn asosida, rasmsiz - "Ko'proq
    ma'lumot" tugmasi uchun). Natija save_info orqali eski qisqa ma'lumotning
    o'rniga saqlanadi (chaqiruvchi tomonda)."""
    try:
        model = _load_model()

        prompt = (
            f"The object is: '{name}'. Here is a short description already given: "
            f"\"{existing_info}\"\n\n"
            "Now, in Uzbek, write a longer and more detailed description (6-8 "
            "sentences): include more specifics such as how it works, interesting "
            "facts, common types/variations if relevant, brief history or usage "
            "tips - without simply repeating the short description word for word."
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"Ma'lumot olishda xatolik yuz berdi: {e}"
