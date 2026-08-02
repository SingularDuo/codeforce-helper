"""
Wrapper CHUNG cho Codeforces API + một số crawler HTML nhẹ (đề bài, submission, link ngoài).
Mọi nơi khác trong hệ thống PHẢI đi qua module này, không được tự gọi requests.get(...) rải rác.

Các hàm crawl HTML (fetch_problem_statement / fetch_submission_source / fetch_url_content) là
BEST-EFFORT: Codeforces không có API chính thức để lấy statement hay source code, nên các hàm
này parse trực tiếp trang HTML công khai. Nếu Codeforces đổi cấu trúc trang, hoặc trang yêu cầu
đăng nhập (đặc biệt là submission source của người khác), hàm sẽ raise CFClientError với thông
báo rõ ràng thay vì âm thầm trả về rác.
"""
import re
import requests

BASE = "https://codeforces.com/api"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}


class CFClientError(Exception):
    pass


def _get(endpoint, params=None, timeout=15):
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
        data = r.json()
    except Exception as e:
        raise CFClientError(f"Lỗi kết nối Codeforces API: {e}")
    if data.get("status") != "OK":
        raise CFClientError(data.get("comment", "Codeforces API trả lỗi."))
    return data["result"]


def get_user_info(handle):
    result = _get("user.info", {"handles": handle})
    return result[0]


def get_user_rating(handle):
    try:
        return _get("user.rating", {"handle": handle})
    except CFClientError:
        return []


def get_user_status(handle):
    return _get("user.status", {"handle": handle})


_PROBLEMSET_CACHE = {"data": None}


def get_problemset(use_cache=True):
    """Trả về danh sách problems, MỖI problem có thêm field 'solvedCount' (độ phổ biến / độ
    kinh điển của bài — bài càng nhiều người AC càng có xu hướng là bài chất lượng/kinh điển)."""
    if use_cache and _PROBLEMSET_CACHE["data"] is not None:
        return _PROBLEMSET_CACHE["data"]
    result = _get("problemset.problems")
    problems = result["problems"]
    stats = result.get("problemStatistics", [])
    stats_map = {f"{s.get('contestId')}{s.get('index')}": s.get("solvedCount", 0) for s in stats}
    for p in problems:
        pid = f"{p.get('contestId')}{p.get('index')}"
        p["solvedCount"] = stats_map.get(pid, 0)
    _PROBLEMSET_CACHE["data"] = problems
    return problems


def get_contest_submission_summary(handle, contest_ids):
    """
    Gộp user.status với danh sách contest_ids (rated contest) để tái tạo lại, với mỗi contest:
    với mỗi problem index đã động vào trong lúc contest diễn ra (relativeTimeSeconds hợp lệ):
      - attempts: tổng số lần nộp trong contest
      - solved: có AC trong contest không
      - solve_time_seconds: thời điểm AC tính từ lúc contest bắt đầu (None nếu chưa AC)
    Đây là cách duy nhất để có dữ liệu "thời gian giải + số lần sai (penalty)" vì CF không có
    endpoint riêng cho việc này — phải suy ra từ user.status.
    """
    contest_ids = set(contest_ids)
    subs = get_user_status(handle)
    summary = {}
    for s in subs:
        cid = s.get("contestId")
        if cid not in contest_ids:
            continue
        rel = s.get("relativeTimeSeconds")
        # CF trả 2^31-ish cho submission ngoài contest (practice) -> loại
        if rel is None or rel > 10 ** 7:
            continue
        prob = s.get("problem", {})
        idx = prob.get("index")
        if not idx:
            continue
        verdict = s.get("verdict")
        d = summary.setdefault(cid, {})
        pd = d.setdefault(idx, {"attempts": 0, "solved": False, "solve_time_seconds": None})
        pd["attempts"] += 1
        if verdict == "OK" and not pd["solved"]:
            pd["solved"] = True
            pd["solve_time_seconds"] = rel
    return summary


# ---------------------------------------------------------------------------
# Crawler HTML best-effort (KHÔNG phải API chính thức)
# ---------------------------------------------------------------------------

def _strip_html(html):
    html = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?>.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def parse_cf_problem_id(s):
    """Nhận '4A', '4 A', '1543D1', hoặc link đầy đủ -> (contest_id:int, index:str)."""
    s = s.strip()
    m = re.match(r"^(\d+)\s*([A-Za-z]\d?)$", s)
    if m:
        return int(m.group(1)), m.group(2).upper()
    m = re.search(r"codeforces\.com/(?:contest|problemset/problem|gym)/(\d+)/(?:problem/)?([A-Za-z]\d?)", s)
    if m:
        return int(m.group(1)), m.group(2).upper()
    raise ValueError(
        f"Không nhận diện được problem id/link: '{s}'. Dùng dạng '4A', '1543D1', hoặc link "
        f"https://codeforces.com/problemset/problem/<id>/<index>."
    )


