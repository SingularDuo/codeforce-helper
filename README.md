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

---

## Bảo mật — đọc trước khi public repo lên GitHub

Repo hiện **không hardcode bất kỳ API key/secret nào** trong source code (`GROQ_API_KEY` chỉ đọc
qua `os.environ`). Tuy vậy, trước khi public, hãy tự kiểm tra các điểm sau trên máy bạn — đây là
những thứ nằm **ngoài phạm vi source code** nên mình không thể tự kiểm tra thay bạn:

### 1. Đừng để lộ `GROQ_API_KEY`
- **Không** commit file `.env`, file config nào chứa `gsk_...` thật.
- Nếu từng lỡ hardcode key vào code lúc test rồi commit (kể cả đã xoá ở commit sau) — **key đó vẫn
  còn trong git history**, người khác `git log -p` là thấy. Cách xử lý:
  - Kiểm tra: `git log -p --all | grep -i "gsk_"`
  - Nếu dính: **rotate/thu hồi key ngay** tại Groq Console (tạo key mới, xoá key cũ) — xoá khỏi
    history sau đó (`git filter-repo` / BFG Repo-Cleaner) chỉ nên coi là dọn dẹp thêm, không thay
    thế được việc thu hồi key.
- Thêm `.gitignore` (đã kèm sẵn trong repo này) để chặn commit nhầm `.env`, thư mục data, v.v.

### 2. Đừng commit dữ liệu người dùng local
- `CF_COACH_DATA_DIR` (mặc định `~/.cf_coach`) chứa **mistake log, flashcard history, roadmap** —
  là dữ liệu cá nhân gắn với handle CF của bạn (không phải thông tin nhạy cảm kiểu password, nhưng
  vẫn là dữ liệu cá nhân/hoạt động học tập, không nên public không chủ đích).
- Mặc định thư mục này nằm ngoài repo (`$HOME/.cf_coach`) nên an toàn. **Chỉ rủi ro nếu bạn từng
  đổi `CF_COACH_DATA_DIR` trỏ vào trong thư mục project** để test — kiểm tra lại trước khi push:
  ```bash
  git status --ignored
  ```

### 3. Codeforces API — không có gì nhạy cảm
- `core/cf_client.py` chỉ gọi Codeforces **API công khai** (`user.info`, `user.status`,
  `problemset.problems`) — không cần login, không lưu cookie/session.
- Phần crawl HTML (`fetch_problem_statement`, `fetch_submission_source`, `fetch_url_content`) là
  **best-effort, không đăng nhập** — vì vậy `fetch_submission_source` (lấy source code submission
  người khác) sẽ thường xuyên fail do Codeforces yêu cầu đúng chủ tài khoản mới xem được source
  của chính họ. Đây là hành vi **chủ đích** để tránh cố lách xác thực của Codeforces, không phải
  bug.

### 4. `GROQ_MODEL` / rate limit
- Key Groq của bạn có quota/rate-limit riêng. Nếu key bị lộ, người khác dùng chung quota → tốn
  tiền/bị giới hạn tốc độ. Luôn coi `GROQ_API_KEY` như mật khẩu, không paste vào issue/PR/log khi
  report bug công khai.

### 5. `eval()` trong `constraint_parser.py`
- `_safe_eval_num()` dùng `eval()` để tính biểu thức số (vd `2*10^5`) nhưng đã **whitelist regex**
  chỉ cho phép ký tự `0-9 . e E + - * / ( )` trước khi eval, và `__builtins__` bị chặn — không thể
  gọi hàm/import qua input này. Đây là input do chính người dùng CLI tự gõ (constraint của bài),
  không phải input từ mạng, nên rủi ro thấp; vẫn nêu ra để bạn nắm rõ nếu audit code.

### Checklist nhanh trước khi `git push` public

- [ ] `git log -p --all | grep -i "gsk_"` → không thấy key nào
- [ ] `.env` (nếu có dùng) đã nằm trong `.gitignore`
- [ ] `git status --ignored` → thư mục data (nếu lỡ tạo trong project) đã bị ignore, không nằm
      trong staged files
- [ ] Đã `export GROQ_API_KEY` ở máy chạy thật, **không** đặt trong file commit vào repo
- [ ] Nếu từng share log lỗi/traceback ở đâu đó công khai, kiểm tra log không vô tình in ra key
      (hiện tại `groq_client.py` không log request/response chứa key, nhưng nên tự rà nếu bạn có
      thêm print/debug riêng)

---

## License

Thêm license phù hợp (vd MIT) trước khi public nếu muốn cho phép người khác dùng/fork tự do.
