"""FEATURE 9 - Complexity Analyzer
Trước đây bắt người dùng tự viết 1 file constraints.txt đúng format. Giờ: người dùng gõ TỰ DO
từng dòng constraint (vd '-1e9 < a_i < 1e9', '1e9 <= a_i', 'n <= 2*10^5'), hệ thống tự chuẩn hoá
bằng core.constraint_parser bất kể thứ tự '<' hay '<=' được viết kiểu nào.
"""
from core import constraint_parser
from . import common

SYSTEM_PROMPT = """Bạn ước lượng độ phức tạp runtime/memory dựa trên constraints và code được cung cấp.
Constraints đã được HỆ THỐNG chuẩn hoá tự động (parse số/biến/khoảng), đi kèm bản gốc người dùng gõ —
nếu có dòng ghi 'chưa chuẩn hoá được', hãy tự đọc hiểu phần văn bản gốc đó, KHÔNG bỏ qua.
Output gồm: Runtime ước lượng (Big-O + số phép tính xấp xỉ theo constraints), Memory ước lượng,
Khả năng AC (định tính: cao/trung bình/thấp, kèm lý do), Khả năng TLE, Khả năng MLE — tất cả PHẢI
suy ra từ constraints/code thực tế được cung cấp, không bịa số liệu benchmark không có căn cứ.
KHÔNG đánh giá tính đúng của thuật toán."""


def normalize_bound_lines(raw_lines):
    """raw_lines: list[str] người dùng gõ tự do. Trả về text đã chuẩn hoá để nhét vào prompt."""
    blocks = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        parsed = constraint_parser.parse_bound_line(line)
        blocks.append(f"* Dòng gốc: '{line}'\n{constraint_parser.to_readable(line, parsed)}")
    return "\n".join(blocks) if blocks else "(người dùng không nhập constraint nào)"


def run(handle, raw_bound_lines, source_code):
    """raw_bound_lines: list các dòng constraint tự do (đã thu thập ở tầng CLI, có thể qua input()
    tương tác hoặc đọc từ 1 file constraints.txt cũ nếu người dùng vẫn muốn dùng file)."""
    profile = common.get_profile(handle)
    constraints_block = normalize_bound_lines(raw_bound_lines)
    user_prompt = (
        f"{common.context_block(profile)}\nConstraints (đã chuẩn hoá tự động):\n{constraints_block}"
        f"\n\nCode:\n```\n{source_code}\n```"
    )
    return common.ask(SYSTEM_PROMPT, user_prompt, temperature=0.2), None
