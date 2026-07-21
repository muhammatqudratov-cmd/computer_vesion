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


def find_match(embedding, threshold: float = MATCH_THRESHOLD):
    """Bazadan eng yaqin narsani qidiradi. Agar masofa threshold'dan
    kichik bo'lsa, mos kelgan narsani qaytaradi, aks holda None."""
    collection = get_collection()
    if collection.count() == 0:
        return None

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=1,
    )

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


def save_item(name: str, embedding, guess_label: str = ""):
    """Yangi narsani (nomi + vektori) bazaga qo'shadi."""
    collection = get_collection()
    item_id = f"{name}_{collection.count()}_{os.urandom(4).hex()}"
    collection.add(
        ids=[item_id],
        embeddings=[embedding.tolist()],
        metadatas=[{"name": name, "guess_label": guess_label}],
    )
    return item_id


def list_items():
    """Bazadagi barcha noyob nomlarni ro'yxat qilib qaytaradi (frontend/tarix uchun)."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    all_items = collection.get()
    names = [meta.get("name", "?") for meta in all_items.get("metadatas", [])]
    return sorted(set(names))


def save_info(name: str, info_text: str):
    """Berilgan nomga mos barcha yozuvlarning metadata'siga "info" maydonini
    qo'shadi/yangilaydi (Gemini'dan olingan ma'lumotni keshlash uchun)."""
    collection = get_collection()
    if collection.count() == 0:
        return

    matches = collection.get(where={"name": name})
    ids = matches.get("ids", [])
    if not ids:
        return

    updated_metadatas = []
    for meta in matches.get("metadatas", []):
        meta = dict(meta)
        meta["info"] = info_text
        updated_metadatas.append(meta)

    collection.update(ids=ids, metadatas=updated_metadatas)


def get_info(name: str) -> str | None:
    """Berilgan nom uchun avval saqlangan "info" ma'lumotini qaytaradi,
    agar mavjud bo'lmasa None qaytaradi (Gemini'ni qayta chaqirmaslik uchun)."""
    collection = get_collection()
    if collection.count() == 0:
        return None

    matches = collection.get(where={"name": name})
    for meta in matches.get("metadatas", []):
        info = meta.get("info")
        if info:
            return info
    return None
