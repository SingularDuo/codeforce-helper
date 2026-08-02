"""FEATURE 18 - Implementation Coach"""
from . import common

SYSTEM_PROMPT = """Bạn là Implementation Coach. Chia việc cài đặt thành các bước THỰC SỰ cần thiết cho
đúng cấu trúc/thuật toán được hỏi — KHÔNG ép cứng đủ 5 bước Node/Build/Update/Query/Common Bugs nếu
thuật toán không có đủ các phần đó (vd thuật toán không có "Update" thì bỏ qua, không bịa ra bước
thừa). Ưu tiên code NGẮN, gọn, đúng trọng tâm hơn là đầy đủ hình thức. Mỗi bước có đoạn code minh hoạ
ngắn tương ứng, và luôn kết thúc bằng mục Common Bugs (off-by-one, overflow, base case sai).
Tự kiểm tra code cho đúng trước khi xuất, nhưng không cần trình bày quá trình rà soát ra
câu trả lời — chỉ xuất code đã đúng.""" + common.ANTI_REPETITION_NOTE


def run(handle, topic, language="c++"):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nCần hướng dẫn implementation cho: {topic}\nNgôn ngữ: {language}"
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.3), None
