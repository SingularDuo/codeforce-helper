"""
RECOMMENDATION ENGINE DÙNG CHUNG.
TẤT CẢ feature liên quan tới gợi ý bài (/daily, /recommend, roadmap-driven picks, review,
challenge, pattern-based suggestion...) đều phải gọi engine này -> không tự chấm điểm
kiểu riêng ở từng feature.

Recommendation Score =
    difficulty fitness + topic priority + roadmap priority + review priority
    + novelty + weakness priority + time suitability + popularity (độ kinh điển)
"""
import math

from . import difficulty_estimator as de

WEIGHTS = {
    "difficulty": 3.0,
    "topic_priority": 2.0,
    "roadmap_priority": 2.0,
    "review_priority": 1.5,
    "novelty": 1.0,
    "weakness_priority": 2.5,
    "time_suitability": 1.0,
    "popularity": 1.2,
}


MIN_SOLVED_COUNT = 60  # lọc bớt bài quá ít người AC (dễ là bài lỗi/đề mơ hồ/tag sai lệch)


def effective_rating(profile):
    """
    Rating dùng để tính difficulty fitness. Trước đây luôn dùng thẳng profile['rating'], khiến
    /daily và /recommend bị 'ghì' về đúng rating hiện tại dù người dùng đã đặt roadmap target cao
    hơn nhiều (vd rating 1300 nhưng target 2000-2500) -> hầu như chỉ ra bài quanh 1300.
    Giờ: nếu có roadmap, kéo dần rating hiệu dụng về phía target (nghiêng 35% về target), để độ
    khó bài được chọn tiệm cận lộ trình thay vì đứng yên ở rating hiện tại.
    """
    base = profile["rating"]
    roadmap = profile.get("roadmap")
    if roadmap and roadmap.get("target_rating"):
        target = roadmap["target_rating"]
        return base + 0.35 * (target - base)
    return base


def _topic_priority(problem_tags, profile):
    weak_tags = {t["tag"] for t in profile["weak_topics"]}
    if not weak_tags:
        return 0.3
    overlap = weak_tags.intersection(problem_tags)
    return min(1.0, 0.4 * len(overlap))


def _roadmap_priority(problem, profile):
    roadmap = profile.get("roadmap")
    if not roadmap or not problem.get("rating"):
        return 0.3
    target = roadmap.get("target_rating")
    if not target:
        return 0.3
    gap = abs(problem["rating"] - target)
    return max(0.0, 1 - gap / 800)


def _review_priority(problem_tags, profile):
    recent_tags = set(profile.get("recent_recommended_tags", []))
    weak_tags = {t["tag"] for t in profile["weak_topics"]}
    stale_weak = weak_tags - recent_tags
    overlap = stale_weak.intersection(problem_tags)
    return min(1.0, 0.5 * len(overlap))


def _novelty(problem, profile):
    recent_ids = profile.get("recent_recommended_ids", set())
    return 0.2 if problem.get("id") in recent_ids else 1.0


def _weakness_priority(problem_tags, profile):
    weak = {t["tag"]: t["score"] for t in profile["weak_topics"]}
    if not weak:
        return 0.2
    hits = [weak[t] for t in problem_tags if t in weak]
    if not hits:
        return 0.1
    return min(1.0, (sum(hits) / len(hits)) / 2)


def _time_suitability(mode):
    # Placeholder có chủ đích: mức độ phù hợp khung giờ đã được lọc trước ở tầng gọi
    # (vd /daily 1800-2100 sẽ lọc problems theo thời lượng ước tính trước khi vào engine).
    return 1.0


def _popularity(problem):
    """
    Độ 'kinh điển' của bài, ước lượng qua solvedCount trả về từ Codeforces API
    (problemset.problems -> problemStatistics). Bài càng nhiều người AC, càng có xu hướng
    là bài chất lượng, được cộng đồng đánh giá cao / là bài kinh điển đáng luyện.
    Dùng log-scale vì solvedCount trải rất rộng (vài chục -> vài chục nghìn).
    """
    solved = problem.get("solvedCount") or 0
    if solved <= 0:
        return 0.3  # không có dữ liệu -> trung tính, không phạt nặng
    return min(1.0, math.log10(solved + 1) / 4.3)  # solvedCount ~ 20000 => gần 1.0


