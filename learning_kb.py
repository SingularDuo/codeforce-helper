"""
Knowledge Base tĩnh cho /learning_graph: định nghĩa SẴN chuỗi prerequisite ĐÚNG cho các nhóm
kiến thức phổ biến trong CP, để tránh việc để LLM tự "đoán" thứ tự và bịa ra chuỗi sai (vd học
Euler Tour trước rồi mới LCA/Binary Lifting, nhưng lại xếp Euler Tour SAU LCA — sai bản chất).

learning_graph.py sẽ tra cứu ở đây trước; nếu không khớp topic nào, mới fallback sang LLM kèm
theo các ví dụ chuẩn này để LLM bắt chước đúng quy ước, tránh bịa quan hệ prerequisite sai.
"""

# Mỗi entry: keywords để match (lowercase) -> chain (list, đúng thứ tự học từ đầu -> topic đích)
_CHAINS = [
    (["segment tree", "fenwick", "bit", "persistent segment", "lazy propagation"], [
        "Prefix Sum", "Difference Array", "Fenwick Tree (BIT)", "Segment Tree",
        "Lazy Propagation Segment Tree", "Persistent Segment Tree",
    ]),
    (["lca", "lowest common ancestor", "binary lifting", "euler tour", "sparse table"], [
        "DFS trên cây", "Euler Tour / DFS Order", "Sparse Table (RMQ)",
        "Binary Lifting", "LCA (Lowest Common Ancestor)",
    ]),
    (["heavy-light", "hld", "heavy light decomposition"], [
        "DFS trên cây", "Subtree Size", "Euler Tour / DFS Order",
        "Heavy-Light Decomposition", "Segment Tree trên HLD",
    ]),
    (["dsu on tree", "small to large"], [
        "DFS trên cây", "Subtree Size", "Small-to-Large Merging", "DSU on Tree",
    ]),
    (["dsu", "union find", "disjoint set"], [
        "Union-Find (DSU) cơ bản", "Union by Rank/Size", "Path Compression",
        "DSU with Rollback (nếu cần offline)",
    ]),
    (["max flow", "min cost flow", "dinic", "ford-fulkerson", "network flow"], [
        "Đồ thị cơ bản (BFS/DFS)", "Bipartite Matching (Kuhn's)", "Max Flow (Ford-Fulkerson/BFS augmenting)",
        "Dinic's Algorithm", "Min Cost Max Flow",
    ]),
    (["centroid decomposition", "centroid"], [
        "DFS trên cây", "Subtree Size", "Centroid của cây", "Centroid Decomposition",
    ]),
    (["convex hull trick", "cht", "li chao"], [
        "Đường thẳng & Slope Trick cơ bản", "Convex Hull (hình học)", "Convex Hull Trick (Monotonic)",
        "Li Chao Tree",
    ]),
    (["mo's algorithm", "mo algorithm", "offline query"], [
        "Prefix Sum", "Xử lý truy vấn Offline cơ bản", "Sqrt Decomposition", "Mo's Algorithm",
    ]),
    (["suffix array", "suffix automaton", "z-function", "kmp"], [
        "String matching cơ bản (Brute force)", "KMP / Prefix Function", "Z-Function",
        "Suffix Array", "Suffix Automaton",
    ]),
    (["dp bitmask", "bitmask dp", "sos dp"], [
        "DP cơ bản (1D/2D)", "Bitmask cơ bản", "DP Bitmask (Traveling Salesman dạng nhỏ)",
        "SOS DP (Sum over Subsets)",
    ]),
    (["sqrt decomposition", "mo"], [
        "Prefix Sum", "Block/Bucket cơ bản", "Sqrt Decomposition",
    ]),
    (["binary search"], [
        "Binary Search trên mảng đã sắp xếp", "Binary Search trên đáp án (Binary Search the Answer)",
        "Parametric Search nâng cao",
    ]),
]


def find_chain(topic):
    t = topic.lower()
    for keywords, chain in _CHAINS:
        if any(k in t for k in keywords):
            return chain
    return None


def format_chain(chain):
    return " → ".join(chain)


def all_topics_hint():
    """Danh sách các cụm từ khoá đã có sẵn chain chuẩn, dùng để gợi ý người dùng."""
    seen = []
    for keywords, chain in _CHAINS:
        seen.append(chain[-1])
    return seen
