# Codeforces AI Coach

CLI coach cho luyện tập Competitive Programming trên Codeforces — dùng AI (Groq) để phân tích
hiện trạng, lập lộ trình, gợi ý bài tập cá nhân hoá, giải thích thuật toán, cho hint không spoil,
review code, theo dõi tiến bộ/lỗi lặp lại theo thời gian...

> 📖 Xem toàn bộ danh sách lệnh + ví dụ dùng chi tiết tại [`GUIDE.md`](./USER_GUIDE.md).

---

## Tính năng chính

- **Roadmap cá nhân hoá**: `/analyze`, `/plan` — báo cáo hiện trạng + lộ trình lên target rating.
- **Recommendation Engine dùng chung**: `/daily`, `/recommend` — chọn bài dựa trên độ khó phù hợp,
  điểm yếu, roadmap, độ phổ biến, tránh lặp lại bài đã gợi ý.
- **Phân tích**: `/weakness`, `/contest_review`, `/submission_review(_cf)`, `/code_review`,
  `/complexity`.
- **Học tập**: `/editorial(_cf/_link)`, `/hint(_cf/_link)`, `/pattern(_cf/_link)`, `/socratic(_cf/_link)`,
  `/learning_graph`, `/template`, `/kb`, `/impl`, `/flashcards` (tương tác, có chấm điểm + lịch sử).
- **Theo dõi lâu dài**: `/progress` (mastery theo topic), `/mistakes` + `/mistake_log` +
  `/mistake_clear` (log lỗi lặp lại, tự gộp lỗi trùng, xoá được khi cần), `/strategy`.
- **UX crawl đề bài chống 403**: các lệnh `_cf`/`_link` tự crawl đề từ Codeforces/URL; nếu bị chặn
  (HTTP 403, Cloudflare, layout đổi...) sẽ **không văng lệnh** — tự chuyển sang cho bạn paste đề
  tay rồi tiếp tục xử lý bình thường.

---

## Cài đặt

```bash
git clone <repo-url>
cd <repo>
pip install -r requirements.txt   # requests, rich
```

### Cấu hình biến môi trường

```bash
export GROQ_API_KEY="gsk_xxx"                  # BẮT BUỘC — lấy tại https://console.groq.com
export GROQ_MODEL="llama-3.3-70b-versatile"    # tuỳ chọn, có default
export CF_COACH_DATA_DIR="$HOME/.cf_coach"     # tuỳ chọn — nơi lưu profile/lịch sử local
```

Chương trình đọc các biến này qua `os.environ` (xem `core/config.py`) — **không** tự đọc file
`.env`. Nếu muốn dùng file `.env`, cài thêm `python-dotenv` và tự `load_dotenv()` trước khi chạy,
hoặc export thủ công như trên mỗi phiên terminal.

### Chạy

```bash
python main.py
```

Gõ `/help` để xem danh sách lệnh, `/use <handle>` để đặt Codeforces handle mặc định.

---

## Cấu trúc project

```
.
├── main.py                  # entrypoint CLI
├── core/                    # logic dùng chung, không phụ thuộc CLI
│   ├── config.py             # đọc biến môi trường (API key, model, data dir)
│   ├── storage.py            # lưu/đọc lịch sử local (JSON theo từng handle)
│   ├── cf_client.py          # wrapper Codeforces API + crawler HTML best-effort
│   ├── groq_client.py        # gọi Groq LLM API
│   ├── user_profile.py       # build profile tổng hợp (rating, tag mạnh/yếu, roadmap...)
│   ├── recommendation_engine.py / difficulty_estimator.py
│   ├── mastery.py / learning_kb.py / constraint_parser.py / legacy_core.py
└── features/                 # mỗi file = 1 command/nhóm command
    ├── common.py              # helper dùng chung (context_block, ask(), fetch_source_text...)
    ├── editorial.py / hint.py / pattern.py / socratic.py
    ├── mistakes.py / progress.py / weakness.py / ...
    └── ...
```

Dữ liệu cá nhân (roadmap, mistake log, flashcard history, recommend log) lưu **local** dạng JSON
tại `CF_COACH_DATA_DIR` (mặc định `~/.cf_coach`, **nằm ngoài thư mục project** nên không bị commit
nhầm — xem thêm phần Bảo mật bên dưới).
Feel free to use
---

