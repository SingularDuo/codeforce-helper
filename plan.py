"""
FEATURE ĐÃ CÓ - /plan (Generate Learning Plan / Roadmap)
KHÔNG được sửa prompt/behavior/output ở đây. Chỉ wrap lại logic gốc.
Điểm mở rộng DUY NHẤT (không đổi output hiển thị cho user): sau khi roadmap được
sinh ra, lưu lại vào history store để các feature khác (recommendation engine,...)
dùng chung dữ liệu roadmap này.
"""
from core import legacy_core, storage
from core.groq_client import call_groq


def run(handle, target_rating, months):
    analytics, err = legacy_core.fetch_cf_rich_analytics(handle, target_rating)
    if err:
        return None, err

    rating_gap = max(0, target_rating - analytics["rating"])
    d = analytics["rating_distribution"]
    rating_dist_str = (
        f"{d['800-1500']} bài (800–1500) | {d['1600-1900']} bài (1600–1900) | "
        f"{d['2000-2200']} bài (2000–2200) | {d['2300-2500']} bài (2300–2500) | {d['2600+']} bài (2600+)"
    )
    top_penalty = ", ".join([x["tag"] for x in analytics["tag_penalty_data"][:3]])

    prompt = f"""
Hãy lập Lộ trình Chinh phục Mục tiêu cho tôi:
- Handle: {analytics['handle']} | Rank: {analytics['rank']}
- Rating hiện tại: {analytics['rating']} | Rating Max: {analytics['maxRating']}
- MỤC TIÊU (TARGET RATING): {target_rating}
- THỜI GIAN: {months} tháng
- RATING GAP CẦN TĂNG: +{rating_gap} rating
- Ngày báo cáo: {analytics['current_date']}
- Phân bố rating bài đã giải: {rating_dist_str}
- Recency: {analytics['days_since_last_contest']} ngày ngắt quãng rated contest.
- Top Tags bị Penalty: {top_penalty}
- Dữ liệu Penalty chi tiết: {analytics['tag_penalty_data']}
- Gợi ý bài tập khởi động hôm nay: {analytics['recommended_problems']}
"""
    result_text = call_groq(legacy_core.SYSTEM_PROMPT, prompt, temperature=0.4)

    # Mở rộng nội bộ (không ảnh hưởng output cho user): lưu roadmap để các feature khác dùng chung
    storage.save_roadmap(handle, target_rating, months, result_text)

    return result_text, None
