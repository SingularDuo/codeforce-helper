"""
FEATURE 3 - Problem Recommendation (/recommend, /recommend dp, /recommend math 2200)
Dùng chung Recommendation Engine, chia theo nhóm Warm-up / Core / Challenge / Review / Must Solve.
"""
from core import cf_client, storage
from core import recommendation_engine as engine
from . import common

SYSTEM_PROMPT = """Bạn là Competitive Programming Coach. Trình bày danh sách bài được đề xuất theo các nhóm:
Warm-up, Core, Challenge, Review, Must Solve — CHỈ sử dụng đúng những bài được cung cấp sẵn bên dưới
(không bịa thêm bài hay đổi rating/tags/link). Với mỗi bài, BẮT BUỘC hiển thị đủ (không được bỏ qua dù
trình bày dạng bảng hay bullet ngắn gọn): Mã bài Codeforces (contestId+index, vd "1543D") + Link
Codeforces đầy đủ (dùng ĐÚNG dữ liệu cho sẵn), Tên, Rating, Tags, Lý do recommend (diễn giải TỪ
breakdown/lý do cụ thể đã cho, không liệt kê số thô, không lặp khuôn câu giữa các bài), Takeaway (kiến
thức chính CỤ THỂ của riêng bài đó, không viết chung chung áp dụng cho mọi bài). Markdown, ngắn gọn, dùng
bullet hoặc bảng.

LƯU Ý: Tags Codeforces chỉ là gợi ý chủ đề, không đảm bảo đúng kỹ thuật giải — tránh khẳng định chắc
chắn một thuật toán duy nhất chỉ dựa vào tag khi chưa có editorial xác nhận.""" + common.ANTI_REPETITION_NOTE

GROUP_MODES = {"Warm-up": "speed", "Core": "core", "Challenge": "stretch", "Review": "review"}


def _must_solve(problems, profile, exclude, tag_filter, rating_filter):
    """Nhóm 'Must Solve': bài rất kinh điển (solvedCount cao) trong đúng dải rating phù hợp core,
    ưu tiên độ phổ biến gần như tuyệt đối — đại diện cho 'ai luyện CP cũng nên làm qua bài này'."""
    candidates = []
    for raw in problems:
        pid = f"{raw.get('contestId')}{raw.get('index')}"
        if pid in exclude or pid in profile["solved_ids"] or not raw.get("name"):
            continue
        if tag_filter and tag_filter.lower() not in [t.lower() for t in raw.get("tags", [])]:
            continue
        if rating_filter and raw.get("rating") != rating_filter:
            continue
        r = raw.get("rating")
        if not r or abs(r - profile["rating"]) > 300:
            continue
        candidates.append(raw)
    candidates.sort(key=lambda p: -(p.get("solvedCount") or 0))
    return candidates[:2]


def run(handle, tag=None, rating=None):
    profile = common.get_profile(handle)
    problems = cf_client.get_problemset()
    exclude = set(profile["solved_ids"]) | set(profile["recent_recommended_ids"])

    lines = []
    all_problems = []
    for label, mode in GROUP_MODES.items():
        picks = engine.recommend(
            problems, profile, mode=mode, count=2, tag_filter=tag, rating_filter=rating, exclude_ids=exclude
        )
        if not picks:
            continue
        lines.append(f"### {label}")
        for pick in picks:
            exclude.add(pick["problem"]["id"])
            p = pick["problem"]
            reasons = engine.explain(pick, mode, profile)
            all_problems.append(p)
            problem_code = f"{p.get('contestId')}{p.get('index')}"
            problem_link = f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}"
            lines.append(
                f"- {p['name']} | mã bài: {problem_code} | link: {problem_link} | "
                f"rating {p.get('rating')} | tags: {', '.join(p.get('tags', []))} | "
                f"solvedCount: {p.get('solvedCount', 0)} | "
                f"lý do: {'; '.join(reasons)} | breakdown: {pick['breakdown']}"
            )

    must_solve = _must_solve(problems, profile, exclude, tag, rating)
    if must_solve:
        lines.append("### Must Solve")
        for p in must_solve:
            pid = f"{p.get('contestId')}{p.get('index')}"
            exclude.add(pid)
            p = dict(p)
            p["id"] = pid
            all_problems.append(p)
            problem_link = f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}"
            lines.append(
                f"- {p['name']} | mã bài: {pid} | link: {problem_link} | "
                f"rating {p.get('rating')} | tags: {', '.join(p.get('tags', []))} | "
                f"solvedCount: {p.get('solvedCount', 0)} | "
                f"lý do: Bài kinh điển với khoảng {p.get('solvedCount', 0):,} lượt AC toàn cầu, gần rating hiện tại"
            )

    if not all_problems:
        return None, "Không tìm thấy bài phù hợp với bộ lọc đã cho (thử bỏ bớt filter tag/rating)."

    user_prompt = (
        f"{common.context_block(profile)}\nBộ lọc: tag={tag or 'không'}, rating={rating or 'không'}\n\n"
        f"Danh sách theo nhóm do Recommendation Engine chọn sẵn (BẮT BUỘC hiển thị mã bài + link cho "
        f"mỗi bài trong output):\n" + "\n".join(lines)
    )
    result = common.ask(SYSTEM_PROMPT, user_prompt)
    storage.log_recommendation(handle, all_problems, mode="recommend")
    return result, None
