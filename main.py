# main.py
# Mahsulot aniqlash + tanish + eslab qolish dasturi.
#
# Ishlash mantig'i:
#   1. Webcam'dan kadr olinadi
#   2. YOLOv8 kadrdagi obyektlarni topadi (detector.py) va umumiy nom beradi
#      (masalan "bottle", "cup")
#   3. Har bir topilgan obyekt CLIP orqali vektorga aylantiriladi (embedder.py)
#   4. Bu vektor bazadagi (database.py) saqlangan narsalar bilan solishtiriladi:
#        - Agar mos kelsa -> saqlangan aniq nom ekranda ko'rsatiladi
#        - Agar mos kelmasa -> "Yangi: <taxminiy nom>" deb ko'rsatiladi va
#          foydalanuvchi 's' tugmasini bosib aniq nom kiritishi mumkin
#   5. Kiritilgan nom + vektor bazaga saqlanadi -> keyingi safar tizim
#      shu narsani avtomatik taniydi.
#
# Boshqaruv:
#   q - dasturdan chiqish
#   s - ekrandagi eng oxirgi "Yangi: ..." obyektga nom berish

import cv2

from app.detector import detect_objects
from app.embedder import get_embedding
from app.database import find_match, save_item

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("XATO: Kameraga ulanib bo'lmadi (cap.isOpened() == False).")
    print("Ehtimoliy sabab: macOS Terminal uchun kamera ruxsati yo'q yoki")
    print("kamera boshqa dastur tomonidan band qilingan.")
    print("Tekshiring: System Settings -> Privacy & Security -> Camera")
    print("Terminal (yoki iTerm) ro'yxatda borligini va yoqilganini tasdiqlang.")
    raise SystemExit(1)

# Eng oxirgi tanilmagan (nomlanmagan) obyektning joylashuvi va taxminiy nomi.
# 's' tugmasi bosilganda shu obyektga nom beriladi.
pending_box = None
pending_guess = None

print("Dastur ishga tushdi.")
print("  q - chiqish")
print("  s - eng oxirgi 'Yangi: ...' obyektga nom berish")

while True:
    success, frame = cap.read()  # True, False | Boolean
    if not success:
        break

    detections = detect_objects(frame)
    pending_box = None
    pending_guess = None

    for det in detections:
        x1, y1, x2, y2 = det["box"]
        embedding = get_embedding(frame, det["box"])
        if embedding is None:
            continue

        match = find_match(embedding)
        if match:
            display_name = match["name"]
            color = (0, 255, 0)  # yashil - tanildi
        else:
            display_name = f"Yangi: {det['label']} ('s' - nom bering)"
            color = (0, 165, 255)  # to'q sariq - tanilmadi
            pending_box = det["box"]
            pending_guess = det["label"]

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame, display_name, (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
        )

    cv2.imshow("Mahsulot Detektor", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):  # 'q' tugmasi bosilganda chiqish
        break
    elif key == ord('s') and pending_box is not None:
        name = input(f"[{pending_guess}] Bu narsaning nomini kiriting: ").strip()
        if name:
            embedding = get_embedding(frame, pending_box)
            if embedding is not None:
                save_item(name, embedding, guess_label=pending_guess or "")
                print(f"'{name}' bazaga saqlandi.")
        pending_box = None
        pending_guess = None

cap.release()  # Ochiq qolgan oynalrni yopish uchun
cv2.destroyAllWindows()
