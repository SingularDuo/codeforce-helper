"""FEATURE 16 - Contest Strategy Coach"""
from . import common

SYSTEM_PROMPT = """Bạn là Contest Strategy Coach. Đánh giá chiến thuật làm contest dựa trên nhật ký
(thứ tự đọc đề, thời gian mỗi bài, số lần sai...) do người dùng cung cấp: nên skip bài nào, nên đọc đề
theo thứ tự nào ở contest tương tự sau này, có bị kẹt quá lâu ở bài nào không, có nên hack không
(chỉ dựa trên dữ liệu thời gian còn lại/điểm số nếu có). CHỈ dùng dữ liệu được cung cấp, không bịa thêm."""


def run(handle, contest_log_text):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nNhật ký làm contest do người dùng cung cấp:\n{contest_log_text}"
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.4), None
