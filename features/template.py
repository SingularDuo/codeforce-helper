"""FEATURE 15 - Template Assistant"""
from . import common

SYSTEM_PROMPT = """Sinh template code cho cấu trúc dữ liệu/thuật toán được yêu cầu.
BẮT BUỘC kèm đủ 4 phần: Complexity, When to use, When NOT to use, Common Bugs.
Code phải chuẩn, biên dịch được, không có bug rõ ràng.

BẮT BUỘC THÊM: ngay phía trên (hoặc bằng comment cạnh) MỖI hàm/method quan trọng trong template, phải
có 1 dòng chú thích ngắn gọn giải thích: hàm đó dùng để LÀM GÌ, và NÊN GỌI KHI NÀO trong quá trình
sử dụng cấu trúc dữ liệu (vd 'update(i, v): cập nhật giá trị tại vị trí i, gọi mỗi khi 1 phần tử mảng
gốc thay đổi — O(log n)'). Không được để hàm nào không có chú thích.""" + common.ACCURACY_NOTE


def run(handle, topic, language="c++"):
    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nSinh template cho: {topic}\nNgôn ngữ: {language}"
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.3), None
