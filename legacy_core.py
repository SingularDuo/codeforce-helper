"""
!!! KHÔNG ĐƯỢC SỬA FILE NÀY !!!

Đây là phần logic GỐC của 2 chức năng đã hoạt động tốt: /analyze và /plan.
Được port gần như nguyên văn từ bản gốc (chỉ đổi cách lấy API key từ hardcode
sang os.environ để vá lỗi bảo mật, KHÔNG đổi behavior/prompt/output).
"""
import requests
from datetime import datetime, timezone

SYSTEM_PROMPT = """
Bạn là một HLV Lập trình Thi đấu (Competitive Programming Coach) cấp quốc tế.
Khi nhận dữ liệu phân tích và YÊU CẦU MỤC TIÊU từ người dùng, hãy xuất ra một BÁO CÁO & KẾ HOẠCH LỘ TRÌNH (ROADMAP) chuẩn định dạng Markdown bên dưới.

Văn phong: Sắc bén, thực tế, định hướng mục tiêu rõ ràng và tạo động lực cao.

---
### 📊 1. BÁO CÁO HIỆN TRẠNG & DỮ LIỆU THỰC TẾ (FACTS)

| Chỉ số | Giá trị | Ghi chú |
|---|---|---|
| **Handle** | {handle} | {rank} |
| **Rating hiện tại / Max** | {rating} / {maxRating} | **Mục tiêu đặt ra: {target_rating}** |
| **Khoảng cách (Gap)** | +{rating_gap} rating | **Thời gian thực hiện: {months} tháng** |
| **Tổng số bài đã giải (AC)** | {total_ac} bài | Trong {total_submissions} lần nộp |
| **Recency (Rated Contests)** | {days_since_last_contest} ngày | {recency_note} |
| **Phân bố bài giải lịch sử** | {rating_dist_str} | Trung vị bài đã giải: ~{median_rating} |
| **180 ngày gần nhất** | {ac_180_days} bài AC | {recent_activity_note} |

---
### 🗺️ 2. LỘ TRÌNH CHINH PHỤC MỤC TIÊU {target_rating} RATING ({months} THÁNG)

Dựa vào khoảng cách **+{rating_gap} rating** trong **{months} tháng**, hãy chia kế hoạch theo các Giai đoạn (Phases) hoặc theo từng Tháng rõ ràng:

- **Giai đoạn 1: Khôi phục nhịp độ & Lấp lỗ hổng (Tháng 1)**
  - *Mục tiêu Rating:* Đạt mốc intermediate.
  - *Trọng tâm:* Xử lý triệt để các mảng bị Penalty cao ({top_penalty_tags}).
  - *Chỉ tiêu bài giải:* Tối thiểu bao nhiêu bài/tuần, dải rating ưu tiên.

- **Giai đoạn 2: Bứt phá dải rating tầm trung (Tháng 2)**
  - *Trọng tâm:* Nâng cao kỹ năng tư duy thuật toán nâng cao, tối ưu thời gian làm bài (Timebox).

- **Giai đoạn 3: Chiến thuật Contest & Cán mốc {target_rating} (Tháng {months})**
  - *Trọng tâm:* Luyện Virtual Contest, kiểm soát tâm lý và chiến thuật nộp bài không bị Penalty.

---
### ⚠️ 3. PHÂN TÍCH LỖ HỔNG CẦN KHẮC PHỤC NGAY (TAG WEAKNESS SIGNALS)

(Dựa vào dữ liệu Penalty trong Prompt, hãy chỉ ra Top 3 - 4 dạng bài đang kéo Rating xuống và cần giải quyết trong Giai đoạn 1):
1. **[Tên Tag] (Score [Penalty_Score]):**
   - **Thống kê:** [Số bài AC] AC / [Số lần sai] sai.
   - **Khắc phục:** Định hướng cách tư duy và thói quen test trước khi submit.

---
### 🎯 4. KẾ HOẠCH LUYỆN TẬP HÔM NAY ({current_date} – KHỞI ĐỘNG)

**Mục tiêu hôm nay:** Tập trung xử lý các bài tập chuẩn bị cho lộ trình {target_rating}.
BẮT BUỘC CHỈ DÙNG CÁC BÀI TẬP ĐƯỢC CUNG CẤP TRONG DANH SÁCH 'GỢI Ý BÀI TẬP':

#### ⚡ 1. Speed Task: [Tên bài] [Link]
- **Rating:** [Rating] | **Timebox:** 35 phút
- **Tags:** [Tags]

#### 🎯 2. Core Task: [Tên bài] [Link]
- **Rating:** [Rating] | **Timebox:** 65 phút
- **Tags:** [Tags]

#### 🚀 3. Stretch Task: [Tên bài] [Link]
- **Rating:** [Rating] | **Timebox:** 95 phút
- **Tags:** [Tags]

---
### 🎯 Process KPI & Kỷ luật Luyện tập

- **Quy tắc vàng:** Không nộp bài ngẫu nhiên (no blind resubmission).
- **Nhật ký:** Sau mỗi bài sai quá 2 lần, bắt buộc ghi chú nguyên nhân vào notebook/journal trước khi xem Editorials.
"""


