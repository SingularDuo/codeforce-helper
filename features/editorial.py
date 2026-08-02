"""FEATURE 7 - Editorial Explainer (3 mức)
Có 3 chế độ, đều dùng chung SYSTEM_PROMPT:
  /editorial <mô_tả_tự_gõ...>        -> run()
  /editorial_cf <problem_id>          -> run_from_cf()   vd: /editorial_cf 4A
  /editorial_link <url>               -> run_from_link()
"""
from . import common

SYSTEM_PROMPT = """Bạn giải thích editorial của một bài toán CP theo 3 mức: Beginner, Intermediate, Advanced.
Mỗi mức PHẢI gồm: Observation, Intuition, Proof, Implementation, Optimization.
Nếu thiếu dữ kiện đề bài/editorial gốc, phải nêu rõ giả định đang dùng thay vì bịa chi tiết đề bài.
Markdown rõ ràng, tách từng mức bằng heading riêng.""" + common.ANTI_REPETITION_NOTE


def run(handle, problem_statement_or_editorial):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nĐề bài / editorial nguồn:\n{problem_statement_or_editorial}"
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.4), None


def run_with_text(handle, text, source_label):
    """Sinh editorial từ text đề bài đã có sẵn (bất kể lấy được bằng crawl tự động hay do người
    dùng tự paste sau khi crawl thất bại) + nhãn nguồn tương ứng. Dùng chung cho run_from_cf()
    và cho main.py khi phải fallback sang nhập tay."""
    profile = common.get_profile(handle)
    prompt = SYSTEM_PROMPT + common.DEEP_REASONING_NOTE
    user_prompt = f"{common.context_block(profile)}\nNguồn: {source_label}\nĐề bài (crawl tự động):\n{text}"
    return common.ask(prompt, user_prompt, temperature=0.25), None


def run_with_text_link(handle, text, source_label):
    """Giống run_with_text(), nhưng dùng cho luồng /editorial_link: đề bài KHÔNG có editorial gốc
    kèm theo nên AI phải tự giải trước. Dùng chung cho run_from_link() và fallback nhập tay."""
    profile = common.get_profile(handle)
    prompt = SYSTEM_PROMPT + common.DEEP_REASONING_NOTE
    user_prompt = (
        f"{common.context_block(profile)}\nNguồn: {source_label}\n"
        f"Đây là bài KHÔNG có editorial gốc kèm theo — bạn phải TỰ GIẢI bài này trước, rồi mới viết "
        f"editorial 3 mức dựa trên lời giải bạn tự tìm ra.\nNội dung trang (crawl tự động):\n{text}"
    )
    return common.ask(prompt, user_prompt, temperature=0.2), None


def run_from_cf(handle, problem_ref):
    """vd problem_ref='4A' hoặc '1543D1' -> tự crawl đề bài Codeforces rồi sinh editorial."""
    try:
        text, source_label = common.fetch_source_text(problem_ref=problem_ref)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run_with_text(handle, text, source_label)


def run_from_link(handle, url):
    """Paste link 1 OJ bất kỳ -> hệ thống tự crawl nội dung trang rồi tự giải + viết editorial.
    Yêu cầu Groq suy luận kỹ hơn (temperature thấp hơn, kèm DEEP_REASONING_NOTE) vì đề bài có thể
    rất khó và không có editorial gốc để tham chiếu."""
    try:
        text, source_label = common.fetch_source_text(link=url)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run_with_text_link(handle, text, source_label)
