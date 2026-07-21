# Loyiha: AI Mahsulot Detektori (opencv)

## Loyiha haqida

Bu — webcam orqali ishlaydigan, obyektlarni real-vaqtda aniqlaydigan, tanib
oladigan va "eslab qoladigan" AI detektor loyihasi. Maqsad: kameraga biror
narsa (mahsulot, buyum) ko'rsatilganda, tizim:

1. Uni umumiy toifasi bo'yicha aniqlaydi (masalan "bottle", "cup", "phone").
2. Agar bu narsani avval ko'rgan bo'lsa (embedding-vektor solishtirish orqali),
   siz bergan aniq nomini eslab, ko'rsatadi.
3. Agar birinchi marta ko'rayotgan bo'lsa, foydalanuvchidan nom so'raydi va
   uni bazasiga (lokal, diskda) saqlab qo'yadi — keyingi safar avtomatik
   taniydi.
4. (Rivojlanmoqda) Foydalanuvchi "ma'lumot olish" tugmasini bossa, Gemini
   (Google AI Studio) orqali obyekt haqida qisqacha tabiiy tildagi
   ma'lumot oladi va uni ham keshlaydi (keyingi safar qayta so'ramaslik uchun).
5. (Rejalashtirilgan) Frontend orqali jonli video oqimi, tanilgan
   mahsulotlar ro'yxati va "ma'lumot olish" tugmasi ko'rsatiladi.

## Texnik stack

- **Python 3.14**, virtual environment: `.venv/`
- **OpenCV (cv2)** — webcam'dan video olish, oyna ko'rsatish
- **Ultralytics YOLOv8** (`yolov8n.pt`, pretrained COCO) — obyektlarni
  aniqlash (bounding box + umumiy toifa nomi)
- **open_clip (CLIP ViT-B-32)** — crop qilingan obyekt rasmini vektorga
  aylantirish (instance-level "bu aynan shu narsami?" solishtirish uchun)
- **ChromaDB** (PersistentClient, `product_memory/` papkasida) — vektor
  bazasi: nom + embedding + (keyinchalik) Gemini'dan olingan ma'lumot
- **FastAPI + Uvicorn** (qo'shilmoqda) — backend API, frontend uchun
- **Google Gemini API** (`google-generativeai`, `.env`dagi
  `GEMINI_API_KEY` orqali) — obyekt haqida tabiiy tildagi ma'lumot olish
  (bepul tier, Google AI Studio orqali olingan)

## Fayl strukturasi

```
opencv/
  main.py                 # Mahalliy test skripti: webcam oynasi orqali
                           # to'g'ridan-to'g'ri ishga tushiriladi (cv2.imshow).
                           # Bu faylning asosiy aniqlash/tanish logikasi
                           # O'ZGARTIRILMASLIGI kerak.
  requirements.txt          # Barcha kerakli Python kutubxonalari
  .env                        # GEMINI_API_KEY (git'ga tushmaydi, .gitignore'da)
  .gitignore
  product_memory/              # ChromaDB fayllari (avtomatik yaratiladi, git'ga tushmaydi)
  app/
    __init__.py
    detector.py                 # YOLOv8 wrapper: detect_objects(frame) -> list[{box, label, conf}]
    embedder.py                  # CLIP wrapper: get_embedding(frame, box) -> np.ndarray | None
    database.py                   # Chroma wrapper: find_match(embedding), save_item(name, embedding, guess_label), list_items()
    gemini_info.py                 # (qo'shilmoqda) Gemini orqali obyekt haqida ma'lumot olish
    api.py                          # (qo'shilmoqda) FastAPI backend: /products, /info, WebSocket /ws/stream
```

## Muhim qoidalar (Claude Code uchun)

- `detector.py`, `embedder.py`, `database.py` dagi **mavjud funksiyalar va
  ularning ishlash mantig'i o'zgartirilmasin** — faqat additive (qo'shimcha)
  yangi funksiyalar qo'shish mumkin (masalan, `database.py`ga
  `save_info()`/`get_info()` kabi yangi funksiya qo'shish — mavjudlarini
  o'zgartirmasdan).
- `main.py` — mahalliy sinov skripti, u ham o'zgartirilmaydi. Yangi
  FastAPI/Gemini funksionalligi **alohida** `app/api.py` faylida, yangi
  kirish nuqtasi sifatida quriladi (masalan `uvicorn app.api:app` orqali
  ishga tushadi), `main.py`dan mustaqil.
- API kalitlar hech qachon kodga hardcode qilinmasin — doim `.env` +
  `python-dotenv` orqali o'qilsin.
- Yangi kutubxonalar `requirements.txt`ga qo'shilsin.

## Ishga tushirish

```bash
cd ~/Desktop/opencv
source .venv/bin/activate
pip install -r requirements.txt

# Mahalliy test (webcam oynasi):
python main.py

# Backend API (qo'shilgandan keyin):
uvicorn app.api:app --reload
```

## Hozirgi holat

- [x] YOLOv8 + CLIP + Chroma asosidagi aniqlash/tanish/eslab qolish ishlaydi
      (`main.py` orqali, webcam oynasida sinovdan o'tgan)
- [ ] Gemini API integratsiyasi (`app/gemini_info.py`) — obyekt haqida
      ma'lumot olish va keshlash
- [ ] FastAPI backend (`app/api.py`) — frontend uchun API/WebSocket
- [ ] Frontend (keyingi bosqich)
