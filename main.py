import sys
import shlex

from rich.console import Console
from rich.markdown import Markdown

from core.groq_client import GroqClientError
from core.cf_client import CFClientError
from features import (
    analyze, plan, daily, recommend, weakness, contest_review,
    submission_review, submission_review_cf, code_review, editorial, hint, complexity,
    progress, learning_graph, flashcards, mistakes, pattern,
    template as template_feat, strategy, kb, impl_coach, socratic, common,
)

console = Console()

ALL_COMMANDS = [
    "/analyze", "/plan", "/daily", "/recommend", "/weakness", "/contest_review",
    "/submission_review", "/submission_review_cf", "/code_review", "/complexity",
    "/editorial", "/editorial_cf", "/editorial_link", "/hint", "/hint_cf", "/hint_link",
    "/progress", "/learning_graph", "/flashcards", "/flashcards_history",
    "/mistakes", "/mistake_log", "/mistake_clear", "/pattern", "/pattern_cf", "/pattern_link",
    "/template", "/kb", "/impl", "/socratic", "/socratic_cf", "/socratic_link",
    "/strategy", "/use", "/help",
]


def suggest_commands(cmd):
    """vd gõ '/mi' -> gợi ý /mistakes, /mistake_log kèm số thứ tự để CHỌN LUÔN (không cần gõ lại)."""
    matches = [c for c in ALL_COMMANDS if c.startswith(cmd)]
    if not matches:
        return None
    console.print(f"[yellow]'{cmd}' chưa đủ rõ / không tồn tại. Có phải bạn muốn:[/yellow]")
    for i, m in enumerate(matches, 1):
        console.print(f"  [{i}] {m}")
    return matches

HELP = """
[bold magenta]=== CODEFORCES AI COACH ===[/bold magenta]

[bold]-- Hai chức năng gốc (không đổi) --[/bold]
  /analyze <handle>
  /plan <handle> <target_rating> <months>          vd: /plan duxp 2000 3

[bold]-- Recommendation Engine dùng chung --[/bold]
  /daily <L> <R> <tong_phut>                        vd: /daily 1400 1800 90
  /recommend [tag] [rating]                         vd: /recommend dp 2200

[bold]-- Phân tích --[/bold]
  /weakness
  /contest_review [n_gan_nhat]
  /submission_review <path_to_code_file> [language]         (paste code thủ công)
  /submission_review_cf <link_submission> [language]        (tự crawl, best-effort)
  /code_review <path_to_code_file> [language]
  /complexity <path_to_code_file>                            (sẽ hỏi constraint tương tác)

[bold]-- Học tập --[/bold]
  /editorial <mo_ta_hoac_editorial...>              (tự gõ)
  /editorial_cf <problem_id>                        vd: /editorial_cf 4A
  /editorial_link <url>                             (bài trên OJ bất kỳ, AI tự giải)
  /hint <hint1|hint2|hint3|almost|final> <de_bai...>
  /hint_cf <mức> <problem_id>
  /hint_link <mức> <url>
  /progress
  /learning_graph <topic...>
  /flashcards <topic...> [n]                        (interactive: trả lời trực tiếp trong CLI)
  /flashcards_history [n]                           in lại n lượt trả lời flashcard gần nhất (mặc định 20)
  /template <topic...> [language]
  /kb <thuat_toan...> [language]
  /impl <topic...> [language]
  /socratic <de_bai...>
  /socratic_cf <problem_id>
  /socratic_link <url>

[bold]-- Theo dõi lâu dài --[/bold]
  /mistakes
  /mistake_log <type> <note...>
  /mistake_clear                                    (xoá toàn bộ mistake log, có hỏi xác nhận)
  /pattern <mo_ta_hoac_code...>
  /pattern_cf <problem_id>
  /pattern_link <url>
  /strategy <path_to_contest_log_file>

[bold]-- Khác --[/bold]
  /use <handle>     đặt handle mặc định cho các lệnh sau (khỏi gõ lại)
  /help
  exit
"""


