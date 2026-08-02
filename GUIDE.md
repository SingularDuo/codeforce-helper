# Codeforces AI Coach — User Guide

CLI coach cho luyện tập Competitive Programming trên Codeforces, có AI (Groq) hỗ trợ phân tích,
gợi ý bài tập, giải thích thuật toán, hint, theo dõi tiến bộ...

---

## 1. Cài đặt & Chạy

```bash
export GROQ_API_KEY="gsk_xxx"          # bắt buộc
# tuỳ chọn:
export GROQ_MODEL="llama-3.3-70b-versatile"
export CF_COACH_DATA_DIR="$HOME/.cf_coach"   # nơi lưu profile/lịch sử

python main.py
```

Sau khi chạy, bạn sẽ thấy màn hình danh sách lệnh. Gõ `/help` bất cứ lúc nào để xem lại.

---

## 2. Khái niệm chung

### 2.1. Handle

Hầu hết lệnh cần một **Codeforces handle** để lấy dữ liệu người dùng (rating, bài đã giải,
điểm mạnh/yếu...). Có 2 cách cung cấp:

```
/use duxp                # đặt handle mặc định — khỏi gõ lại cho các lệnh sau
/weakness                # dùng handle mặc định "duxp"

# hoặc truyền trực tiếp mỗi lần gọi (khi CHƯA /use):
/weakness duxp
```

### 2.2. Gợi ý lệnh gõ tắt

Gõ thiếu/gõ tắt tên lệnh, hệ thống sẽ gợi ý và cho chọn số thứ tự:

```
You > /mi
'/mi' chưa đủ rõ / không tồn tại. Có phải bạn muốn:
  [1] /mistakes
  [2] /mistake_log
  Chọn số (Enter để bỏ qua) > 1
```

### 2.3. Nhập đề bài kiểu paste nhiều dòng (multiline input)

Các lệnh `/editorial`, `/hint`, `/pattern` (và các bản `_cf` / `_link` khi crawl tự động thất
bại — xem mục 2.4) dùng chung 1 kiểu nhập: **paste toàn bộ đề bài, kết thúc bằng 2 lần Enter
liên tiếp.**

```
=================================
Hãy paste toàn bộ đề bài.
Có thể paste:
- Problem Statement
- Input
- Output
- Constraints
- Notes
Nhấn Enter 2 lần liên tiếp để kết thúc.
=================================
> A. Watermelon
> Pete and his friend Billy...
> Input
> The first line contains ... n (1 ≤ n ≤ 100)
> Output
> Print YES or NO
>
>
```

Chỉ cần 2 dòng trống **liên tiếp** mới kết thúc — 1 dòng trống ở giữa đề bài (ngắt đoạn) vẫn
được giữ nguyên trong nội dung, không bị coi là tín hiệu dừng.

### 2.4. Crawl tự động lỗi (403 / lỗi mạng) — KHÔNG bao giờ bị văng lệnh

Các lệnh có hậu tố `_cf` (tự lấy đề theo problem id Codeforces) và `_link` (tự lấy đề theo URL
bất kỳ) sẽ cố crawl trước. Nếu crawl **thành công** → chạy như bình thường, không có gì khác biệt.

Nếu crawl **thất bại** (Codeforces/trang web chặn bot — HTTP 403, layout đổi, lỗi mạng...),
chương trình **không thoát lệnh**, mà in cảnh báo:

```
---------------------------------
Không thể lấy đề tự động.
Nguyên nhân:
Codeforces CHẶN request tự động tới bài 4A (HTTP 403 — anti-bot/Cloudflare chặn IP server, ...)
Điều này không phải lỗi của người dùng.
Vui lòng:
1. Mở link/bài được hiển thị ở trên.
2. Copy toàn bộ đề.
3. Paste ngay bên dưới.
4. Nhấn Enter hai lần để kết thúc.
---------------------------------
```

...rồi tự động chuyển sang màn hình paste đề (mục 2.3). Bạn paste đề vào, Enter 2 lần, AI xử lý
tiếp bình thường — không cần gõ lại lệnh từ đầu.

