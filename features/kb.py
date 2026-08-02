"""FEATURE 17 - Knowledge Base"""
from . import common

SYSTEM_PROMPT = """Bạn là Knowledge Base cho thuật toán CP. Trả lời về thuật toán được hỏi với cấu trúc:
Ý tưởng, Proof, Complexity, Implementation (code mẫu ngắn gọn ĐÚNG NGÔN NGỮ được chỉ định), Common Bugs,
Practice Problems (mô tả DẠNG bài phù hợp để luyện, không bịa link/ID cụ thể nếu không chắc chắn),
và mục Tài liệu tham khảo / Minh hoạ trực quan: CHỈ liệt kê lại đúng các link đã được cung cấp sẵn bên
dưới (không tự bịa thêm link khác), ghi rõ link nào là bài viết lý thuyết, link nào có visualization/
animation tương tác để người dùng tự trực quan hoá thuật toán từng bước.""" + common.ACCURACY_NOTE

# Link tĩnh, đã kiểm chứng là nguồn uy tín + có (hoặc gần với) trang minh hoạ trực quan (visualgo...).
# Đây là bảng tra cứu tĩnh, KHÔNG phải LLM tự bịa link -> tránh hallucinate URL.
_RESOURCES = {
    "segment tree": ["https://cp-algorithms.com/data_structures/segment_tree.html", "https://visualgo.net/en/segmentree"],
    "fenwick": ["https://cp-algorithms.com/data_structures/fenwick.html", "https://visualgo.net/en/fenwicktree"],
    "binary indexed tree": ["https://cp-algorithms.com/data_structures/fenwick.html", "https://visualgo.net/en/fenwicktree"],
    "dsu": ["https://cp-algorithms.com/data_structures/disjoint_set_union.html", "https://visualgo.net/en/ufds"],
    "union find": ["https://cp-algorithms.com/data_structures/disjoint_set_union.html", "https://visualgo.net/en/ufds"],
    "lca": ["https://cp-algorithms.com/graph/lca.html", "https://visualgo.net/en/graphds"],
    "binary lifting": ["https://cp-algorithms.com/graph/lca_binary_lifting.html"],
    "dijkstra": ["https://cp-algorithms.com/graph/dijkstra.html", "https://visualgo.net/en/sssp"],
    "bellman-ford": ["https://cp-algorithms.com/graph/bellman_ford.html", "https://visualgo.net/en/sssp"],
    "floyd": ["https://cp-algorithms.com/graph/all-pair-shortest-path-floyd-warshall.html"],
    "max flow": ["https://cp-algorithms.com/graph/edmonds_karp.html", "https://visualgo.net/en/maxflow"],
    "dinic": ["https://cp-algorithms.com/graph/dinic.html", "https://visualgo.net/en/maxflow"],
    "convex hull": ["https://cp-algorithms.com/geometry/convex-hull.html", "https://visualgo.net/en/convexhull"],
    "kmp": ["https://cp-algorithms.com/string/prefix-function.html"],
    "suffix array": ["https://cp-algorithms.com/string/suffix-array.html"],
    "hld": ["https://cp-algorithms.com/graph/hld.html"],
    "heavy-light": ["https://cp-algorithms.com/graph/hld.html"],
    "sorting": ["https://cp-algorithms.com/", "https://visualgo.net/en/sorting"],
    "sort": ["https://cp-algorithms.com/", "https://visualgo.net/en/sorting"],
    "bfs": ["https://cp-algorithms.com/graph/breadth-first-search.html", "https://visualgo.net/en/dfsbfs"],
    "dfs": ["https://cp-algorithms.com/graph/depth-first-search.html", "https://visualgo.net/en/dfsbfs"],
}
_FALLBACK = ["https://cp-algorithms.com/", "https://usaco.guide/", "https://cses.fi/book/book.pdf"]


def _find_resources(algorithm_name):
    t = algorithm_name.lower()
    for key, links in _RESOURCES.items():
        if key in t:
            return links
    return _FALLBACK


def run(handle, algorithm_name, language="c++"):
    profile = common.get_profile(handle)
    links = _find_resources(algorithm_name)
    links_block = "\n".join(f"  - {l}" for l in links)
    user_prompt = (
        f"{common.context_block(profile)}\nThuật toán cần tra cứu: {algorithm_name}\nNgôn ngữ code mẫu: {language}\n\n"
        f"Link tài liệu/minh hoạ đã được tra cứu sẵn (chỉ dùng đúng các link này):\n{links_block}"
    )
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.3), None
