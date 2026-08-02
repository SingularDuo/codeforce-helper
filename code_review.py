"""FEATURE 6 - Code Review (style, không phải logic)"""
from . import common

SYSTEM_PROMPT = """Bạn là reviewer style code cho lập trình thi đấu.
Đánh giá: Naming, Readability, Structure, Modularity, Duplication, Template, Maintainability.
KHÔNG đánh giá tính đúng đắn thuật toán. Markdown, bullet, có thang điểm ngắn (vd 1-5) cho mỗi tiêu chí."""


def run(handle, source_code, language="c++"):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nNgôn ngữ: {language}\n\nSource code:\n```\n{source_code}\n```"
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.3), None