def render(md_text):
    console.print("")  # tách rõ khỏi output crawl/log phía trên (vd đề bài vừa crawl cho /hint)
    console.print(Markdown(md_text))
    console.print("\n" + "─" * 60)


def print_error(msg):
    """Trước đây các thông báo lỗi (vd crawl fail, HTTP 403...) in dính sát ngay dưới dòng
    'Đang crawl...' phía trên, nhìn rối. Thêm dòng trắng để tách rõ, đồng bộ với render()."""
    console.print("")
    console.print(f"[bold red]{msg}[/bold red]")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def collect_interactive_lines(prompt_text):
    console.print(f"[cyan]{prompt_text} (Enter dòng trống để kết thúc)[/cyan]")
    lines = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        lines.append(line)
    return lines


def read_multiline_input():
    """Helper dùng CHUNG cho mọi command cần paste nguyên đề bài (/editorial, /hint, /pattern,
    và luồng fallback của các bản _cf/_link khi crawl tự động thất bại). Đọc nhiều dòng liên
    tiếp, chỉ dừng khi gặp ĐÚNG 2 dòng trống liên tiếp, rồi ghép lại thành 1 string."""
    console.print("=================================")
    console.print("[cyan]Hãy paste toàn bộ đề bài.[/cyan]")
    console.print("[cyan]Có thể paste:[/cyan]")
    console.print("[cyan]- Problem Statement[/cyan]")
    console.print("[cyan]- Input[/cyan]")
    console.print("[cyan]- Output[/cyan]")
    console.print("[cyan]- Constraints[/cyan]")
    console.print("[cyan]- Notes[/cyan]")
    console.print("[cyan]Nhấn Enter 2 lần liên tiếp để kết thúc.[/cyan]")
    console.print("=================================")
    lines = []
    blank_count = 0
    while True:
        line = input("> ")
        if line.strip() == "":
            blank_count += 1
            if blank_count >= 2:
                break
        else:
            blank_count = 0
        lines.append(line)
    # 2 dòng trống dùng để kết thúc không phải nội dung đề bài -> bỏ khoảng trắng thừa cuối cùng
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines)


def fetch_or_prompt_problem(problem_ref=None, url=None):
    """Helper dùng CHUNG cho /editorial_cf, /editorial_link, /hint_cf, /hint_link, /pattern_cf,
    /pattern_link: thử crawl đề bài tự động trước. Nếu crawl OK -> hoạt động y hệt trước giờ.
    Nếu crawl lỗi (HTTP 403 hoặc bất kỳ lỗi nào khác) -> KHÔNG terminate command, in rõ lý do rồi
    chuyển sang flow paste thủ công dùng chung với read_multiline_input()."""
    try:
        if problem_ref:
            text, source_label = common.fetch_source_text(problem_ref=problem_ref)
        else:
            text, source_label = common.fetch_source_text(link=url)
        return text, source_label
    except Exception as e:
        console.print("")
        console.print("[bold red]---------------------------------[/bold red]")
        console.print("[bold red]Không thể lấy đề tự động.[/bold red]")
        console.print("[bold red]Nguyên nhân:[/bold red]")
        console.print(f"[red]{e}[/red]")
        console.print("[yellow]Điều này không phải lỗi của người dùng.[/yellow]")
        console.print("[yellow]Vui lòng:[/yellow]")
        console.print("[yellow]1. Mở link/bài được hiển thị ở trên.[/yellow]")
        console.print("[yellow]2. Copy toàn bộ đề.[/yellow]")
        console.print("[yellow]3. Paste ngay bên dưới.[/yellow]")
        console.print("[yellow]4. Nhấn Enter hai lần để kết thúc.[/yellow]")
        console.print("[bold red]---------------------------------[/bold red]")
        text = read_multiline_input()
        source_label = "Paste thủ công (crawl tự động thất bại)"
        return text, source_label