def score_problem(problem, profile, mode="core"):
    if problem.get("id") in profile.get("solved_ids", set()):
        return None  # KHÔNG BAO GIỜ recommend bài đã AC

    tags = set(problem.get("tags", []))
    breakdown = {
        "difficulty": de.fitness(problem.get("rating"), effective_rating(profile), mode),
        "topic_priority": _topic_priority(tags, profile),
        "roadmap_priority": _roadmap_priority(problem, profile),
        "review_priority": _review_priority(tags, profile),
        "novelty": _novelty(problem, profile),
        "weakness_priority": _weakness_priority(tags, profile),
        "time_suitability": _time_suitability(mode),
        "popularity": _popularity(problem),
    }
    total = sum(WEIGHTS[k] * v for k, v in breakdown.items())
    return total, breakdown


def recommend(problems, profile, mode="core", count=1, tag_filter=None, rating_filter=None,
               rating_range=None, exclude_ids=None):
    exclude_ids = exclude_ids or set()
    scored = []
    for raw in problems:
        pid = f"{raw.get('contestId')}{raw.get('index')}"
        if pid in exclude_ids or not raw.get("name"):
            continue
        if tag_filter and tag_filter.lower() not in [t.lower() for t in raw.get("tags", [])]:
            continue
        if rating_filter and (not raw.get("rating") or abs(raw["rating"] - rating_filter) > 100):
            continue
        if rating_range:
            lo, hi = rating_range
            r = raw.get("rating")
            if not r or r < lo or r > hi:
                continue

        p = dict(raw)
        p["id"] = pid
        result = score_problem(p, profile, mode)
        if result is None:
            continue
        total, breakdown = result
        scored.append((total, breakdown, p))

    # Ưu tiên bài có đủ độ phổ biến (solvedCount) trước, vì bài quá ít người AC thường có tag
    # không phản ánh đúng kỹ thuật cần dùng để giải (tag chỉ là gợi ý chủ đề, không phải lời giải).
    # Nếu lọc xong không còn đủ ứng viên (chủ đề hiếm gặp), fallback dùng lại toàn bộ danh sách.
    popular = [s for s in scored if (s[2].get("solvedCount") or 0) >= MIN_SOLVED_COUNT]
    if len(popular) >= count:
        scored = popular

    scored.sort(key=lambda x: -x[0])

    picks, seen_names = [], set()
    for total, breakdown, p in scored:
        if p["name"] in seen_names:
            continue
        seen_names.add(p["name"])
        picks.append({
            "problem": p,
            "score": round(total, 2),
            "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
        })
        if len(picks) >= count:
            break
    return picks


def explain(pick, mode, profile):
    """
    Sinh danh sách lý do CỤ THỂ cho 1 bài, dựa trên breakdown thực tế (không phải văn mẫu).
    Mỗi feature gọi lại hàm này -> đảm bảo lý do khác nhau bài này với bài khác, vì phụ thuộc
    breakdown số thực chứ không phải liệt kê tags.
    """
    p = pick["problem"]
    b = pick["breakdown"]
    reasons = []
    if b["weakness_priority"] > 0.4:
        top_weak = [t["tag"] for t in profile["weak_topics"]][:3]
        overlap = [t for t in top_weak if t in p.get("tags", [])]
        if overlap:
            reasons.append(f"Đánh trúng điểm yếu: {', '.join(overlap)}")
    if b["roadmap_priority"] > 0.6 and profile.get("roadmap"):
        reasons.append(f"Rating {p.get('rating')} nằm sát mục tiêu roadmap {profile['roadmap']['target_rating']}")
    if b["review_priority"] > 0.4:
        reasons.append("Topic yếu đã lâu chưa luyện lại trong lịch sử gần đây, cần ôn lại")
    if b["novelty"] < 0.5:
        reasons.append("Đưa lại để củng cố (từng được gợi ý trước đó)")
    if b["popularity"] > 0.75:
        solved = p.get("solvedCount", 0)
        reasons.append(f"Bài kinh điển, đã có khoảng {solved:,} người AC")
    if not reasons:
        reasons.append(f"Độ khó khớp mức '{mode}' so với rating hiện tại ({p.get('rating')})")
    return reasons
