"""
Mastery Estimation dùng chung cho /progress và /weakness.

Vấn đề của bản cũ: coi "AC 93 bài" ~ "93% mastery" là SAI logic (làm 93 bài dễ không có nghĩa
gì nhiều nếu ceiling thấp). Công thức mới kết hợp 3 tín hiệu, KHÔNG suy ra 1-1 từ số bài:

  mastery = 0.4 * volume_factor      (đã luyện đủ nhiều bài ở tag này chưa, bão hoà dần)
          + 0.3 * accuracy_factor    (tỉ lệ AC / (AC+WA), phản ánh độ chắc tay)
          + 0.3 * ceiling_factor     (rating cao nhất từng AC so với rating MAX của chính user)

Diễn giải: một người AC 93 bài Math nhưng ceiling chỉ 1300 trong khi max rating cá nhân là 1900
thì KHÔNG thể coi là "93% thành thạo Math" — ceiling_factor sẽ kéo mastery xuống, phản ánh đúng
việc bài AC được chủ yếu là bài dễ.
"""

VOLUME_SATURATION = 40  # từ ~40 bài AC trở lên coi là đủ volume cho 1 tag


def estimate(tag_stat, user_max_rating):
    ac = tag_stat.get("ac", 0)
    wa = tag_stat.get("wa", 0)
    ceiling = tag_stat.get("ceiling", 0) or 0

    volume_factor = min(1.0, ac / VOLUME_SATURATION)
    accuracy_factor = ac / max(ac + wa, 1)

    if user_max_rating and ceiling:
        ceiling_factor = min(1.0, ceiling / user_max_rating)
    elif ceiling == 0:
        ceiling_factor = 0.15  # AC toàn bài unrated ở tag này -> chưa thử sức ở độ khó thật
    else:
        ceiling_factor = 0.3

    mastery = 0.4 * volume_factor + 0.3 * accuracy_factor + 0.3 * ceiling_factor
    return {
        "mastery_pct": round(mastery * 100, 1),
        "volume_factor": round(volume_factor, 2),
        "accuracy_factor": round(accuracy_factor, 2),
        "ceiling_factor": round(ceiling_factor, 2),
        "ac": ac, "wa": wa, "ceiling": ceiling,
    }


def stars(mastery_pct):
    n = round(mastery_pct / 20)
    n = max(0, min(5, n))
    return "★" * n + "☆" * (5 - n)
