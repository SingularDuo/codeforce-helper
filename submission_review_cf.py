"""
FEATURE 5b (mới) - Submission Review TỰ ĐỘNG từ link Codeforces
(/submission_review_cf <link_hoặc_contestId/submissionId> [language])

Tách riêng khỏi submission_review.py (paste code thủ công) theo đúng yêu cầu: người dùng chỉ cần
đưa link submission, hệ thống tự crawl source code rồi review y hệt tiêu chí của Submission Review.

GIỚI HẠN THẬT: Codeforces không cho xem source code của submission người khác qua trang public nếu
không đăng nhập đúng chủ tài khoản đó. Vì hệ thống không lưu cookie đăng nhập, phần lớn submission
của người khác (hoặc kể cả của chính bạn nếu không login) sẽ KHÔNG lấy được source — hàm sẽ báo lỗi
rõ ràng và gợi ý dùng /submission_review (paste code) thay thế, thay vì trả kết quả sai/rỗng.
"""
import re
from core import cf_client
from . import submission_review


def _parse_submission_ref(ref):
    ref = ref.strip()
    m = re.search(r"codeforces\.com/contest/(\d+)/submission/(\d+)", ref)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"^(\d+)[/\s]+(\d+)$", ref)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(
        "Không nhận diện được submission. Dùng link đầy đủ "
        "'https://codeforces.com/contest/<id>/submission/<subId>' hoặc '<contestId> <submissionId>'."
    )


def run(handle, submission_ref, language="c++"):
    try:
        contest_id, sub_id = _parse_submission_ref(submission_ref)
        source = cf_client.fetch_submission_source(contest_id, sub_id)
    except (ValueError, cf_client.CFClientError) as e:
        return None, str(e)
    return submission_review.run(handle, source, language)
