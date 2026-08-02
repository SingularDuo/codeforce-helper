"""FEATURE 10 - Topic Progress / Mastery (đã sửa: mastery KHÔNG còn suy trực tiếp 1-1 từ số bài AC,
xem core/mastery.py để biết công thức: volume + accuracy + ceiling-so-với-max-rating-của-chính-user)."""
from core import mastery
from . import common

SYSTEM_PROMPT = """Trình bày Topic Progress / mastery dựa trên dữ liệu mastery ĐÃ ĐƯỢC HỆ THỐNG TÍNH SẴN
(công thức: volume_factor + accuracy_factor + ceiling_factor, xem breakdown số kèm theo mỗi topic).
Với topic có mastery thủ công đã lưu (topic_progress), LUÔN ưu tiên dùng đúng số đó và ghi 'đã lưu thủ công'.
Với topic dùng công thức ước lượng, PHẢI giải thích ngắn 1 câu vì sao ra con số đó dựa trên breakdown
(vd 'AC nhiều nhưng ceiling thấp nên mastery không cao'), KHÔNG được nói kiểu 'AC 93 bài = 93% thành thạo'.
Markdown, bullet hoặc bảng, có emoji mức độ.""" + common.ANTI_REPETITION_NOTE


def run(handle):
    profile = common.get_profile(handle)
    manual = profile.get("topic_progress", {})
    max_rating = profile.get("max_rating")

    lines = [f"- {k}: mastery ĐÃ LƯU THỦ CÔNG = {v['mastery']*100:.0f}% (cập nhật {v['updated']})" for k, v in manual.items()]

    for t in profile["tag_penalty"][:10]:
        if t["tag"] in manual:
            continue
        m = mastery.estimate(t, max_rating)
        lines.append(
            f"- {t['tag']} (ước lượng theo công thức): mastery={m['mastery_pct']}% {mastery.stars(m['mastery_pct'])} "
            f"| breakdown: volume={m['volume_factor']}, accuracy={m['accuracy_factor']}, "
            f"ceiling={m['ceiling_factor']} (AC={m['ac']}, WA={m['wa']}, ceiling_rating={m['ceiling']})"
        )
    if not lines:
        return None, "Chưa có đủ dữ liệu topic để hiển thị progress."
    user_prompt = f"{common.context_block(profile)}\n" + "\n".join(lines)
    return common.ask(SYSTEM_PROMPT, user_prompt), None
