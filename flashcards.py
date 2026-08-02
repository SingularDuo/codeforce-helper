"""FEATURE 12 - Flashcards (spaced repetition), giờ INTERACTIVE:
main.py sẽ: generate() -> với mỗi câu, hỏi người dùng qua input() -> grade_answer() chấm -> lưu lại.
"""
import json
import re

from core import storage
from core.groq_client import call_groq
from . import common

GEN_SYSTEM = """Sinh CHÍNH XÁC N flashcard cho spaced repetition, output CHỈ LÀ 1 JSON list hợp lệ,
mỗi phần tử có đúng 2 key "question" và "answer" (string), KHÔNG thêm bất kỳ text/markdown/giải
thích nào khác ngoài JSON. Nội dung súc tích, đúng trọng tâm kiến thức CP, không lan man."""

GRADE_SYSTEM = """Bạn chấm câu trả lời của người học so với đáp án chuẩn cho 1 flashcard CP.
Trả lời CỰC NGẮN GỌN gồm 3 phần: (1) Kết quả: Đúng / Sai / Gần đúng, (2) Vì sao (1 câu),
(3) Bổ sung nếu thiếu (nếu có). Không khắt khe với cách diễn đạt khác đáp án miễn bản chất đúng.
KHÔNG lặp lại nguyên văn câu hỏi."""


def generate(handle, topic, n=5):
    profile = common.get_profile(handle)
    prompt = f"{common.context_block(profile)}\nTopic: {topic}\nSố lượng thẻ cần sinh: {n}"
    raw = call_groq(GEN_SYSTEM, prompt, temperature=0.5)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.M).strip()
    try:
        cards = json.loads(cleaned)
        cards = [c for c in cards if isinstance(c, dict) and "question" in c and "answer" in c]
    except Exception:
        cards = []
    if not cards:
        return None, "Không sinh được flashcard hợp lệ (lỗi định dạng từ LLM), hãy thử lại lệnh."
    return cards, None


def grade_answer(question, correct_answer, user_answer):
    prompt = f"Câu hỏi: {question}\nĐáp án chuẩn: {correct_answer}\nCâu trả lời của người học: {user_answer}"
    return call_groq(GRADE_SYSTEM, prompt, temperature=0.2)


def save_card_result(handle, topic, question, answer, user_answer=None, verdict=None):
    storage.add_flashcard(
        handle, question=question, answer=answer, topic=topic,
        user_answer=user_answer, verdict=verdict,
    )


def history(handle, limit=30):
    """Lịch sử các lượt trả lời flashcard gần nhất (câu hỏi/đáp án chuẩn/câu trả lời của người
    dùng/kết quả chấm), dùng cho lệnh /flashcards_history."""
    profile = common.get_profile(handle)
    return profile.get("flashcards", [])[-limit:]
