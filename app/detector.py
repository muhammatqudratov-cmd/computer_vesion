# detector.py
# Kadr ichidan obyektlarni topish uchun modul.
# YOLOv8 (pretrained, COCO) yordamida umumiy obyektlarni aniqlaydi:
# har bir topilgan obyekt uchun joylashuv (box) va umumiy toifa nomini
# (masalan "bottle", "cup", "cell phone") qaytaradi.
#
# Bu "umumiy nom" keyinchalik yangi obyektga taxminiy nom sifatida
# ko'rsatiladi (masalan "Yangi: bottle"), foydalanuvchi esa aniq nom
# beradi (masalan "Mening choy termosim").

from ultralytics import YOLO

_model = None


def load_model():
    """YOLOv8 modelini bir marta yuklaydi (keyingi chaqiruvlarda qayta ishlatadi).
    Birinchi ishga tushirishda 'yolov8n.pt' fayli internetdan avtomatik yuklab olinadi."""
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
    return _model


def detect_objects(frame, conf_threshold: float = 0.4):
    """Berilgan kadrdan obyektlarni topadi.

    Qaytaradi: har biri {"box": (x1, y1, x2, y2), "label": str, "conf": float}
    ko'rinishidagi lug'atlardan iborat ro'yxat.
    """
    model = load_model()
    results = model(frame, verbose=False)[0]

    detections = []
    for box in results.boxes:
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        label = model.names[cls_id]

        detections.append({
            "box": (x1, y1, x2, y2),
            "label": label,
            "conf": conf,
        })

    return detections
