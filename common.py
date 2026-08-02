"""
Helper DÙNG CHUNG cho các feature: lấy profile, dựng đoạn context tóm tắt để nhét vào mọi
prompt, hàm gọi LLM thống nhất, và helper crawl nguồn (CF problem id / link ngoài) dùng chung
cho các feature "đọc bài thật" (editorial, hint, pattern, socratic).
"""
from core import user_profile, groq_client, cf_client


def get_profile(handle):
    return user_profile.build_profile(handle)


def context_block(profile):
    weak = ", ".join(f"{t['tag']}(penalty {t['score']})" for t in profile["weak_topics"]) or "chưa đủ dữ liệu"
    strong = ", ".join(f"{t['tag']}(AC {t['ac']})" for t in profile["strong_topics"]) or "chưa đủ dữ liệu"
    roadmap = profile.get("roadmap")
    roadmap_line = (
        f"Target {roadmap['target_rating']} rating trong {roadmap['months']} tháng "
        f"(tạo lúc {roadmap['created_at']})"
        if roadmap else "Chưa có roadmap (người dùng chưa chạy /plan)"
    )
    return (
        f"Handle: {profile['handle']} | Rank: {profile['rank']}\n"
        f"Rating: {profile['rating']} / Max: {profile['max_rating']}\n"
        f"Roadmap hiện tại: {roadmap_line}\n"
        f"Topic mạnh: {strong}\n"
        f"Topic yếu: {weak}\n"
        f"Số bài AC trong 180 ngày gần nhất: {profile['ac_180_days']}\n"
        f"Số ngày ngắt quãng contest rated: {profile['days_since_last_contest']}\n"
    )


def ask(system_prompt, user_prompt, temperature=0.4, model=None):
    return groq_client.call_groq(system_prompt, user_prompt, temperature=temperature, model=model)


# Nhét thêm vào cuối các system prompt có tính "liệt kê nhiều bài/nhiều mục" để chống văn mẫu
# lặp lại y hệt nhau giữa các mục (vấn đề người dùng phản ánh: mọi lý do đều same-pattern).
ANTI_REPETITION_NOTE = (
    "\n\nQUY TẮC VĂN PHONG BẮT BUỘC: Mỗi mục/mỗi bài phải có cách hành văn RIÊNG, không được dùng "
    "lại đúng 1 khuôn câu cho nhiều mục (vd cấm lặp lại kiểu câu 'Bài này giúp rèn luyện kỹ năng về "
    "X, Y, Z' cho tất cả các bài). Luôn bám sát lý do/breakdown CỤ THỂ đã được cung cấp cho từng "
    "mục thay vì liệt kê lại danh sách tags một cách máy móc. Nếu 2 mục có lý do gần giống nhau, "
    "hãy diễn đạt khác nhau và nêu rõ điểm khác biệt thực tế giữa 2 mục đó."
)


ACCURACY_NOTE = (
    "\n\nQUY TẮC CHÍNH XÁC: Nếu không chắc chắn 100% về một con số/độ phức tạp/tên hàm thư viện cụ thể,"
    " hãy nói rõ đây là ước lượng thay vì khẳng định chắc nịch. Không tự bịa số liệu benchmark, độ phức"
    " tạp, hay API không có căn cứ từ dữ liệu được cung cấp."
)


def fetch_source_text(problem_ref=None, link=None):
    """
    Helper dùng chung cho các feature có 2 chế độ 'đọc bài thật': theo problem id Codeforces
    (vd '1543D') hoặc theo link OJ bất kỳ. Trả về (text, source_label).
    """
    if problem_ref:
        contest_id, index = cf_client.parse_cf_problem_id(problem_ref)
        text = cf_client.fetch_problem_statement(contest_id, index)
        return text, f"Codeforces {contest_id}{index} (crawl tự động từ problemset)"
    if link:
        text = cf_client.fetch_url_content(link)
        return text, f"Link: {link} (crawl tự động)"
    raise ValueError("Cần truyền problem_ref (vd '1543D') hoặc link.")


DEEP_REASONING_NOTE = (
    "\n\nLƯU Ý QUAN TRỌNG: Đây là dữ liệu bài toán THẬT được crawl tự động, có thể là bài RẤT KHÓ. "
    "Hãy suy luận từng bước một cách cẩn trọng: (1) đọc kỹ constraints, (2) liệt kê hướng brute-force "
    "trước, (3) tìm quan sát/observation để tối ưu dần, (4) chỉ chốt kết luận cuối cùng sau khi đã tự "
    "kiểm tra lại tính đúng đắn với vài test case nhỏ trong đầu. KHÔNG bịa thêm chi tiết đề bài không "
    "có trong statement được cung cấp — nếu statement bị cắt/thiếu, nêu rõ giả định đang dùng."
)
