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
- **MongoDB Atlas** (`pymongo`, `.env`dagi `MONGO_DEV`/`MONGO_PROD` orqali,
  `ENVIRONMENT` o'zgaruvchisiga qarab tanlanadi) — foydalanuvchilar
  (`users`) va tarix (`history`) kolleksiyalari uchun. SQLite'dan MongoDB'ga
  ko'chirildi — UniFinder loyihasidagi `DatabaseModule` uslubiga o'xshab,
  backend ishga tushganda ulanish holati konsolga chiqariladi ("MongoDB
  connected successfully to development db" yoki xato bo'lsa
  "Failed to connect to MongoDB"). `users` kolleksiyasida email **yo'q** —
  faqat `username` (noyob) + `hashed_password` + `is_admin`.
- **JWT** (python-jose yoki PyJWT) — login token'lari
- **Frontend**: Next.js + React (Claude.ai uslubidagi dizayn: chap
  tomonda tarix sidebar'i, asosiy panelda kamera/chat maydoni)

## Loyiha strukturasi (IKKITA ALOHIDA PAPKA)

Bu loyiha endi ikkita mustaqil papkaga bo'lingan (UniFinder loyihasidagi kabi
backend/frontend ajratilgan tuzilma):

- **`~/Desktop/opencv/`** — backend (Python/FastAPI). Ishga tushirish:
  `npm run start:dev` (bu shunchaki `.venv`dagi uvicorn'ni chaqiradigan
  package.json skripti, backend kodining o'zi Python bo'lib qoladi).
- **`~/Desktop/opencv-frontend/`** — frontend (Next.js, alohida papka,
  `opencv/frontend` ichida EMAS). Ishga tushirish: `yarn run dev`.
  Ikkalasi ham bir-biriga HTTP/WebSocket orqali ulanadi
  (frontend -> `http://localhost:8000`).

`opencv/frontend/` papkasidagi eski frontend kodi endi kerak emas — barcha
frontend mantig'i `opencv-frontend/`ga ko'chirilgan.

### opencv/ (backend) fayl strukturasi

```
opencv/
  main.py                 # Mahalliy test skripti (webcam oynasi). Asosiy
                           # aniqlash/tanish logikasi O'ZGARTIRILMASLIGI kerak.
  requirements.txt
  package.json               # (yangi) faqat "start:dev" skripti uchun (npm)
  .env                        # GEMINI_API_KEY, JWT_SECRET_KEY, MONGO_DEV,
                                # MONGO_PROD, ENVIRONMENT (git'ga tushmaydi)
  .gitignore
  product_memory/                 # ChromaDB fayllari (git'ga tushmaydi, obyekt
                                    # embeddinglar shu yerda qoladi - MongoDB'ga
                                    # ko'chirilmaydi, faqat users/history ko'chadi)
  app/
    __init__.py
    detector.py                    # YOLOv8 wrapper (o'zgartirilmaydi)
    embedder.py                     # CLIP wrapper (o'zgartirilmaydi)
    database.py                      # Chroma wrapper: mavjud funksiyalar
                                       # o'zgartirilmaydi, faqat user_id bilan
                                       # ishlaydigan additive parametrlar/funksiyalar
                                       # qo'shiladi
    database_mongo.py                  # (yangi) MongoDB ulanishi (pymongo),
                                         # startup'da ulanish holatini chop etadi
    gemini_info.py                    # Gemini orqali ma'lumot olish
    api.py                              # FastAPI backend: /products, /info,
                                          # /scan, /info/expand, /ws/stream,
                                          # /auth/*, /history, /admin/*
    auth.py                              # parol hash, JWT yaratish/tekshirish
    users_db.py                           # MongoDB: users (+ is_admin), history CRUD
                                            # (SQLite'dan MongoDB'ga ko'chirildi,
                                            # funksiya imzolari o'zgarmadi)
```

### opencv-frontend/ (frontend) fayl strukturasi

```
opencv-frontend/            # Next.js ilova, opencv/ papkasidan MUSTAQIL
  package.json                # yarn bilan boshqariladi (yarn.lock)
  app/
    login/page.tsx
    signup/page.tsx
    admin/page.tsx              # (yangi) faqat is_admin userlar uchun
    page.tsx                     # asosiy: sidebar (tarix) + kamera paneli
  components/
    CameraPanel.tsx
    Sidebar.tsx
  lib/
    api.ts                        # backend bilan bog'lanish (fetch/WS)
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
- Frontend kodi `opencv/` ichida EMAS — mustaqil `~/Desktop/opencv-frontend/`
  papkasida, `yarn` bilan boshqariladi. `opencv/frontend` papkasi endi
  ishlatilmaydi (bo'sh qoldirilishi yoki o'chirilishi mumkin).
- Backendni ishga tushirish uchun `opencv/package.json`dagi
  `npm run start:dev` skripti ishlatiladi — bu FAQAT wrapper, backend
  kodi Python bo'lib qoladi (Node'ga ko'chirilmaydi).
- Admin panel hozircha faqat **ko'rish** huquqiga ega (barcha userlar +
  ularning tarixi) — o'chirish/tahrirlash funksiyalari yo'q.

## Ishga tushirish

```bash
# Backend (~/Desktop/opencv):
cd ~/Desktop/opencv
source .venv/bin/activate && pip install -r requirements.txt   # bir martalik
npm run start:dev          # uvicorn'ni --reload bilan ishga tushiradi (port 8000)

# Mahalliy test (webcam oynasi, autentifikatsiyasiz, alohida):
python main.py

# Frontend (~/Desktop/opencv-frontend, ALOHIDA papka):
cd ~/Desktop/opencv-frontend
yarn install    # bir martalik
yarn run dev
```

Admin sifatida kirish uchun (email/ro'yxatdan o'tish orqali emas, birinchi
marta qo'lda belgilanadi) — MongoDB Atlas'ning veb-interfeysida (Atlas ->
Browse Collections -> `users`) yoki `mongosh` orqali:
```
db.users.updateOne({ username: "SIZNING_USERNAME" }, { $set: { is_admin: true } })
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
- [x] "Ko'proq ma'lumot" (kengaytirilgan tavsif) va "Mahsulotni skanerlash"
      (`/scan`, `/info/expand`) — backend tomoni tasdiqlangan
- [ ] **Loyiha ikkiga bo'linmoqda**: frontend `opencv/frontend`dan
      `~/Desktop/opencv-frontend` (mustaqil papka) ga ko'chirilmoqda,
      `yarn run dev` bilan ishga tushadi. Backendga `package.json` qo'shilib,
      `npm run start:dev` UniFinder uslubida ishlaydi (ichida Python/uvicorn).
- [ ] **Admin panel** (UniFinder admin uslubida): `users` kolleksiyasida
      `is_admin` maydoni (default false, qo'lda MongoDB orqali yoqiladi).
      Faqat ko'rish huquqi: barcha foydalanuvchilar ro'yxati + har
      birining tarixi. O'chirish/bloklash YO'Q (hozircha faqat ko'rish
      rejimi).
- [x] **MongoDB migratsiyasi**: users/history MongoDB Atlas'da (tasdiqlangan,
      Compass orqali ko'rilgan)
- [ ] **Signup'ga telefon raqami maydoni qo'shilmoqda** (NESTAR loyihasidagi
      `memberPhone` uslubida) — `users` kolleksiyasida `phone` maydoni,
      majburiy, tasdiqlash (OTP) YO'Q — shunchaki saqlanadi.
- [x] Admin panel dizayni NESTAR "Member List" uslubiga yaqinlashtirildi
      (statistik kartalar, qidiruv, jadval)
- [ ] **`is_admin` (boolean) -> `role` (string enum: "ADMIN" | "USER") ga
      o'zgartirilmoqda** — NESTAR'dagi `memberType` uslubiga mos kelishi
      uchun. Admin qilish MongoDB Compass'da qo'lda `role` maydonini
      `"ADMIN"` ga o'zgartirish orqali amalga oshiriladi (`is_admin`
      o'rniga). O'zgartirgandan keyin **chiqib qayta kirish** kerak
      (JWT eski token'da eski rolni saqlab qoladi).