def main():
    console.print(HELP)
    current_handle = None

    while True:
        try:
            raw = input("\nYou > ").strip()
            if not raw:
                continue
            if raw.lower() in ("exit", "quit"):
                break
            if raw == "/help":
                console.print(HELP)
                continue

            try:
                parts = shlex.split(raw)
            except ValueError as e:
                console.print(f"[bold red]Lỗi cú pháp dòng lệnh:[/bold red] {e}")
                continue

            redo = True
            while redo:
                redo = False
                cmd = parts[0]

                if cmd == "/use":
                    if len(parts) < 2:
                        console.print("[bold red]Cú pháp: /use <handle>[/bold red]")
                        continue
                    current_handle = parts[1]
                    console.print(f"[green]Đã đặt handle mặc định: {current_handle}[/green]")
                    continue

                def get_handle(idx=1, args=parts):
                    if current_handle:
                        return current_handle, idx
                    if len(args) <= idx:
                        raise ValueError("Thiếu handle. Dùng /use <handle> trước, hoặc truyền handle làm tham số.")
                    return args[idx], idx + 1

                # ---------------- 2 chức năng gốc (KHÔNG đổi output) ----------------
                if cmd == "/analyze":
                    handle, _ = get_handle()
                    console.print(f"\n[bold cyan]Đang phân tích chuyên sâu cho '{handle}'...[/bold cyan]")
                    result, err = analyze.run(handle)
                    if err:
                        print_error(err)
                        continue
                    render(result)

                elif cmd == "/plan":
                    handle, next_i = get_handle()
                    if len(parts) < next_i + 2:
                        console.print("[bold red]Cú pháp: /plan <handle> <target_rating> <months>[/bold red]")
                        continue
                    target_rating = int(parts[next_i])
                    months = int(parts[next_i + 1])
                    console.print(
                        f"\n[bold cyan]Đang lập lộ trình chinh phục {target_rating} rating "
                        f"trong {months} tháng cho '{handle}'...[/bold cyan]"
                    )
                    result, err = plan.run(handle, target_rating, months)
                    if err:
                        print_error(err)
                        continue
                    render(result)

                # ---------------- Recommendation Engine ----------------
                elif cmd == "/daily":
                    handle, next_i = get_handle()
                    if len(parts) < next_i + 3:
                        print_error(
                            "Cú pháp: /daily <L> <R> <tổng_phút>  (vd: /daily 1400 1800 90 nghĩa là "
                            "muốn luyện bài rating 1400-1800, có tổng 90 phút hôm nay)"
                        )
                        continue
                    try:
                        low_rating = int(parts[next_i])
                        high_rating = int(parts[next_i + 1])
                        total_minutes = int(parts[next_i + 2])
                    except ValueError:
                        print_error("L, R, tổng phút phải là số nguyên. Cú pháp: /daily <L> <R> <tổng_phút>")
                        continue
                    if low_rating > high_rating:
                        low_rating, high_rating = high_rating, low_rating
                    console.print(
                        f"\n[bold cyan]Đang tạo buổi luyện tập hôm nay cho '{handle}' "
                        f"(rating {low_rating}-{high_rating}, {total_minutes} phút)...[/bold cyan]"
                    )
                    result, err = daily.run(handle, low_rating, high_rating, total_minutes)
                    if err:
                        print_error(err); continue
                    render(result)

                elif cmd == "/recommend":
                    handle, next_i = get_handle()
                    tag = parts[next_i] if len(parts) > next_i else None
                    rating = None
                    if len(parts) > next_i + 1:
                        try:
                            rating = int(parts[next_i + 1])
                        except ValueError:
                            pass
                    console.print(f"\n[bold cyan]Đang tìm bài phù hợp cho '{handle}'...[/bold cyan]")
                    result, err = recommend.run(handle, tag, rating)
                    if err:
                        print_error(err); continue
                    render(result)

                # ---------------- Phân tích ----------------
                elif cmd == "/weakness":
                    handle, _ = get_handle()
                    result, err = weakness.run(handle)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/contest_review":
                    handle, next_i = get_handle()
                    n = int(parts[next_i]) if len(parts) > next_i else 10
                    result, err = contest_review.run(handle, n)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/submission_review":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /submission_review <path_to_code_file> [language][/bold red]")
                        continue
                    code = read_file(parts[next_i])
                    lang = parts[next_i + 1] if len(parts) > next_i + 1 else "c++"
                    result, err = submission_review.run(handle, code, lang)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/submission_review_cf":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /submission_review_cf <link_submission> [language][/bold red]")
                        continue
                    link = parts[next_i]
                    lang = parts[next_i + 1] if len(parts) > next_i + 1 else "c++"
                    console.print("[bold cyan]Đang thử crawl source code từ Codeforces (best-effort)...[/bold cyan]")
                    result, err = submission_review_cf.run(handle, link, lang)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/code_review":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /code_review <path_to_code_file> [language][/bold red]")
                        continue
                    code = read_file(parts[next_i])
                    lang = parts[next_i + 1] if len(parts) > next_i + 1 else "c++"
                    result, err = code_review.run(handle, code, lang)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/complexity":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /complexity <path_to_code_file>[/bold red]")
                        continue
                    code = read_file(parts[next_i])
                    console.print("[cyan]Nhập từng dòng giới hạn biến (vd '1 <= n <= 2*10^5', '-1e9 <= a_i <= 1e9', "
                                   "'time limit 2s'). Không cần lo về dạng '<' hay '<=', hệ thống tự chuẩn hoá.[/cyan]")
                    bound_lines = collect_interactive_lines("Nhập constraints")
                    result, err = complexity.run(handle, bound_lines, code)
                    if err: print_error(err); continue
                    render(result)

                # ---------------- Học tập ----------------
                elif cmd == "/editorial":
                    handle, _ = get_handle()
                    text = read_multiline_input()
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = editorial.run(handle, text)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/editorial_cf":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /editorial_cf <problem_id> (vd 4A)[/bold red]")
                        continue
                    console.print("[bold cyan]Đang crawl đề bài từ Codeforces...[/bold cyan]")
                    text, source_label = fetch_or_prompt_problem(problem_ref=parts[next_i])
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = editorial.run_with_text(handle, text, source_label)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/editorial_link":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /editorial_link <url>[/bold red]")
                        continue
                    console.print("[bold cyan]Đang crawl nội dung từ link (AI sẽ tự giải bài này)...[/bold cyan]")
                    text, source_label = fetch_or_prompt_problem(url=parts[next_i])
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = editorial.run_with_text_link(handle, text, source_label)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/hint":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /hint <hint1|hint2|hint3|almost|final>[/bold red]")
                        continue
                    level = parts[next_i]
                    text = read_multiline_input()
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = hint.run(handle, text, level)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/hint_cf":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i + 1:
                        console.print("[bold red]Cú pháp: /hint_cf <mức> <problem_id>[/bold red]")
                        continue
                    level = parts[next_i]
                    console.print("[bold cyan]Đang crawl đề bài từ Codeforces...[/bold cyan]")
                    text, source_label = fetch_or_prompt_problem(problem_ref=parts[next_i + 1])
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = hint.run_with_text(handle, level, text, source_label)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/hint_link":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i + 1:
                        console.print("[bold red]Cú pháp: /hint_link <mức> <url>[/bold red]")
                        continue
                    level = parts[next_i]
                    console.print("[bold cyan]Đang crawl nội dung từ link...[/bold cyan]")
                    text, source_label = fetch_or_prompt_problem(url=parts[next_i + 1])
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = hint.run_with_text_link(handle, level, text, source_label)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/progress":
                    handle, _ = get_handle()
                    result, err = progress.run(handle)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/learning_graph":
                    handle, next_i = get_handle()
                    topic = " ".join(parts[next_i:]) or "Segment Tree"
                    result, err = learning_graph.run(handle, topic)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/flashcards":
                    handle, next_i = get_handle()
                    rest = parts[next_i:]
                    n = 5
                    if rest and rest[-1].isdigit():
                        n = int(rest[-1]); rest = rest[:-1]
                    topic = " ".join(rest) or "General"
                    cards, err = flashcards.generate(handle, topic, n)
                    if err:
                        print_error(err); continue
                    console.print(f"\n[bold magenta]{len(cards)} flashcard về '{topic}' — trả lời từng câu:[/bold magenta]")
                    for i, c in enumerate(cards, 1):
                        console.print(f"\n[bold]Câu {i}:[/bold] {c['question']}")
                        user_answer = input("  Trả lời của bạn > ").strip()
                        verdict = None
                        if not user_answer:
                            console.print("[yellow](bỏ qua)[/yellow]")
                        else:
                            verdict = flashcards.grade_answer(c["question"], c["answer"], user_answer)
                            v_lower = verdict.lower()
                            if v_lower.startswith("sai") or "kết quả: sai" in v_lower:
                                color = "bold red"
                            elif v_lower.startswith("gần đúng") or "gần đúng" in v_lower.split("\n")[0].lower():
                                color = "yellow"
                            else:
                                color = "green"
                            console.print(f"[{color}]{verdict}[/{color}]")
                        console.print(f"[dim]Đáp án chuẩn: {c['answer']}[/dim]")
                        flashcards.save_card_result(handle, topic, c["question"], c["answer"], user_answer, verdict)
                    console.print("\n[bold green]Đã hoàn thành bộ flashcard và lưu lại lịch sử.[/bold green]")

                elif cmd == "/flashcards_history":
                    handle, next_i = get_handle()
                    n = int(parts[next_i]) if len(parts) > next_i and parts[next_i].isdigit() else 20
                    items = flashcards.history(handle, n)
                    if not items:
                        console.print("[yellow](Chưa có lịch sử flashcard nào.)[/yellow]")
                        continue
                    console.print(f"\n[bold magenta]Lịch sử {len(items)} flashcard gần nhất ('{handle}'):[/bold magenta]")
                    for it in items:
                        v = (it.get("verdict") or "").lower()
                        color = "red" if v.startswith("sai") else ("yellow" if "gần đúng" in v else "green")
                        console.print(f"\n[bold]{it['date']}[/bold] | topic: {it['topic']}")
                        console.print(f"  Q: {it['question']}")
                        console.print(f"  Trả lời của bạn: {it.get('user_answer') or '(bỏ qua)'}")
                        if it.get("verdict"):
                            console.print(f"  [{color}]Kết quả: {it['verdict']}[/{color}]")
                        console.print(f"  [dim]Đáp án chuẩn: {it['answer']}[/dim]")

                elif cmd == "/template":
                    handle, next_i = get_handle()
                    rest = parts[next_i:]
                    lang = "c++"
                    if rest and rest[-1] in ("c++", "python", "java", "cpp"):
                        lang = rest[-1]; rest = rest[:-1]
                    topic = " ".join(rest)
                    result, err = template_feat.run(handle, topic, lang)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/kb":
                    handle, next_i = get_handle()
                    rest = parts[next_i:]
                    lang = "c++"
                    if rest and rest[-1] in ("c++", "python", "java", "cpp"):
                        lang = rest[-1]; rest = rest[:-1]
                    topic = " ".join(rest)
                    result, err = kb.run(handle, topic, lang)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/impl":
                    handle, next_i = get_handle()
                    rest = parts[next_i:]
                    lang = "c++"
                    if rest and rest[-1] in ("c++", "python", "java", "cpp"):
                        lang = rest[-1]; rest = rest[:-1]
                    topic = " ".join(rest)
                    result, err = impl_coach.run(handle, topic, lang)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/socratic":
                    handle, next_i = get_handle()
                    text = " ".join(parts[next_i:])
                    result, err = socratic.run(handle, text)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/socratic_cf":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /socratic_cf <problem_id>[/bold red]")
                        continue
                    result, err = socratic.run_from_cf(handle, parts[next_i])
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/socratic_link":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /socratic_link <url>[/bold red]")
                        continue
                    result, err = socratic.run_from_link(handle, parts[next_i])
                    if err: print_error(err); continue
                    render(result)

                # ---------------- Theo dõi lâu dài ----------------
                elif cmd == "/mistakes":
                    handle, _ = get_handle()
                    result, err = mistakes.run(handle)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/mistake_log":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i + 1:
                        console.print("[bold red]Cú pháp: /mistake_log <type> <note...>[/bold red]")
                        continue
                    mtype = parts[next_i]
                    note = " ".join(parts[next_i + 1:])
                    console.print(mistakes.log(handle, mtype, note))

                elif cmd == "/mistake_clear":
                    handle, _ = get_handle()
                    console.print(
                        f"[yellow]Bạn có chắc muốn XOÁ TOÀN BỘ mistake log của '{handle}'? "
                        f"Hành động này KHÔNG thể hoàn tác.[/yellow]"
                    )
                    confirm = input("  Gõ 'yes' để xác nhận, Enter để huỷ > ").strip().lower()
                    if confirm != "yes":
                        console.print("[cyan]Đã huỷ, không xoá gì.[/cyan]")
                        continue
                    console.print(mistakes.clear(handle))

                elif cmd == "/pattern":
                    handle, _ = get_handle()
                    text = read_multiline_input()
                    if not text.strip():
                        console.print("[bold red]Chưa nhập mô tả/code nào.[/bold red]")
                        continue
                    result, err = pattern.run(handle, text)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/pattern_cf":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /pattern_cf <problem_id>[/bold red]")
                        continue
                    console.print("[bold cyan]Đang crawl đề bài từ Codeforces...[/bold cyan]")
                    text, source_label = fetch_or_prompt_problem(problem_ref=parts[next_i])
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = pattern.run_with_text(handle, text, source_label)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/pattern_link":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /pattern_link <url>[/bold red]")
                        continue
                    console.print("[bold cyan]Đang crawl nội dung từ link...[/bold cyan]")
                    text, source_label = fetch_or_prompt_problem(url=parts[next_i])
                    if not text.strip():
                        console.print("[bold red]Chưa nhập đề bài nào.[/bold red]")
                        continue
                    result, err = pattern.run_with_text(handle, text, source_label)
                    if err: print_error(err); continue
                    render(result)

                elif cmd == "/strategy":
                    handle, next_i = get_handle()
                    if len(parts) <= next_i:
                        console.print("[bold red]Cú pháp: /strategy <path_to_contest_log_file>[/bold red]")
                        continue
                    log_text = read_file(parts[next_i])
                    result, err = strategy.run(handle, log_text)
                    if err: print_error(err); continue
                    render(result)

                else:
                    matches = suggest_commands(cmd)
                    if not matches:
                        console.print(f"[bold red]Lệnh không tồn tại:[/bold red] {cmd}. Gõ /help để xem danh sách lệnh.")
                    elif len(matches) == 1:
                        parts = [matches[0]] + parts[1:]
                        redo = True
                    else:
                        sel = input("  Chọn số (Enter để bỏ qua) > ").strip()
                        if sel.isdigit() and 1 <= int(sel) <= len(matches):
                            parts = [matches[int(sel) - 1]] + parts[1:]
                            redo = True

        except (GroqClientError, CFClientError) as e:
            print_error(f"Lỗi: {e}")
        except FileNotFoundError as e:
            print_error(f"Không tìm thấy file: {e}")
        except ValueError as e:
            print_error(str(e))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print_error(f"Lỗi không xác định: {e}")


if __name__ == "__main__":
    main()