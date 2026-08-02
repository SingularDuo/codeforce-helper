"""FEATURE 8 - Hint Mode (không spoil ngay)
  /hint <mức> <đề_bài_tự_gõ...>       -> run()
  /hint_cf <mức> <problem_id>          -> run_from_cf()
  /hint_link <mức> <url>               -> run_from_link()
"""
from . import common

SYSTEM_PROMPT = """Bạn là Hint Coach. KHÔNG được spoil lời giải ngay lập tức.
Cấu trúc hint tăng dần: Hint 1 (gợi ý quan sát nhỏ) -> Hint 2 (thu hẹp hướng đi) ->
Hint 3 (gần công thức/thuật toán) -> Almost Solution (gần đủ nhưng còn thiếu 1 mảnh) ->
Final Hint (lời giải đầy đủ). CHỈ hiển thị đúng mức mà người dùng yêu cầu ở lượt này,
không tự nhảy thẳng xuống mức cuối trừ khi người dùng yêu cầu rõ 'final hint' hoặc 'giải luôn'."""


def run(handle, problem_statement, requested_level="hint1"):
    profile = common.get_profile(handle)
    user_prompt = (
        f"{common.context_block(profile)}\nMức hint được yêu cầu: {requested_level}\n\n"
        f"Đề bài:\n{problem_statement}"
    )
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.5), None


def run_with_text(handle, requested_level, text, source_label):
    """Sinh hint từ text đề bài đã có sẵn (crawl tự động thành công hoặc người dùng tự paste sau
    khi crawl thất bại). Dùng chung cho run_from_cf() và cho main.py khi fallback nhập tay."""
    profile = common.get_profile(handle)
    prompt = SYSTEM_PROMPT + common.DEEP_REASONING_NOTE
    user_prompt = (
        f"{common.context_block(profile)}\nMức hint được yêu cầu: {requested_level}\nNguồn: {source_label}\n\n"
        f"Đề bài (crawl tự động):\n{text}"
    )
    return common.ask(prompt, user_prompt, temperature=0.4), None


def run_with_text_link(handle, requested_level, text, source_label):
    """Giống run_with_text(), dùng cho luồng /hint_link (nội dung trang có thể không có lời giải
    mẫu). Dùng chung cho run_from_link() và fallback nhập tay."""
    profile = common.get_profile(handle)
    prompt = SYSTEM_PROMPT + common.DEEP_REASONING_NOTE
    user_prompt = (
        f"{common.context_block(profile)}\nMức hint được yêu cầu: {requested_level}\nNguồn: {source_label}\n\n"
        f"Nội dung trang (crawl tự động, có thể không có lời giải mẫu — tự giải trước khi cho hint):\n{text}"
    )
    return common.ask(prompt, user_prompt, temperature=0.35), None


def run_from_cf(handle, requested_level, problem_ref):
    try:
        text, source_label = common.fetch_source_text(problem_ref=problem_ref)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run_with_text(handle, requested_level, text, source_label)


def run_from_link(handle, requested_level, url):
    try:
        text, source_label = common.fetch_source_text(link=url)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run_with_text_link(handle, requested_level, text, source_label)
