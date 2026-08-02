"""FEATURE 2 - Weakness Analysis"""
from core import mastery
from . import common

SYSTEM_PROMPT = """Bạn là Competitive Programming Coach. Phân tích điểm mạnh/yếu KHÔNG chỉ đếm tag suông:
với mỗi topic quan trọng hãy nêu mức độ (thang sao ★, LẤY ĐÚNG số sao đã được tính sẵn ở dữ liệu, KHÔNG tự
suy ra lại), Rating Ceiling (= rating cao nhất user từng AC ở topic đó — nếu ceiling=0 nghĩa là user chưa AC
bài nào CÓ RATING ở tag này, phải nói rõ điều đó thay vì bỏ trống hay ghi 'không có dữ liệu'), và Bottleneck
cụ thể (suy từ tỉ lệ WA/AC). CHỈ dùng đúng số liệu được cung cấp, KHÔNG bịa thêm số liệu không có.
Markdown, bullet, không viết văn dài.""" + common.ANTI_REPETITION_NOTE


def run(handle):
    profile = common.get_profile(handle)
    max_rating = profile.get("max_rating")
    lines = []
    for t in profile["tag_penalty"][:12]:
        m = mastery.estimate(t, max_rating)
        ceiling_note = "chưa AC bài nào có rating ở tag này" if t["ceiling"] == 0 else f"rating {t['ceiling']}"
        lines.append(
            f"- {t['tag']}: AC={t['ac']}, WA={t['wa']}, penalty_score={t['score']}, "
            f"rating_ceiling={ceiling_note}, mastery_ước_lượng={m['mastery_pct']}% ({mastery.stars(m['mastery_pct'])})"
        )
    if not lines:
        return None, "Chưa đủ dữ liệu bài đã giải để phân tích điểm mạnh/yếu."
    user_prompt = f"{common.context_block(profile)}\nDữ liệu tag chi tiết:\n" + "\n".join(lines)
    return common.ask(SYSTEM_PROMPT, user_prompt), None
