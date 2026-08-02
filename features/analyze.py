"""
FEATURE ĐÃ CÓ - /analyze
KHÔNG được sửa prompt/behavior/output ở đây. Chỉ wrap lại logic gốc.
"""
from core import legacy_core
from core.groq_client import call_groq


def run(handle):
    analytics, err = legacy_core.fetch_cf_rich_analytics(handle)
    if err:
        return None, err

    target_rating = analytics["rating"] + 200
    rating_gap = 200
    d = analytics["rating_distribution"]
    rating_dist_str = (
        f"{d['800-1500']} bài (800–1500) | {d['1600-1900']} bài (1600–1900) | "
        f"{d['2000-2200']} bài (2000–2200) | {d['2300-2500']} bài (2300–2500) | {d['2600+']} bài (2600+)"
    )

    prompt = f"""
Lập Báo cáo hiện trạng:
- Handle: {analytics['handle']} | Rank: {analytics['rank']} | Rating: {analytics['rating']} / Max: {analytics['maxRating']}
- Target mặc định: {target_rating} | Thời gian: 3 tháng | Gap: +{rating_gap}
- Phân bố bài giải: {rating_dist_str}
- Penalty Tags: {analytics['tag_penalty_data']}
- Gợi ý bài tập: {analytics['recommended_problems']}
- Ngày: {analytics['current_date']}
"""
    result_text = call_groq(legacy_core.SYSTEM_PROMPT, prompt, temperature=0.4)
    return result_text, None
