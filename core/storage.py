"""
History Store dùng CHUNG cho toàn bộ hệ thống: lưu roadmap, log bài đã recommend,
training session, mistake log, flashcards, topic progress theo từng handle.
Lưu dạng JSON file local (không cần DB ngoài).
"""
import json
import os
import threading
from datetime import datetime, timezone

from .config import DATA_DIR

_lock = threading.Lock()


def _path(handle):
    os.makedirs(DATA_DIR, exist_ok=True)
    safe = "".join(c for c in handle if c.isalnum() or c in "-_").lower()
    return os.path.join(DATA_DIR, f"{safe}.json")


def _default():
    return {
        "handle": None,
        "roadmap": None,          # {"target_rating", "months", "created_at", "raw"}
        "recommended_log": [],    # [{"problem_id","name","rating","tags","mode","date"}]
        "training_sessions": [],  # log các buổi /daily
        "mistakes": [],           # [{"type","note","source","date"}]
        "flashcards": [],         # [{"question","answer","topic","date","box"}]
        "topic_progress": {},     # {"Segment Tree": {"mastery":0.8,"updated":...}}
    }


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load(handle):
    p = _path(handle)
    base = _default()
    if not os.path.exists(p):
        base["handle"] = handle
        return base
    with _lock:
        with open(p, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    base.update(data)
    base["handle"] = handle
    return base


def save(handle, data):
    p = _path(handle)
    with _lock:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def log_recommendation(handle, problems, mode):
    data = load(handle)
    for p in problems:
        data["recommended_log"].append({
            "problem_id": p.get("id"),
            "name": p.get("name"),
            "rating": p.get("rating"),
            "tags": p.get("tags", []),
            "mode": mode,
            "date": now_iso(),
        })
    data["recommended_log"] = data["recommended_log"][-500:]
    save(handle, data)


def save_roadmap(handle, target_rating, months, raw_text):
    data = load(handle)
    data["roadmap"] = {
        "target_rating": target_rating,
        "months": months,
        "created_at": now_iso(),
        "raw": raw_text,
    }
    save(handle, data)


def log_training_session(handle, session):
    data = load(handle)
    session = dict(session)
    session["date"] = now_iso()
    data["training_sessions"].append(session)
    data["training_sessions"] = data["training_sessions"][-200:]
    save(handle, data)


def add_mistake(handle, mistake_type, note, source=""):
    data = load(handle)
    data["mistakes"].append({
        "type": mistake_type, "note": note, "source": source, "date": now_iso()
    })
    save(handle, data)


def clear_mistakes(handle):
    """Xoá toàn bộ mistake log đã lưu của 1 handle (dùng cho /mistake_clear). Không đụng tới các
    phần dữ liệu khác (roadmap, recommended_log, flashcards, topic_progress...)."""
    data = load(handle)
    count = len(data.get("mistakes", []))
    data["mistakes"] = []
    save(handle, data)
    return count


def add_flashcard(handle, question, answer, topic, user_answer=None, verdict=None):
    data = load(handle)
    data["flashcards"].append({
        "question": question, "answer": answer, "topic": topic, "date": now_iso(), "box": 1,
        "user_answer": user_answer, "verdict": verdict,
    })
    save(handle, data)


def update_topic_progress(handle, topic, mastery):
    data = load(handle)
    data["topic_progress"][topic] = {"mastery": mastery, "updated": now_iso()}
    save(handle, data)


def recent_recommended_ids(handle, n=40):
    data = load(handle)
    return [x["problem_id"] for x in data["recommended_log"][-n:] if x.get("problem_id")]


def recent_recommended_tags(handle, last_n_entries=15):
    data = load(handle)
    tags = []
    for x in data["recommended_log"][-last_n_entries:]:
        tags.extend(x.get("tags") or [])
    return tags