def fetch_cf_rich_analytics(handle, target_rating=None):
    try:
        user_res = requests.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=10).json()
        if user_res.get("status") != "OK":
            return None, f"Không tìm thấy handle '{handle}' trên Codeforces."
        user_info = user_res["result"][0]

        rating_res = requests.get(f"https://codeforces.com/api/user.rating?handle={handle}", timeout=10).json()
        contests = rating_res.get("result", []) if rating_res.get("status") == "OK" else []

        now_ts = datetime.now(timezone.utc).timestamp()
        days_since_last_contest = 0
        if contests:
            last_contest_time = contests[-1]["ratingUpdateTimeSeconds"]
            days_since_last_contest = int((now_ts - last_contest_time) / 86400)

        status_res = requests.get(f"https://codeforces.com/api/user.status?handle={handle}", timeout=15).json()
        submissions = status_res.get("result", []) if status_res.get("status") == "OK" else []

        solved_problems = set()
        tag_ac, tag_wa = {}, {}
        rating_buckets = {"800-1500": 0, "1600-1900": 0, "2000-2200": 0, "2300-2500": 0, "2600+": 0}
        ratings_list = []
        ac_180_days = 0
        limit_180_ts = now_ts - (180 * 86400)

        for s in submissions:
            prob = s.get("problem", {})
            contest_id, index = prob.get("contestId"), prob.get("index")
            if not contest_id or not index:
                continue

            prob_id = f"{contest_id}{index}"
            creation_time = s.get("creationTimeSeconds", 0)
            verdict = s.get("verdict")
            tags, r = prob.get("tags", []), prob.get("rating")

            if verdict == "OK":
                if prob_id not in solved_problems:
                    solved_problems.add(prob_id)
                    if creation_time >= limit_180_ts:
                        ac_180_days += 1

                    if r:
                        ratings_list.append(r)
                        if 800 <= r <= 1500:
                            rating_buckets["800-1500"] += 1
                        elif 1600 <= r <= 1900:
                            rating_buckets["1600-1900"] += 1
                        elif 2000 <= r <= 2200:
                            rating_buckets["2000-2200"] += 1
                        elif 2300 <= r <= 2500:
                            rating_buckets["2300-2500"] += 1
                        elif r >= 2600:
                            rating_buckets["2600+"] += 1

                    for tag in tags:
                        tag_ac[tag] = tag_ac.get(tag, 0) + 1
            else:
                for tag in tags:
                    tag_wa[tag] = tag_wa.get(tag, 0) + 1

        tag_penalty_list = []
        for tag, ac_cnt in tag_ac.items():
            wa_cnt = tag_wa.get(tag, 0)
            score = round(wa_cnt / max(ac_cnt, 1), 3)
            tag_penalty_list.append({"tag": tag, "ac": ac_cnt, "wa": wa_cnt, "score": score})
        tag_penalty_list.sort(key=lambda x: x["score"], reverse=True)

        ratings_list.sort()
        median_rating = ratings_list[len(ratings_list) // 2] if ratings_list else 1200
        current_r = user_info.get("rating", 1200)

        rec_problems = fetch_unsolved_candidates(solved_problems, current_r, target_rating)

        analytics = {
            "handle": handle,
            "rank": user_info.get("rank", "Unrated").title(),
            "rating": current_r,
            "maxRating": user_info.get("maxRating", 1200),
            "total_ac": len(solved_problems),
            "total_submissions": len(submissions),
            "days_since_last_contest": days_since_last_contest,
            "recency_note": "Ngắt quãng thi đấu rated" if days_since_last_contest > 30 else "Thi đấu đều đặn",
            "rating_distribution": rating_buckets,
            "median_rating": median_rating,
            "ac_180_days": ac_180_days,
            "recent_activity_note": "Phong độ duy trì tốt" if ac_180_days > 50 else "Cần tăng số lượng bài giải",
            "tag_penalty_data": tag_penalty_list[:5],
            "recommended_problems": rec_problems,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }
        return analytics, None

    except Exception as e:
        return None, f"Lỗi cào dữ liệu Codeforces: {e}"


def fetch_unsolved_candidates(solved_set, current_rating, target_rating=None):
    try:
        res = requests.get("https://codeforces.com/api/problemset.problems", timeout=10).json()
        if res.get("status") != "OK":
            return []

        problems = res["result"]["problems"]
        candidates = []

        t_rating = target_rating if target_rating else current_rating + 200
        target_ratings = [max(800, current_rating - 100), current_rating + 100, t_rating]

        for target_r in target_ratings:
            for p in problems:
                r = p.get("rating")
                p_id = f"{p.get('contestId')}{p.get('index')}"
                if r and abs(r - target_r) <= 50 and p_id not in solved_set:
                    link = f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}"
                    candidates.append({
                        "name": f"{p.get('contestId')}{p.get('index')} – {p.get('name')}",
                        "rating": r,
                        "link": link,
                        "tags": ", ".join(p.get("tags", [])),
                    })
                    break
        return candidates
    except Exception:
        return []