def fetch_problem_statement(contest_id, index):
    """Crawl trang đề bài công khai. BEST-EFFORT — nếu CF đổi layout hoặc bài thuộc gym riêng
    tư/kèm điều kiện đặc biệt, có thể thất bại."""
    url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
    try:
        r = requests.get(url, timeout=15, headers=_HEADERS)
    except Exception as e:
        raise CFClientError(f"Không tải được đề bài {contest_id}{index}: {e}")
    if r.status_code == 403:
        raise CFClientError(
            f"Codeforces CHẶN request tự động tới bài {contest_id}{index} (HTTP 403 — anti-bot/Cloudflare "
            f"chặn IP server, KHÔNG phải bài không tồn tại). Cách khắc phục: mở "
            f"https://codeforces.com/problemset/problem/{contest_id}/{index} trên trình duyệt của bạn, "
            f"copy phần đề bài, rồi paste vào bản gõ tay (/hint, /editorial, /socratic, /pattern — "
            f"không dùng hậu tố _cf) thay vì để hệ thống tự crawl."
        )
    if r.status_code == 404:
        raise CFClientError(f"Không tìm thấy bài {contest_id}{index} trên Codeforces (HTTP 404, sai id/index).")
    if r.status_code != 200:
        raise CFClientError(
            f"Không tải được bài {contest_id}{index} (HTTP {r.status_code})."
        )
    m = re.search(r'<div class="problem-statement">(.*?)<div class="footer">', r.text, re.S)
    html_block = m.group(1) if m else r.text
    text = _strip_html(html_block)
    if len(text) < 40:
        raise CFClientError(
            f"Trích xuất đề bài {contest_id}{index} thất bại (trang có thể đã đổi cấu trúc)."
        )
    return text[:12000]


def fetch_submission_source(contest_id, submission_id):
    """
    BEST-EFFORT: Codeforces KHÔNG cung cấp API công khai để lấy source code của một submission.
    Trang https://codeforces.com/contest/<id>/submission/<subId> chỉ hiển thị source nếu:
      - bạn đang đăng nhập ĐÚNG bằng chính tài khoản đã nộp bài đó, hoặc
      - bài đó thuộc dạng công khai source (hiếm).
    Vì hệ thống này chạy không kèm cookie đăng nhập, hàm này trong đa số trường hợp sẽ raise lỗi
    rõ ràng để người dùng biết cần paste code thủ công thay vì nhận về trang lỗi/login.
    """
    url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
    try:
        r = requests.get(url, timeout=15, headers=_HEADERS)
    except Exception as e:
        raise CFClientError(f"Không tải được submission: {e}")
    m = re.search(r'<pre[^>]*id="program-source-text"[^>]*>(.*?)</pre>', r.text, re.S)
    if not m:
        raise CFClientError(
            "Không lấy được source code của submission này (Codeforces yêu cầu đăng nhập đúng "
            "chủ tài khoản để xem source người khác/chưa public). Hãy paste code trực tiếp bằng "
            "lệnh /submission_review thay vì /submission_review_cf."
        )
    source = _strip_html(m.group(1))
    return source


def fetch_url_content(url):
    """Crawl nội dung text thô từ 1 URL bất kỳ (dùng cho /editorial_link, /hint_link, ...)."""
    if not re.match(r"^https?://", url):
        raise ValueError("Link phải bắt đầu bằng http:// hoặc https://")
    try:
        r = requests.get(url, timeout=20, headers=_HEADERS)
    except Exception as e:
        raise CFClientError(f"Không tải được nội dung từ link: {e}")
    if r.status_code == 403:
        raise CFClientError(
            "Trang này CHẶN request tự động (HTTP 403 — anti-bot, không phải link sai). Cách khắc phục: "
            "mở link đó trên trình duyệt của bạn, copy nội dung đề bài, rồi paste vào bản gõ tay "
            "(/hint, /editorial, /socratic, /pattern — không dùng hậu tố _link) thay vì để hệ thống tự crawl."
        )
    if r.status_code != 200:
        raise CFClientError(f"Link trả về lỗi HTTP {r.status_code}.")
    text = _strip_html(r.text)
    if not text:
        raise CFClientError(
            "Không trích xuất được nội dung nào từ link này (trang trả về rỗng hoặc chặn truy cập)."
        )
    if len(text) < 40:
        # Trang có thật (HTTP 200) nhưng nội dung render bằng JS -> HTML tĩnh gần như rỗng.
        # Trả về best-effort kèm cảnh báo rõ ràng thay vì raise lỗi, để AI vẫn có thể thử đọc
        # phần ít ỏi lấy được thay vì chặn đứng toàn bộ tính năng.
        text = (
            f"[CẢNH BÁO: trang này có vẻ render nội dung bằng JavaScript nên chỉ crawl được "
            f"{len(text)} ký tự tĩnh, có thể KHÔNG đủ đề bài. Nếu thiếu, hãy paste trực tiếp đề bài "
            f"thay vì dùng link.]\n{text}"
        )
    return text[:16000]