Áp dụng cho: `/editorial_cf`, `/editorial_link`, `/hint_cf`, `/hint_link`, `/pattern_cf`,
`/pattern_link`.

---

## 3. Danh sách lệnh

### 3.1. Hai chức năng gốc

| Lệnh | Cú pháp | Mô tả |
|---|---|---|
| `/analyze` | `/analyze <handle>` | Báo cáo hiện trạng: rating, phân bố bài giải, tag yếu, gợi ý bài khởi động. |
| `/plan` | `/plan <handle> <target_rating> <months>` | Lập lộ trình chinh phục target rating trong N tháng. Kết quả được lưu làm **roadmap**, các lệnh khác (`/daily`, `/recommend`,...) sẽ dùng roadmap này để ưu tiên độ khó bài phù hợp mục tiêu. |

```
/plan duxp 2000 3
```

### 3.2. Recommendation Engine

| Lệnh | Cú pháp | Mô tả |
|---|---|---|
| `/daily` | `/daily <L> <R> <tổng_phút>` | Sinh 1 buổi luyện gồm 3 bài (Speed / Core / Stretch — hoặc Review nếu đang gặp khó khăn liên tiếp), lọc theo dải rating L–R, thời gian mỗi bài được chia tỉ lệ từ tổng số phút bạn có. |
| `/recommend` | `/recommend [tag] [rating]` | Danh sách bài đề xuất theo nhóm Warm-up / Core / Challenge / Review / Must Solve, có thể lọc theo tag và/hoặc rating. |

```
/daily 1400 1800 90
/recommend dp 2200
/recommend            # không filter gì
```

### 3.3. Phân tích

| Lệnh | Cú pháp | Mô tả |
|---|---|---|
| `/weakness` | `/weakness` | Phân tích điểm mạnh/yếu theo tag (mastery, rating ceiling, bottleneck WA/AC). |
| `/contest_review` | `/contest_review [n_gần_nhất]` | Phân tích N contest rated gần nhất: rating trend, solve-time, penalty, pattern lặp lại. Mặc định n=10. |
| `/submission_review` | `/submission_review <path_to_code_file> [language]` | Review performance/implementation (KHÔNG đụng logic thuật toán) từ file code bạn trỏ tới. `language` mặc định `c++`. |
| `/submission_review_cf` | `/submission_review_cf <link_submission> [language]` | Giống trên nhưng tự crawl source code từ link submission Codeforces (best-effort — CF thường chặn xem source người khác). |
| `/code_review` | `/code_review <path_to_code_file> [language]` | Review style code: naming, readability, structure, duplication... |
| `/complexity` | `/complexity <path_to_code_file>` | Ước lượng độ phức tạp runtime/memory. Sau khi gõ lệnh, hệ thống hỏi bạn nhập từng dòng constraint tự do (vd `1 <= n <= 2*10^5`), Enter dòng trống để kết thúc — không cần soạn file constraints.txt riêng. |

```
/submission_review ./sol.cpp c++
/submission_review_cf https://codeforces.com/contest/4/submission/123456789
/complexity ./sol.cpp
```

### 3.4. Học tập

