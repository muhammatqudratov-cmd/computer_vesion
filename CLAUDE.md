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
4. Foydalanuvchi "ma'lumot olish" tugmasini bossa, Gemini (Google AI Studio)
   orqali obyekt haqida qisqacha tabiiy tildagi ma'lumot oladi va uni ham
   keshlaydi (keyingi safar qayta so'ramaslik uchun).
5. **(Yangi, qurilmoqda) Ko'p foydalanuvchili tizim**: sayt Claude.ai kabi
   dizaynga ega bo'ladi — foydalanuvchi ro'yxatdan o'tadi/kiradi (faqat
   **username + parol**, email yo'q — shuning uchun email tasdiqlash yoki
   "parolni unutdim" funksiyalari mavjud emas), faqat shundan keyin
   "Kamerani ishga tushirish" tugmasi ko'rinadi. Har bir foydalanuvchining
   avval skanerlagan/nomlagan narsalari va ular haqida olingan ma'lumotlar
   shu foydalanuvchiga xos tarzda saqlanadi va chap tomondagi sidebar'da
   (Claude'dagi chat tarixi kabi) ro'yxat sifatida ko'rinadi — bosilganda
   o'sha yozuvning tafsilotlari ochiladi.

## Texnik stack

- **Python 3.14**, virtual environment: `.venv/`
- **OpenCV (cv2)** — webcam'dan video olish (mahalliy test uchun, `main.py`)
- **Ultralytics YOLOv8** (`yolov8n.pt`, pretrained COCO) — obyektlarni
  aniqlash (bounding box + umumiy toifa nomi)
- **open_clip (CLIP ViT-B-32)** — crop qilingan obyekt rasmini vektorga
  aylantirish (instance-level "bu aynan shu narsami?" solishtirish uchun)
- **ChromaDB** (PersistentClient, `product_memory/` papkasida) — vektor
  bazasi: nom + embedding + Gemini'dan olingan ma'lumot. Har bir yozuv
  endi `user_id` maydoniga ega bo'ladi (foydalanuvchiga xos filtrlash uchun).
- **FastAPI + Uvicorn** — backend API, WebSocket, autentifikatsiya
- **Google Gemini API** (`google-generativeai`, `.env`dagi `GEMINI_API_KEY`
  orqali, model: `gemini-3.5-flash`) — obyekt haqida tabiiy tildagi
  ma'lumot olish
- **SQLite** (`app.db`, yangi) — foydalanuvchilar (`users`) va tarix
  (`history`) jadvallari uchun (Chroma bunga mos emas, relyatsion
  ma'lumotlar uchun SQLite ishlatiladi). `users` jadvalida email **yo'q** —
  faqat `username` (noyob) + `hashed_password`.
- **JWT** (python-jose yoki PyJWT) — login token'lari
- **Frontend**: Next.js + React (Claude.ai uslubidagi dizayn: chap
  tomonda tarix sidebar'i, asosiy panelda kamera/chat maydoni)

## Fayl strukturasi

```
opencv/
  main.py                 # Mahalliy test skripti (webcam oynasi). Asosiy
                           # aniqlash/tanish logikasi O'ZGARTIRILMASLIGI kerak.
  requirements.txt
  .env                        # GEMINI_API_KEY, JWT_SECRET_KEY (git'ga tushmaydi)
  .gitignore
  app.db                        # SQLite: users, history (git'ga tushmaydi)
  product_memory/                 # ChromaDB fayllari (git'ga tushmaydi)
  app/
    __init__.py
    detector.py                    # YOLOv8 wrapper (o'zgartirilmaydi)
    embedder.py                     # CLIP wrapper (o'zgartirilmaydi)
    database.py                      # Chroma wrapper: mavjud funksiyalar
                                       # o'zgartirilmaydi, faqat user_id bilan
                                       # ishlaydigan additive parametrlar/funksiyalar
                                       # qo'shiladi
    gemini_info.py                    # Gemini orqali ma'lumot olish
    api.py                              # FastAPI backend: /products, /info,
                                          # /ws/stream, /auth/*, /history
    auth.py                              # (yangi) parol hash, JWT yaratish/tekshirish
    users_db.py                           # (yangi) SQLite: users (username-based) + history CRUD
  frontend/                                # (yangi) Next.js ilova
    - /login, /signup sahifalari (username + parol)
    - / (asosiy, faqat login qilingandan keyin): sidebar (tarix) +
      kamera/chat paneli
```

## Muhim qoidalar (Claude Code uchun)

- `detector.py`, `embedder.py` dagi mavjud funksiyalar o'zgartirilmasin.
- `database.py` dagi **mavjud funksiyalarning imzosi va asosiy ishlash
  mantig'i buzilmasin** — `user_id` kabi yangi parametrlarni **default
  qiymat bilan** (masalan `user_id: str | None = None`) qo'shish mumkin,
  shunda `main.py` (user_id bermaydi) hamon eskicha ishlayveradi.
- `main.py` — mahalliy sinov skripti, o'zgartirilmaydi.
- Parollar hech qachon ochiq matnda saqlanmasin — faqat hash (bcrypt/argon2)
  orqali.
- JWT maxfiy kaliti, Gemini API kalit — barchasi `.env` orqali, hech qachon
  kodga yozilmasin.
- Autentifikatsiya faqat **username + parol** orqali — email maydoni yo'q,
  email tasdiqlash yoki parolni tiklash funksiyalari yo'q.
- Frontend dizayni Claude.ai'ga o'xshash: chap sidebar (tarix ro'yxati,
  har bir yozuv bosilganda tafsilotlari ochiladi), o'ng/asosiy qismda
  kontent. "Kamerani ishga tushirish" tugmasi faqat login qilingan
  foydalanuvchiga ko'rinadi.

## Ishga tushirish

```bash
cd ~/Desktop/opencv
source .venv/bin/activate
pip install -r requirements.txt

# Mahalliy test (webcam oynasi, autentifikatsiyasiz):
python main.py

# Backend API:
uvicorn app.api:app --reload --port 8000

# Frontend (qo'shilgandan keyin):
cd frontend && npm install && npm run dev
```

## Hozirgi holat

- [x] YOLOv8 + CLIP + Chroma asosidagi aniqlash/tanish/eslab qolish ishlaydi
- [x] Gemini API integratsiyasi (`app/gemini_info.py`) — tasdiqlangan, ishlaydi
- [x] FastAPI backend (`app/api.py`) — `/products`, `/info`, `/ws/stream` —
      tasdiqlangan, ishlaydi
- [x] Git repo sozlangan (`main` + `develop` branchlar, GitHub'ga ulangan)
- [ ] Ko'p foydalanuvchili autentifikatsiya (signup/login, username + parol) — qurilmoqda
- [ ] Foydalanuvchiga xos tarix (`history`) va Chroma yozuvlarini
      `user_id` bilan filtrlash — qurilmoqda
- [x] Claude.ai uslubidagi frontend (login gate, sidebar tarix, kamera
      paneli) — asosiy oqim ishlaydi
- [ ] **Muhim cheklov aniqlandi**: YOLOv8 faqat 80 ta COCO toifasini biladi
      (masalan "kitob" ular orasida yo'q) — shuning uchun COCO'da bo'lmagan
      narsalar butunlay aniqlanmay qoladi. Yechim: "Mahsulotni skanerlash"
      tugmasi butun kadrni (YOLO natijasidan qat'iy nazar) to'g'ridan-to'g'ri
      Gemini'ga yuborib, u nima ekanini mustaqil aniqlaydi — qurilmoqda.
- [ ] "Ko'proq ma'lumot" (kengaytirilgan tavsif) tugmasi — qurilmoqda
