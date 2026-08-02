"""FEATURE 5 - Submission Review (chỉ performance/implementation, KHÔNG đụng vào logic thuật toán)
Chế độ THỦ CÔNG: người dùng paste/trỏ tới file code trực tiếp.
Xem thêm submission_review_cf.py cho chế độ tự động lấy theo link submission Codeforces."""
from . import common

SYSTEM_PROMPT = """Bạn là reviewer performance/implementation cho code thi đấu.
CHỈ được phân tích các khía cạnh: Time Complexity, Memory Complexity, Overflow, Undefined Behaviour,
Iterator invalidation, Precision, Recursion Depth, Macro nguy hiểm, STL usage, khả năng TLE do implementation.

TUYỆT ĐỐI KHÔNG được: phân tích đúng/sai của thuật toán, chỉ ra thuật toán đúng là gì, spoil lời giải,
hay debug logic bài toán. Nếu người dùng hỏi lấn sang phần đó, từ chối phần đó và nói rõ đây là ngoài
phạm vi feature Submission Review (gợi ý dùng feature Code Review hoặc Hint Mode thay thế).
Markdown, bullet, ngắn gọn."""


def run(handle, source_code, language="c++"):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nNgôn ngữ: {language}\n\nSource code:\n```\n{source_code}\n```"
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.2), None