| Lệnh | Cú pháp | Mô tả |
|---|---|---|
| `/editorial` | `/editorial` | Giải thích editorial theo 3 mức Beginner/Intermediate/Advanced. Sau khi gõ lệnh, **paste đề bài** theo flow ở mục 2.3. |
| `/editorial_cf` | `/editorial_cf <problem_id>` | Tự crawl đề theo problem id Codeforces (vd `4A`) rồi sinh editorial. Nếu crawl lỗi → tự chuyển sang paste tay (mục 2.4), không thoát lệnh. |
| `/editorial_link` | `/editorial_link <url>` | Tự crawl đề từ 1 URL OJ bất kỳ, AI **tự giải bài** (vì không có editorial gốc) rồi giải thích 3 mức. Nếu crawl lỗi → chuyển sang paste tay. |
| `/hint` | `/hint <hint1\|hint2\|hint3\|almost\|final>` | Hint tăng dần, không spoil ngay. Sau khi gõ lệnh + mức hint, **paste đề bài**. |
| `/hint_cf` | `/hint_cf <mức> <problem_id>` | Giống trên, tự crawl đề theo problem id. Lỗi crawl → paste tay. |
| `/hint_link` | `/hint_link <mức> <url>` | Giống trên, tự crawl đề theo URL. Lỗi crawl → paste tay. |
| `/progress` | `/progress` | Mastery theo từng topic (công thức volume + accuracy + ceiling, không phải "AC N bài = N% giỏi"). |
| `/learning_graph` | `/learning_graph <topic...>` | Vẽ sơ đồ kiến thức tiền đề (prerequisite chain) dẫn tới topic, kèm chú thích đã vững/đang học/chưa học. |
| `/flashcards` | `/flashcards <topic...> [n]` | Sinh N flashcard (mặc định 5), **tương tác trực tiếp**: mỗi câu bạn gõ câu trả lời ngay trong CLI, AI chấm và lưu lại lịch sử. |
| `/flashcards_history` | `/flashcards_history [n]` | Xem lại N lượt trả lời flashcard gần nhất (mặc định 20). |
| `/template` | `/template <topic...> [language]` | Sinh template code cho cấu trúc dữ liệu/thuật toán, kèm Complexity / When to use / When NOT to use / Common Bugs, mỗi hàm có chú thích dùng khi nào. |
| `/kb` | `/kb <thuật_toán...> [language]` | Tra cứu kiến thức: Ý tưởng, Proof, Complexity, Implementation, Common Bugs, kèm link tài liệu/visualization đã kiểm chứng (cp-algorithms, visualgo...). |
| `/impl` | `/impl <topic...> [language]` | Hướng dẫn implementation từng bước (chỉ các bước thực sự cần thiết, không ép khuôn cứng), kèm code minh hoạ + Common Bugs. |
| `/socratic` | `/socratic <đề_bài...>` | Coach kiểu Socratic: đặt câu hỏi dẫn dắt, KHÔNG giải bài trực tiếp. |
| `/socratic_cf` | `/socratic_cf <problem_id>` | Giống trên, tự crawl đề theo problem id. |
| `/socratic_link` | `/socratic_link <url>` | Giống trên, tự crawl đề theo URL. |

```
/editorial_cf 4A
# nếu 403 -> paste đề tay theo hướng dẫn hiện ra

/hint hint1
# -> màn hình paste đề hiện ra, paste xong Enter x2

/pattern_link https://oj.example.com/problem/123
# nếu crawl lỗi -> paste tay, AI vẫn nhận diện pattern bình thường

/template segment tree c++
/kb dsu c++
/learning_graph fenwick tree
```

> **Lưu ý về `/socratic_cf` và `/socratic_link`:** 2 lệnh này vẫn giữ hành vi cũ — nếu crawl lỗi
> sẽ báo lỗi và dừng lệnh (không nằm trong phạm vi thay đổi của bản cập nhật này).

### 3.5. Theo dõi lâu dài

| Lệnh | Cú pháp | Mô tả |
|---|---|---|
| `/mistakes` | `/mistakes` | Tổng hợp Top lỗi lặp lại từ mistake log, sắp theo tần suất (count giảm dần). |
| `/mistake_log` | `/mistake_log <type> <note...>` | Ghi 1 lỗi mới. Nếu lỗi tương tự (≥ 80% giống) đã tồn tại, chỉ tăng biến đếm `count` thay vì tạo bản ghi trùng. |
| `/mistake_clear` | `/mistake_clear` | **Xoá toàn bộ mistake log** của handle hiện tại. Có hỏi xác nhận trước khi xoá (gõ đúng `yes` mới xoá, hành động không thể hoàn tác). |
| `/pattern` | `/pattern` | Nhận diện pattern kỹ thuật + đề xuất bài luyện tương tự. Sau khi gõ lệnh, **paste mô tả bài/code**. |
| `/pattern_cf` | `/pattern_cf <problem_id>` | Giống trên, tự crawl đề theo problem id. Lỗi crawl → paste tay. |
| `/pattern_link` | `/pattern_link <url>` | Giống trên, tự crawl đề theo URL. Lỗi crawl → paste tay. |
| `/strategy` | `/strategy <path_to_contest_log_file>` | Đánh giá chiến thuật làm contest (skip bài nào, thứ tự đọc đề, thời gian kẹt...) từ 1 file nhật ký contest bạn cung cấp. |

