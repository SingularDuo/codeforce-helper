"""FEATURE 4 - Contest Review (đã fix lỗ hổng dữ liệu: trước đây không có solve-time/penalty,
giờ tái tạo lại từ user.status bằng cf_client.get_contest_submission_summary)."""
from core import cf_client
from . import common

SYSTEM_PROMPT = """Bạn là Competitive Programming Coach phân tích lịch sử contest.
Phân tích: Rating Trend, Contest Consistency, Average Solve Time theo từng problem index, Wrong
Submission/Penalty, khả năng đọc đề, khả năng implementation, khả năng quản lý thời gian — dựa trên
dữ liệu rank/delta rating VÀ dữ liệu solve-time/attempts thực tế được cung cấp bên dưới (đã crawl từ
lịch sử nộp bài, không phải suy đoán). Nếu một mục nào đó vẫn thiếu dữ liệu thô, phải nói rõ cụ thể
thiếu gì, không dùng câu chung chung "không có dữ liệu chi tiết".
Nếu phát hiện pattern lặp lại rõ ràng (vd luôn mất quá nhiều thời gian ở bài C, hoặc rating giảm liên
tục N contest liền, hoặc attempts trung bình bài D luôn > 3 lần), PHẢI nêu rõ pattern đó kèm bằng
chứng số liệu cụ thể. Markdown, bullet/table, ngắn gọn.""" + common.ANTI_REPETITION_NOTE


def run(handle, last_n=10):
    contests = cf_client.get_user_rating(handle)
    recent = contests[-last_n:] if contests else []
    if not recent:
        return None, "Không có dữ liệu contest rated nào cho handle này."

    contest_ids = [c["contestId"] for c in recent]
    try:
        summary = cf_client.get_contest_submission_summary(handle, contest_ids)
    except cf_client.CFClientError:
        summary = {}

    lines = []
    for c in recent:
        cid = c["contestId"]
        delta = c["newRating"] - c["oldRating"]
        lines.append(
            f"- {c['contestName']} (id {cid}) | rank {c['rank']} | {c['oldRating']} -> {c['newRating']} "
            f"(delta {delta:+d})"
        )
        per_problem = summary.get(cid)
        if per_problem:
            detail = []
            for idx in sorted(per_problem.keys()):
                pd = per_problem[idx]
                if pd["solved"]:
                    mins = pd["solve_time_seconds"] // 60
                    detail.append(f"{idx}: AC lúc {mins} phút, {pd['attempts']} lần nộp (penalty {pd['attempts']-1})")
                else:
                    detail.append(f"{idx}: KHÔNG AC, {pd['attempts']} lần nộp")
            lines.append("    Chi tiết từng bài: " + " | ".join(detail))
        else:
            lines.append("    (Không tìm thấy submission nào của contest này trong user.status — có thể do "
                          "lịch sử submission bị Codeforces giới hạn số lượng trả về, hoặc contest quá cũ.)")

    profile = common.get_profile(handle)
    user_prompt = f"{common.context_block(profile)}\nLịch sử {len(recent)} contest gần nhất (kèm chi tiết solve-time/attempts đã crawl):\n" + "\n".join(lines)
    return common.ask(SYSTEM_PROMPT, user_prompt), None
