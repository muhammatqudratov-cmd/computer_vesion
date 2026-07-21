# database.py
# Lokal vektor baza (Chroma). Diskka saqlanadi, dastur qayta ishga
# tushirilganda ham avval o'rgangan narsalarini eslab qoladi.
#
# Har bir yozuv: {embedding vektori, "name": foydalanuvchi bergan nom,
# "guess_label": YOLO bergan umumiy toifa (masalan "bottle")}

import os
import chromadb

_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "product_memory",
)

_client = None
_collection = None

# Cosine masofa: 0 = aynan bir xil, qancha katta bo'lsa shuncha farqli.
# Bu qiymatdan kichik bo'lsa "tanidi" deb hisoblaymiz.
MATCH_THRESHOLD = 0.25


def get_collection():
    global _client, _collection
    if _collection is None:
        os.makedirs(_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=_DB_PATH)
        _collection = _client.get_or_create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def find_match(embedding, threshold: float = MATCH_THRESHOLD, user_id: str | None = None):
    """Bazadan eng yaqin narsani qidiradi. Agar masofa threshold'dan
    kichik bo'lsa, mos kelgan narsani qaytaradi, aks holda None.

    user_id berilsa, qidiruv faqat o'sha foydalanuvchiga tegishli
    yozuvlar bilan cheklanadi (ko'p foydalanuvchili rejim)."""
    collection = get_collection()
    if collection.count() == 0:
        return None

    query_kwargs = {"query_embeddings": [embedding.tolist()], "n_results": 1}
    if user_id is not None:
        query_kwargs["where"] = {"user_id": user_id}

    results = collection.query(**query_kwargs)

    ids = results.get("ids", [[]])[0]
    if not ids:
        return None

    distance = results["distances"][0][0]
    if distance <= threshold:
        metadata = results["metadatas"][0][0]
        return {
            "name": metadata.get("name", "?"),
            "guess_label": metadata.get("guess_label", ""),
            "distance": distance,
        }
    return None


def save_item(name: str, embedding, guess_label: str = "", user_id: str | None = None):
    """Yangi narsani (nomi + vektori) bazaga qo'shadi.

    user_id berilsa, metadata'ga qo'shiladi - shu orqali har bir
    foydalanuvchining narsalari bir-biridan ajratiladi (ko'p foydalanuvchili
    rejim). Berilmasa (masalan main.py'dan chaqirilganda), eski xatti-harakat
    o'zgarmaydi."""
    collection = get_collection()
    item_id = f"{name}_{collection.count()}_{os.urandom(4).hex()}"
    metadata = {"name": name, "guess_label": guess_label}
    if user_id is not None:
        metadata["user_id"] = user_id
    collection.add(
        ids=[item_id],
        embeddings=[embedding.tolist()],
        metadatas=[metadata],
    )
    return item_id


def list_items(user_id: str | None = None):
    """Bazadagi barcha noyob nomlarni ro'yxat qilib qaytaradi (frontend/tarix uchun).

    user_id berilsa, faqat o'sha foydalanuvchiga tegishli nomlar bilan
    cheklanadi."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    if user_id is not None:
        all_items = collection.get(where={"user_id": user_id})
    else:
        all_items = collection.get()
    names = [meta.get("name", "?") for meta in all_items.get("metadatas", [])]
    return sorted(set(names))


def save_info(name: str, info_text: str, user_id: str | None = None):
    """Berilgan nomga mos barcha yozuvlarning metadata'siga "info" maydonini
    qo'shadi/yangilaydi (Gemini'dan olingan ma'lumotni keshlash uchun).

    user_id berilsa, faqat o'sha foydalanuvchiga tegishli yozuvlar
    yangilanadi."""
    collection = get_collection()
    if collection.count() == 0:
        return

    where = {"name": name}
    if user_id is not None:
        where = {"$and": [{"name": name}, {"user_id": user_id}]}

    matches = collection.get(where=where)
    ids = matches.get("ids", [])
    if not ids:
        return

    updated_metadatas = []
    for meta in matches.get("metadatas", []):
        meta = dict(meta)
        meta["info"] = info_text
        updated_metadatas.append(meta)

    collection.update(ids=ids, metadatas=updated_metadatas)


def get_info(name: str, user_id: str | None = None) -> str | None:
    """Berilgan nom uchun avval saqlangan "info" ma'lumotini qaytaradi,
    agar mavjud bo'lmasa None qaytaradi (Gemini'ni qayta chaqirmaslik uchun).

    user_id berilsa, qidiruv faqat o'sha foydalanuvchiga tegishli
    yozuvlar bilan cheklanadi."""
    collection = get_collection()
    if collection.count() == 0:
        return None

    where = {"name": name}
    if user_id is not None:
        where = {"$and": [{"name": name}, {"user_id": user_id}]}

    matches = collection.get(where=where)
    for meta in matches.get("metadatas", []):
        info = meta.get("info")
        if info:
            return info
    return None
