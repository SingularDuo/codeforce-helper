"""FEATURE 11 - Learning Graph (đã sửa lỗi thứ tự sai, vd Euler Tour bị xếp sau LCA/Binary Lifting).
Ưu tiên tra core/learning_kb.py (chuỗi prerequisite tĩnh, đã kiểm chứng đúng thứ tự chuẩn CP).
Nếu topic không khớp KB nào, fallback sang LLM nhưng kèm theo các ví dụ ĐÚNG để LLM bắt chước
đúng quy ước prerequisite, tránh tự bịa quan hệ sai."""
from core import learning_kb
from . import common

SYSTEM_PROMPT = """Vẽ Learning Graph dạng text (dùng mũi tên →) cho chuỗi kiến thức tiền đề dẫn tới
topic được hỏi, kèm chú thích topic nào người dùng đã vững / đang học / chưa học (dựa dữ liệu topic
mạnh/yếu được cung cấp). BẮT BUỘC tuân thủ ĐÚNG quan hệ nhân-quả: A phải đứng TRƯỚC B nếu và chỉ nếu
hiểu B cần hiểu A trước (vd DFS/Euler Tour PHẢI đứng trước Binary Lifting và LCA, không được đảo
ngược). Không bịa quan hệ prerequisite sai. Dưới đây là các chuỗi mẫu ĐÃ ĐƯỢC XÁC NHẬN ĐÚNG, hãy dùng
làm chuẩn tham chiếu về cách sắp thứ tự (không nhất thiết phải dùng đúng các topic này nếu người
dùng hỏi chủ đề khác):
  - Prefix Sum → Difference Array → Fenwick Tree (BIT) → Segment Tree → Lazy Propagation → Persistent Segment Tree
  - DFS trên cây → Euler Tour / DFS Order → Sparse Table (RMQ) → Binary Lifting → LCA
""" + common.ANTI_REPETITION_NOTE


def run(handle, topic):
    profile = common.get_profile(handle)
    known_chain = learning_kb.find_chain(topic)

    if known_chain:
        chain_text = learning_kb.format_chain(known_chain)
        user_prompt = (
            f"{common.context_block(profile)}\nTopic gốc cần vẽ learning graph: {topic}\n\n"
            f"CHUỖI PREREQUISITE CHUẨN (đã tra cứu sẵn, BẮT BUỘC dùng đúng thứ tự này, không đảo):\n"
            f"{chain_text}\n\nHãy trình bày lại dạng sơ đồ mũi tên kèm chú thích đã vững/đang học/chưa "
            f"học cho từng bước, dựa trên topic mạnh/yếu của người dùng."
        )
    else:
        user_prompt = (
            f"{common.context_block(profile)}\nTopic gốc cần vẽ learning graph: {topic}\n"
            f"(Không có sẵn chuỗi chuẩn cho topic này trong hệ thống — hãy tự suy luận quan hệ "
            f"prerequisite THẬT SỰ đúng bản chất, tham khảo cách sắp xếp ở 2 ví dụ mẫu trong system prompt.)"
        )
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.2), None
