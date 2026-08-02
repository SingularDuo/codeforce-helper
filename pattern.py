"""FEATURE 14 - Pattern Recognition (+ recommend bài tương tự qua Recommendation Engine)
  /pattern <mô_tả_tự_gõ...>       -> run()
  /pattern_cf <problem_id>         -> run_from_cf()
  /pattern_link <url>              -> run_from_link()
"""
from core import cf_client
from core import recommendation_engine as engine
from . import common

SYSTEM_PROMPT = """Nhận diện Pattern kỹ thuật từ mô tả bài toán / code được cung cấp. Các nhóm pattern
cần cân nhắc (không giới hạn nếu bạn nhận ra pattern khác rõ ràng hơn): Offline Query, Bitmask DP,
Mo's Algorithm, DSU on Tree, Centroid Decomposition, Max Flow/Min Cost Flow, Convex Hull Trick/Li Chao,
SOS DP, Two Pointers, Sliding Window, Binary Search on Answer (Parametric Search), Greedy + Exchange
Argument, Divide and Conquer Optimization (DP), Persistent Data Structure, Sqrt Decomposition,
Small-to-Large Merging, Euler Tour + Binary Lifting (LCA), Heavy-Light Decomposition, Digit DP,
Interval DP, Matrix Exponentiation, Suffix Structures (SA/SAM), Xor Basis/Linear Basis, Game Theory
(Sprague-Grundy), Randomization/Hashing tricks.
CHỈ kết luận một pattern khi có dấu hiệu rõ ràng trong input; nếu không chắc, liệt kê các pattern khả dĩ
kèm lý do nghi ngờ thay vì khẳng định chắc chắn một pattern duy nhất.
Sau đó, dựa trên danh sách bài luyện tập tương tự do Recommendation Engine chọn sẵn bên dưới, đề xuất
lại các bài đó (không tự bịa thêm bài khác)."""


def _with_recommendations(handle, description_or_code, profile=None):
    profile = profile or common.get_profile(handle)
    problems = cf_client.get_problemset()
    exclude = set(profile["solved_ids"]) | set(profile["recent_recommended_ids"])
    picks = engine.recommend(problems, profile, mode="core", count=3, exclude_ids=exclude)
    picks_lines = [
        f"- {p['problem']['name']} | rating {p['problem'].get('rating')} | tags {', '.join(p['problem'].get('tags', []))}"
        for p in picks
    ]
    return (
        f"Mô tả bài / code cần nhận diện pattern:\n{description_or_code}\n\n"
        f"Bài luyện tập tương tự do Recommendation Engine chọn sẵn:\n" + "\n".join(picks_lines or ["(không có)"])
    )


def run(handle, description_or_code):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\n" + _with_recommendations(handle, description_or_code, profile)
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.3), None


def run_with_text(handle, text, source_label):
    """Nhận diện pattern từ text đề bài/mô tả đã có sẵn (crawl tự động thành công hoặc người dùng
    tự paste sau khi crawl thất bại). Dùng chung cho run_from_cf(), run_from_link(), và cho
    main.py khi phải fallback sang nhập tay."""
    profile = common.get_profile(handle)
    prompt = SYSTEM_PROMPT + common.DEEP_REASONING_NOTE
    user_prompt = f"{common.context_block(profile)}\nNguồn: {source_label}\n" + _with_recommendations(handle, text, profile)
    return common.ask(prompt, user_prompt, temperature=0.25), None


def run_from_cf(handle, problem_ref):
    try:
        text, source_label = common.fetch_source_text(problem_ref=problem_ref)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run_with_text(handle, text, source_label)


def run_from_link(handle, url):
    try:
        text, source_label = common.fetch_source_text(link=url)
    except (ValueError, Exception) as e:
        return None, str(e)
    return run_with_text(handle, text, source_label)
