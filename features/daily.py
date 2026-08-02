"""
FEATURE 1 - Daily Training

Input giờ là:
  - Dải độ khó mong muốn hôm nay: <L> <R> (rating)
  - Tổng thời gian có thể dành cho CP hôm nay: <tổng_phút>

Trước đây tham số duy nhất là 1 khung giờ trong ngày (vd "1800-2100") nhưng KHÔNG hề được dùng để
lọc bài hay chia thời gian — chỉ nhét vào prompt cho có. Giờ cả 2 tham số đều dùng thật:
  - L-R lọc thẳng candidate problems trong Recommendation Engine (rating_range).
  - Tổng phút được chia tỉ lệ cho 3 bài Speed/Core/Stretch (hoặc Review nếu đang gặp khó khăn
    liên tục), kẹp trong khoảng hợp lý mỗi loại thay vì disable khung giờ cố định 10-25/30-70/60-120
    bất kể người dùng hôm nay có bao nhiêu thời gian.
"""
from core import cf_client, storage
from core import recommendation_engine as engine
from . import common

SYSTEM_PROMPT = """Bạn là Competitive Programming Coach. Nhiệm vụ: trình bày MỘT buổi luyện tập hôm nay
gồm đúng 3 bài: Speed Task, Core Task, và bài thứ 3 là Stretch Task (khó hơn) HOẶC Review Task (ôn lại
prerequisite/topic yếu) — dùng ĐÚNG loại được ghi trong danh sách bên dưới (nếu nhãn là REVIEW nghĩa là
hệ thống phát hiện người dùng đang gặp khó khăn liên tục gần đây nên chủ động hạ độ khó để củng cố nền
tảng thay vì đẩy khó hơn — hãy giải thích rõ lý do này cho người dùng), dựa CHÍNH XÁC trên danh sách bài đã được
Recommendation Engine chọn sẵn bên dưới (KHÔNG được tự bịa bài khác, KHÔNG đổi rating/tags/link/thời
gian đã cho — thời gian mỗi bài đã được HỆ THỐNG chia sẵn từ tổng số phút người dùng có hôm nay,
KHÔNG dùng con số 10-25/30-70/60-120 mặc định cũ nữa).

Với mỗi bài, trình bày rõ (BẮT BUỘC đủ các mục sau, không được bỏ qua bất kỳ mục nào kể cả khi trình
bày ngắn gọn dạng bullet):
- Mã bài Codeforces (contestId+index, vd "1543D") VÀ Link Codeforces đầy đủ — dùng ĐÚNG mã/link đã
  cho trong danh sách bên dưới, không tự bịa, không rút gọn, không bỏ sót
- Tên bài, Rating, Tags, Độ khó (dùng emoji mức độ phù hợp)
- Thời gian được chia (đúng số phút đã cho, không tự đổi)
- Lý do recommend (dựa trên breakdown điểm được cung cấp, diễn giải lại bằng lời, không liệt kê số thô)
- Kiến thức sẽ học được
- Prerequisite cần ôn trước (nếu tag bài đòi hỏi, vd Fenwick cần ôn Coordinate Compression)

Nếu tổng thời gian 3 bài được chia nhỏ hơn tổng phút người dùng có, hãy nói rõ phần dư nên dùng để
đọc lại lý thuyết/nghỉ giữa giờ thay vì lờ đi.

Output Markdown, có header/bullet, KHÔNG viết đoạn văn dài, KHÔNG dùng câu sáo rỗng kiểu
"hãy cố gắng" / "cứ luyện thêm" / "practice makes perfect".

LƯU Ý: Tags của Codeforces chỉ là gợi ý CHỦ ĐỀ, KHÔNG phải lời giải chắc chắn — một bài gắn tag
"segment tree" đôi khi giải gọn hơn bằng kỹ thuật khác. Khi nêu "Kiến thức sẽ học được", diễn đạt
dạng khả năng ("nhiều khả năng cần...", "hãy thử hướng ... trước khi kết luận") thay vì khẳng định
chắc nịch một thuật toán duy nhất nếu bạn không có editorial/lời giải xác nhận.""" + common.ANTI_REPETITION_NOTE

# Tỉ lệ chia tổng thời gian cho từng loại bài, và khoảng kẹp hợp lý (phút) để tránh Speed chiếm hết
# thời gian hoặc Stretch chỉ còn vài phút vô nghĩa khi tổng thời gian quá ít/quá nhiều.
MODE_SHARE = {"speed": 0.20, "core": 0.50, "stretch": 0.30, "review": 0.30}
MODE_BOUNDS = {"speed": (10, 30), "core": (20, 90), "stretch": (20, 130), "review": (20, 90)}

