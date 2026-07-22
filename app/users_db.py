# users_db.py
# Foydalanuvchilar (users) va ularning tarixi (history) uchun MongoDB
# kolleksiyalari (database_mongo.py'dagi `db` handle orqali). Bu ChromaDB
# vektor bazasi (database.py) bilan bir xil narsa emas - u yerda
# instance-level "bu narsani ko'rganmiz-ganmi" solishtirish, bu yerda esa
# relyatsion-uslub ma'lumotlar (login, tarix ro'yxati) saqlanadi.
#
# SQLite'dan MongoDB'ga ko'chirildi - har bir funksiyaning nomi, parametrlari
# va qaytish shakli o'zgarmadi. Id'lar SQLite'dagi kabi butun sonli
# (auto-increment, `counters` kolleksiyasi orqali) - shunda api.py'dagi
# JWT/id solishtirishlari va route tiplari (masalan `user_id: int`)
# o'zgarishsiz ishlayveradi.

from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.database_mongo import db

_users = db["users"] if db is not None else None
_history = db["history"] if db is not None else None
_counters = db["counters"] if db is not None else None

if _users is not None:
    _users.create_index("username", unique=True)


def _migrate_role_field():
    """Bir martalik, idempotent migratsiya: `is_admin` (boolean) dan
    `role` (string enum) ga o'tish. Har startup'da xavfsiz qayta ishga
    tushirish mumkin - faqat `role` maydoni hali yo'q hujjatlarga tegadi."""
    _users.update_many(
        {"role": {"$exists": False}, "is_admin": True},
        {"$set": {"role": "ADMIN"}},
    )
    _users.update_many(
        {"role": {"$exists": False}},
        {"$set": {"role": "USER"}},
    )


if _users is not None:
    _migrate_role_field()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _next_id(counter_name: str) -> int:
    doc = _counters.find_one_and_update(
        {"_id": counter_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]


def _user_to_dict(doc) -> dict:
    return {
        "id": doc["_id"],
        "username": doc["username"],
        "hashed_password": doc["hashed_password"],
        "phone": doc.get("phone", ""),
        "created_at": doc["created_at"],
        "role": doc.get("role", "USER"),
    }


def _history_to_dict(doc) -> dict:
    return {
        "id": doc["_id"],
        "user_id": doc["user_id"],
        "object_name": doc.get("object_name"),
        "guess_label": doc.get("guess_label"),
        "info_text": doc.get("info_text"),
        "created_at": doc["created_at"],
    }


def create_user(username: str, hashed_password: str, phone: str) -> int:
    """Yangi foydalanuvchi yozuvini yaratadi, id'sini qaytaradi.
    Agar username band bo'lsa ValueError ko'taradi (chaqiruvchi buni
    HTTP 400'ga aylantiradi)."""
    user_id = _next_id("users")
    try:
        _users.insert_one({
            "_id": user_id,
            "username": username,
            "hashed_password": hashed_password,
            "phone": phone,
            "created_at": _now(),
            "role": "USER",
        })
        return user_id
    except DuplicateKeyError:
        raise ValueError(f"Username allaqachon band: {username}")


def get_user_by_username(username: str):
    doc = _users.find_one({"username": username})
    return _user_to_dict(doc) if doc else None


def get_user_by_id(user_id: int):
    doc = _users.find_one({"_id": user_id})
    return _user_to_dict(doc) if doc else None


def add_history_entry(user_id: int, object_name: str, guess_label: str, info_text: str) -> int:
    entry_id = _next_id("history")
    _history.insert_one({
        "_id": entry_id,
        "user_id": user_id,
        "object_name": object_name,
        "guess_label": guess_label,
        "info_text": info_text,
        "created_at": _now(),
    })
    return entry_id


def get_history_for_user(user_id: int):
    """Berilgan foydalanuvchining tarixini eng yangisidan boshlab qaytaradi."""
    docs = _history.find({"user_id": user_id}).sort([("created_at", -1), ("_id", -1)])
    return [_history_to_dict(doc) for doc in docs]


def get_all_users():
    """Barcha foydalanuvchilarni item_count (tarix yozuvlari soni) bilan
    birga qaytaradi - admin panel uchun."""
    result = []
    for doc in _users.find().sort("created_at", -1):
        item_count = _history.count_documents({"user_id": doc["_id"]})
        user = _user_to_dict(doc)
        user.pop("hashed_password", None)
        user["item_count"] = item_count
        result.append(user)
    return result
