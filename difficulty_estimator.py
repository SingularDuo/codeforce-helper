"""
Difficulty Estimation module DÙNG CHUNG cho Recommendation Engine.
fitness() trả điểm 0..1 thể hiện độ phù hợp giữa rating bài và rating người dùng,
theo từng "mode" luyện tập (speed / core / stretch / review).
"""

# (lo, hi, center) tính theo (problem_rating - user_rating)
_WINDOWS = {
    "speed": (-500, -150, -350),
    "core": (-150, 250, 50),
    "stretch": (200, 600, 400),
    "review": (-400, 0, -200),
}


def fitness(problem_rating, user_rating, mode):
    if problem_rating is None or user_rating is None:
        return 0.0
    diff = problem_rating - user_rating
    lo, hi, center = _WINDOWS.get(mode, (-200, 200, 0))
    span = max(abs(lo - center), abs(hi - center)) or 1

    if lo <= diff <= hi:
        return max(0.0, 1 - abs(diff - center) / span)

    overflow = min(abs(diff - center) - span, span)
    return max(0.0, 0.5 - overflow / span)
