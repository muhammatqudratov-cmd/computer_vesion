# database_mongo.py
# MongoDB Atlas ulanishi (pymongo, sinxron drayver). users_db.py shu
# yerdagi `db` handle orqali `users`/`history` kolleksiyalariga kiradi.
# Ulanish holati FastAPI startup vaqtida (api.py'dagi lifespan handler)
# connect_to_mongo() chaqirilib konsolga chop etiladi.

import logging
import os

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

logger = logging.getLogger(__name__)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
MONGO_DEV = os.environ.get("MONGO_DEV")
MONGO_PROD = os.environ.get("MONGO_PROD")

_uri = MONGO_PROD if ENVIRONMENT == "production" else MONGO_DEV

# macOS'dagi Python.org build'lari tizim CA bundle'ini avtomatik topa
# olmasligi mumkin (SSL: CERTIFICATE_VERIFY_FAILED) - shuning uchun
# certifi'ning bundle'i aniq ko'rsatiladi.
client = MongoClient(_uri, tlsCAFile=certifi.where()) if _uri else None
db = client.get_database() if client is not None else None


def connect_to_mongo():
    """FastAPI startup'da chaqiriladi: serverga ping yuborib ulanishni
    tekshiradi va holatni konsolga chop etadi. Ulanish muvaffaqiyatsiz
    bo'lsa xatoni log qiladi, lekin ilovani ishga tushishdan to'xtatmaydi."""
    try:
        if client is None:
            raise RuntimeError("MongoDB URI (.env dagi MONGO_DEV/MONGO_PROD) topilmadi")
        client.admin.command("ping")
        env_label = "production" if ENVIRONMENT == "production" else "development"
        print(f"MongoDB connected successfully to {env_label} db")
    except Exception as exc:
        logger.error("MongoDB connection failed: %s", exc)
        print("Failed to connect to MongoDB")