STRUGGLE_WINDOW_DAYS = 7
STRUGGLE_THRESHOLD = 3  # >= N mistake log trong window này -> đang gặp khó khăn liên tục


def _is_struggling(profile):
    """Nếu người dùng vừa ghi nhận nhiều lỗi liên tiếp gần đây (/mistake_log), coi là đang gặp
    khó khăn -> KHÔNG đẩy bài khó hơn (Stretch), thay vào đó ưu tiên củng cố lại (Review)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    recent = 0
    for m in profile.get("mistakes", [])[-30:]:
        try:
            d = datetime.fromisoformat(m["date"])
        except Exception:
            continue
        if (now - d).days <= STRUGGLE_WINDOW_DAYS:
            recent += 1
    return recent >= STRUGGLE_THRESHOLD


def _allocate_time(total_minutes, modes):
    """Chia tổng số phút người dùng có hôm nay cho từng mode theo MODE_SHARE, kẹp lại trong
    MODE_BOUNDS để không ra kết quả vô lý (vd tổng 20 phút mà Stretch vẫn đòi 60 phút)."""
    budget = {}
    for mode in modes:
        share = MODE_SHARE.get(mode, 1 / len(modes))
        lo, hi = MODE_BOUNDS.get(mode, (10, max(10, total_minutes)))
        budget[mode] = max(lo, min(hi, round(total_minutes * share)))
    return budget


def run(handle, low_rating, high_rating, total_minutes):
    profile = common.get_profile(handle)
    problems = cf_client.get_problemset()
    exclude = set(profile["solved_ids"]) | set(profile["recent_recommended_ids"])

    struggling = _is_struggling(profile)
    modes = ("speed", "core", "review") if struggling else ("speed", "core", "stretch")
    time_budget = _allocate_time(total_minutes, modes)

    picks_lines = []
    chosen = {}
    for mode in modes:
        picks = engine.recommend(
            problems, profile, mode=mode, count=1, exclude_ids=exclude,
            rating_range=(low_rating, high_rating),
        )
        if not picks:
            continue
        pick = picks[0]
        exclude.add(pick["problem"]["id"])
        chosen[mode] = pick
        reasons = engine.explain(pick, mode, profile)
        p = pick["problem"]
        minutes = time_budget[mode]
        problem_code = f"{p.get('contestId')}{p.get('index')}"
        problem_link = f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}"
        picks_lines.append(
            f"[{mode.upper()}] {p['name']} | mã bài: {problem_code} | link: {problem_link} | "
            f"rating {p.get('rating')} | tags: {', '.join(p.get('tags', []))} | "
            f"thời gian được chia: {minutes} phút | lý do: {'; '.join(reasons)} | "
            f"breakdown điểm: {pick['breakdown']}"
        )

    if not chosen:
        return None, (
            f"Không tìm thấy bài phù hợp trong dải rating {low_rating}-{high_rating} (có thể do dải quá "
            f"hẹp, hoặc đã recommend/AC hết bài trong dải này gần đây). Thử nới rộng L-R."
        )

    total_allocated = sum(time_budget[m] for m in chosen)
    user_prompt = (
        f"{common.context_block(profile)}\n"
        f"Dải độ khó người dùng chọn hôm nay: {low_rating}-{high_rating} rating\n"
        f"Tổng thời gian có thể luyện tập hôm nay: {total_minutes} phút "
        f"(đã chia: {total_allocated} phút cho {len(chosen)} bài, phần dư nếu có nên dùng để đọc lại/nghỉ)\n\n"
        f"Danh sách bài đã được Recommendation Engine chọn sẵn (bắt buộc dùng đúng các bài này, "
        f"BẮT BUỘC hiển thị mã bài + link cho mỗi bài):\n"
        + "\n".join(picks_lines)
    )

    result = common.ask(SYSTEM_PROMPT, user_prompt)

    storage.log_recommendation(handle, [c["problem"] for c in chosen.values()], mode="daily")
    storage.log_training_session(handle, {
        "type": "daily",
        "rating_range": [low_rating, high_rating],
        "total_minutes": total_minutes,
        "problems": [c["problem"]["id"] for c in chosen.values()],
    })
    return result, None
