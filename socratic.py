"""FEATURE 19 - Socratic Coach
  /socratic <đề_bài_tự_gõ...>       -> run()
  /socratic_cf <problem_id>          -> run_from_cf()
  /socratic_link <url>               -> run_from_link()
"""
from . import common

SYSTEM_PROMPT = """Bạn là Socratic Coach. TUYỆT ĐỐI KHÔNG giải bài trực tiếp hay tiết lộ hướng giải.
Thay vào đó, đặt các câu hỏi dẫn dắt tuần tự kiểu: Constraint là gì? Bruteforce là gì?
Có Observation nào có thể tận dụng? Có tính chất Monotonicity không? Có thể xử lý Offline không?
DP State là gì (nếu có)? ... CHỈ hỏi 1-3 câu mỗi lượt dựa trên những gì người dùng đã trả lời
(nếu có lịch sử hội thoại), KHÔNG tự trả lời thay người dùng."""


def run(handle, problem_statement, conversation_so_far=""):
    profile = common.get_profile(handle)
    user_prompt = (
        f"{common.context_block(profile)}\nĐề bài:\n{problem_statement}\n\n"
        f"Hội thoại Socratic đã diễn ra (nếu có):\n{conversation_so_far or '(chưa có, đây là câu hỏi đầu tiên)'}"
    )
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.5), None


def run_from_cf(handle, problem_ref, conversation_so_far=""):
    try:
        text, source_label = common.fetch_source_text(problem_ref=problem_ref)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run(handle, f"[{source_label}]\n{text}", conversation_so_far)


def run_from_link(handle, url, conversation_so_far=""):
    try:
        text, source_label = common.fetch_source_text(link=url)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run(handle, f"[{source_label}]\n{text}", conversation_so_far)
