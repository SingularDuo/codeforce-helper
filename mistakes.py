"""FEATURE 13 - Mistake Tracker"""
import difflib

from core import storage
from . import common

SYSTEM_PROMPT = """Tổng hợp Top recurring mistakes từ mistake log được cung cấp bên dưới.
CHỈ dùng dữ liệu có trong log, KHÔNG bịa lỗi không có trong log. Nếu log rỗng, nói rõ chưa có dữ liệu
và hướng dẫn ngắn gọn cách bắt đầu ghi log (dùng lệnh /mistake-log). Với mỗi mục có field 'count' > 1,
PHẢI nêu rõ số lần lặp lại (count), vì đó là tín hiệu quan trọng nhất về lỗi hệ thống chưa sửa được.
Markdown, bullet, xếp theo tần suất (count giảm dần)."""

SIMILARITY_THRESHOLD = 0.8


def _find_duplicate(handle, mistake_type, note):
    data = storage.load(handle)
    for m in data.get("mistakes", []):
        if m.get("type") != mistake_type:
            continue
        ratio = difflib.SequenceMatcher(None, m.get("note", "").lower(), note.lower()).ratio()
        if ratio >= SIMILARITY_THRESHOLD:
            return data, m
    return data, None


def log(handle, mistake_type, note, source=""):
    data, dup = _find_duplicate(handle, mistake_type, note)
    if dup is not None:
        dup["count"] = dup.get("count", 1) + 1
        dup["date"] = storage.now_iso()  # cập nhật lần gặp gần nhất
        storage.save(handle, data)
        return f"🔁 Lỗi này gần giống 1 lỗi đã ghi trước đó — tăng đếm lặp lại lên {dup['count']} lần: [{mistake_type}] {dup['note']}"
    storage.add_mistake(handle, mistake_type, note, source)
    return f"✅ Đã ghi nhận lỗi mới: [{mistake_type}] {note}"


def clear(handle):
    """Xoá toàn bộ mistake log của handle. Chỉ thao tác dữ liệu (storage), không gọi AI."""
    count = storage.clear_mistakes(handle)
    if count == 0:
        return "ℹ️ Mistake log của bạn đang trống, không có gì để xoá."
    return f"🗑️ Đã xoá toàn bộ mistake log ({count} mục)."


def run(handle):
    profile = common.get_profile(handle)
    mistakes = profile.get("mistakes", [])
    if not mistakes:
        lines = ["(chưa có dữ liệu lỗi nào được ghi nhận)"]
    else:
        mistakes = sorted(mistakes, key=lambda m: -m.get("count", 1))
        lines = [
            f"- [{m['type']}] {m['note']} (count={m.get('count',1)}, nguồn: {m.get('source','')}, lần gần nhất: {m['date']})"
            for m in mistakes[-50:]
        ]
    user_prompt = f"{common.context_block(profile)}\nMistake log:\n" + "\n".join(lines)
    return common.ask(SYSTEM_PROMPT, user_prompt), None