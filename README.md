Dưới đây là nội dung `README.md` đã được định dạng lại chuẩn chỉnh, chuyên nghiệp, đẹp mắt hơn với badge, icon sinh động và cấu trúc trực quan để dễ theo dõi.

---

# 🏆 Codeforces AI Coach

> **CLI Coach hỗ trợ luyện tập Competitive Programming (Codeforces) sử dụng AI (Groq)** — Phân tích hiện trạng, lập lộ trình cá nhân hóa, gợi ý bài tập, giải thích thuật toán, đưa ra hint không spoil, review code và theo dõi tiến độ/lỗi lặp lại.

📖 **Hướng dẫn chi tiết**: Xem toàn bộ danh sách lệnh và ví dụ sử dụng tại [`GUIDE.md`](https://www.google.com/search?q=./GUIDE.md).

---

## ✨ Tính năng chính

* **🎯 Roadmap & Lộ trình**:
* `/analyze`, `/plan` — Báo cáo hiện trạng kỹ năng & lập lộ trình leo target rating.


* **💡 Recommendation Engine**:
* `/daily`, `/recommend` — Tự động chọn bài dựa trên rating phù hợp, điểm yếu, lộ trình và độ phổ biến (tránh lặp lại bài đã gợi ý).


* **📊 Phân tích & Đánh giá**:
* `/weakness`, `/contest_review`, `/submission_review(_cf)`, `/code_review`, `/complexity`.


* **📚 Học tập & Luyện tập**:
* `/editorial(_cf/_link)`, `/hint(_cf/_link)`, `/pattern(_cf/_link)`, `/socratic(_cf/_link)`.
* `/learning_graph`, `/template`, `/kb`, `/impl`.
* `/flashcards` — Thẻ ghi nhớ tương tác, hỗ trợ chấm điểm và lưu lịch sử học tập.


* **📈 Theo dõi dài hạn**:
* `/progress` — Đo lường mức độ thành thạo (mastery) theo từng topic.
* `/mistakes`, `/mistake_log`, `/mistake_clear` — Quản lý nhật ký lỗi lặp lại, tự động gộp lỗi trùng lặp.
* `/strategy` — Định hình tư duy và chiến thuật làm bài.


* **🛡️ Crawl đề bài thông minh (Anti-403 Fallback)**:
* Các lệnh có hậu tố `_cf`/`_link` hỗ trợ tự động cào đề từ Codeforces hoặc URL bất kỳ.
* Nếu bị chặn (`HTTP 403`, Cloudflare, thay đổi DOM structure...), chương trình **không bị văng** — hệ thống sẽ linh hoạt chuyển sang chế độ cho phép bạn dán (paste) đề thủ công để tiếp tục xử lý.



---

## 🚀 Cài đặt

```bash
# 1. Clone repository
git clone <repo-url>
cd <repo>

# 2. Cài đặt các thư viện phụ thuộc (requests, rich, ...)
pip install -r requirements.txt

```

### 🔑 Cấu hình biến môi trường

Chương trình đọc cấu hình trực tiếp qua `os.environ` (chi tiết tại `core/config.py`).

| Biến môi trường | Trạng thái | Mô tả |
| --- | --- | --- |
| `GROQ_API_KEY` | **Bắt buộc** | Lấy API Key miễn phí tại [Groq Console](https://console.groq.com/home) |
| `GROQ_MODEL` | Tuỳ chọn | Model sử dụng (Mặc định: `llama-3.3-70b-versatile`) |
| `CF_COACH_DATA_DIR` | Tuỳ chọn | Đường dẫn lưu profile & lịch sử local (Mặc định: `~/.cf_coach`) |

**Thực thi trên Terminal:**

```bash
export GROQ_API_KEY="gsk_xxx"
export GROQ_MODEL="llama-3.3-70b-versatile"     # Tuỳ chọn
export CF_COACH_DATA_DIR="$HOME/.cf_coach"       # Tuỳ chọn

```

> **Mẹo**: Chương trình không tự động đọc file `.env`. Nếu muốn sử dụng `.env`, hãy cài thêm `python-dotenv` và gọi `load_dotenv()` trong dự án trước khi khởi chạy.

### 🏁 Chạy chương trình

```bash
python main.py

```

* Gõ `/help` để xem danh sách câu lệnh.
* Gõ `/use <handle>` để thiết lập Codeforces Handle mặc định.

---

## 📁 Cấu trúc Project

```text
.
├── main.py                     # Entrypoint CLI
├── core/                       # Core Logic (độc lập với interface CLI)
│   ├── config.py               # Quản lý cấu hình & biến môi trường
│   ├── storage.py              # Xử lý đọc/ghi data local dạng JSON theo handle
│   ├── cf_client.py             # Codeforces API wrapper + HTML crawler (best-effort)
│   ├── groq_client.py           # Wrapper kết nối Groq LLM API
│   ├── user_profile.py          # Báo cáo tổng hợp (rating, tag mạnh/yếu, roadmap...)
│   ├── recommendation_engine.py # Bộ máy gợi ý bài tập
│   ├── difficulty_estimator.py  # Đánh giá độ khó tương đối
│   └── mastery.py / learning_kb.py / constraint_parser.py / legacy_core.py
└── features/                   # Mỗi file đảm nhận 1 lệnh hoặc nhóm lệnh CLI
    ├── common.py               # Utilities chung (context_block, ask(), fetch_source_text...)
    ├── editorial.py / hint.py / pattern.py / socratic.py
    ├── mistakes.py / progress.py / weakness.py
    └── ...

```

🔒 **Lưu trữ dữ liệu cá nhân**: Lộ trình, nhật ký lỗi, lịch sử flashcard, log bài gợi ý... đều được lưu **cục bộ (local)** dưới dạng file JSON tại thư mục `CF_COACH_DATA_DIR` (mặc định: `~/.cf_coach`). Thư mục này nằm **ngoài project**, hoàn toàn an toàn và không lo bị push nhầm lên Git repository.
