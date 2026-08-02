"""
Chuẩn hoá các dòng constraint tự do người dùng gõ (vd '-1e9 < a_i < 1e9', '1e9 <= a_i',
'n <= 2*10^5', '1 <= n, m <= 100') thành dạng có cấu trúc, để đưa vào prompt /complexity
một cách nhất quán, thay vì bắt người dùng tự soạn file constraints.txt đúng format.

Không cố "hiểu đúng 100%" mọi câu tiếng Anh tự nhiên — chỉ chuẩn hoá phần SỐ + biến + so sánh,
phần nào không parse được thì giữ nguyên văn bản gốc và đánh dấu rõ để AI tự đọc, KHÔNG bịa số.
"""
import re

_OP_TOKEN = r"(<=|>=|<|>|=)"
_NUM_RE = r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?:\s*\^\s*\d+|\s*\*\*\s*\d+)?(?:\s*\*\s*10\s*\^\s*\d+)?"


def _safe_eval_num(expr):
    expr = expr.strip().replace("^", "**")
    if not re.fullmatch(r"[0-9.eE+\-*/() ]+", expr):
        raise ValueError(f"Biểu thức số không hợp lệ: {expr}")
    return eval(expr, {"__builtins__": {}}, {})


def _try_num(token):
    try:
        return _safe_eval_num(token)
    except Exception:
        return None


def _fmt(n):
    if n is None:
        return "?"
    if float(n).is_integer():
        return f"{int(n):,}"
    return f"{n:,g}"


def parse_bound_line(line):
    """
    Trả về list các dict chuẩn hoá: {"var":, "low":, "high":, "raw":, "note":}
    Hỗ trợ các dạng phổ biến:
      'n <= 2*10^5'                -> var n, high 200000
      '1 <= n <= 100'              -> var n, low 1, high 100
      '-1e9 < a_i < 1e9'           -> var a_i, low -1e9(+1 do dấu <), high 1e9-1
      '1e9 <= a_i'                 -> var a_i, low None, high 1e9 (một chiều)
      'time limit 2s' / 'memory limit 256mb' -> giữ nguyên, note='limit'
    """
    line = line.strip()
    if not line:
        return []
    if re.search(r"time\s*limit|memory\s*limit|\bTL\b|\bML\b", line, re.I):
        return [{"raw": line, "note": "limit"}]

    results = []
    for part in re.split(r",(?![^()]*\))", line):
        part = part.strip()
        if not part:
            continue
        tokens = [t.strip() for t in re.split(_OP_TOKEN, part) if t.strip() != ""]
        if len(tokens) == 3:
            a, op, b = tokens
            na, nb = _try_num(a), _try_num(b)
            if na is not None and nb is None:
                # NUM OP VAR  (vd '2*10^5 >= n' hoặc 'n <= 2*10^5' đã bắt ở nhánh dưới)
                var = b
                bound = na
                if op in ("<=", "<"):
                    results.append({"var": var, "low": bound, "high": None, "raw": part})
                else:
                    results.append({"var": var, "low": None, "high": bound, "raw": part})
            elif nb is not None and na is None:
                var = a
                bound = nb
                if op in ("<=", "<"):
                    results.append({"var": var, "low": None, "high": bound, "raw": part})
                else:
                    results.append({"var": var, "low": bound, "high": None, "raw": part})
            else:
                results.append({"raw": part, "note": "Không xác định được biến số, giữ nguyên."})
        elif len(tokens) == 5:
            a, op1, var, op2, b = tokens
            na, nb = _try_num(a), _try_num(b)
            results.append({"var": var, "low": na, "high": nb, "raw": part,
                             "note": f"{op1}/{op2} (đã coi là khoảng đóng, sai số cận biên không đáng kể ở CP)"})
        else:
            results.append({"raw": part, "note": "Không parse được cấu trúc, AI sẽ tự đọc nguyên văn."})
    return results


def to_readable(raw_line, parsed_results):
    out = []
    for r in parsed_results:
        if "var" in r:
            out.append(
                f"  - Biến '{r['var']}': low={_fmt(r.get('low'))}, high={_fmt(r.get('high'))} "
                f"(gốc: '{r['raw']}'" + (f", {r['note']}" if r.get("note") else "") + ")"
            )
        else:
            out.append(f"  - (chưa chuẩn hoá được, giữ nguyên): '{r['raw']}'" +
                        (f" [{r['note']}]" if r.get("note") else ""))
    return "\n".join(out) if out else f"  - '{raw_line}' (rỗng sau khi parse)"