```
/mistake_log implementation "quên xử lý overflow khi n lớn"
/pattern_cf 1543D
/strategy ./contest_log.txt
```

**Xoá mistake log:**

```
You > /mistake_clear
Bạn có chắc muốn XOÁ TOÀN BỘ mistake log của 'duxp'? Hành động này KHÔNG thể hoàn tác.
  Gõ 'yes' để xác nhận, Enter để huỷ > yes
🗑️ Đã xoá toàn bộ mistake log (7 mục).
```

Nếu gõ bất kỳ gì khác `yes` (kể cả Enter trống), lệnh sẽ huỷ, không xoá gì:

```
You > /mistake_clear
Bạn có chắc muốn XOÁ TOÀN BỘ mistake log của 'duxp'? Hành động này KHÔNG thể hoàn tác.
  Gõ 'yes' để xác nhận, Enter để huỷ > 
Đã huỷ, không xoá gì.
```

> **Lưu ý:** `/mistake_clear` chỉ xoá mảng `mistakes` trong file lưu trữ của handle — KHÔNG đụng
> tới roadmap, lịch sử recommend, flashcards hay topic_progress.

### 3.6. Khác

| Lệnh | Mô tả |
|---|---|
| `/use <handle>` | Đặt handle mặc định cho các lệnh sau, khỏi phải gõ lại mỗi lần. |
| `/help` | In lại toàn bộ danh sách lệnh. |
| `exit` / `quit` | Thoát chương trình. |

---

## 4. Ví dụ luồng làm việc điển hình

```
You > /use duxp
Đã đặt handle mặc định: duxp

You > /analyze
[... báo cáo hiện trạng ...]

You > /plan 2000 3
[... roadmap 3 tháng lên 2000 rating, được lưu lại ...]

You > /daily 1400 1800 90
[... 3 bài Speed/Core/Stretch, thời gian chia từ 90 phút ...]

You > /hint hint1
=================================
Hãy paste toàn bộ đề bài.
...
=================================
> [paste đề bài vào đây]
>
>
[... Hint 1, không spoil lời giải ...]

You > /editorial_cf 4A
Đang crawl đề bài từ Codeforces...

---------------------------------
Không thể lấy đề tự động.
Nguyên nhân:
Codeforces CHẶN request tự động tới bài 4A (HTTP 403 ...)
...
---------------------------------
=================================
Hãy paste toàn bộ đề bài.
...
=================================
> [paste đề đã copy từ trình duyệt]
>
>
[... editorial 3 mức Beginner/Intermediate/Advanced ...]

You > /mistake_log implementation "off-by-one khi duyệt mảng"
✅ Đã ghi nhận lỗi mới: [implementation] off-by-one khi duyệt mảng

You > /weakness
[... phân tích điểm mạnh/yếu theo tag ...]

You > exit
```

---

## 5. Lưu ý chung

- Toàn bộ dữ liệu cá nhân (roadmap, mistake log, flashcard history, lịch sử recommend...) được
  lưu **local** dưới dạng file JSON theo từng handle tại `CF_COACH_DATA_DIR` (mặc định
  `~/.cf_coach`), không cần database ngoài.
- Các lệnh `_cf` dựa vào Codeforces API chính thức (`user.info`, `user.status`, `problemset.problems`...)
  cho phần dữ liệu số liệu — phần **crawl HTML** (đề bài, source submission, nội dung link ngoài)
  là **best-effort**, có thể fail nếu Codeforces/trang đích chặn bot. Khi đó luôn có đường paste
  tay để không bị chặn hoàn toàn công việc.
- Codeforces **không cho xem source code submission của người khác** qua trang public nếu không
  đăng nhập đúng chủ tài khoản — `/submission_review_cf` phần lớn sẽ báo lỗi rõ ràng trong
  trường hợp này, hãy dùng `/submission_review` (paste code) thay thế.
