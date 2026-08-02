"""
User Profile Builder DÙNG CHUNG. Mọi feature muốn biết "người dùng này là ai, mạnh/yếu gì,
đang theo roadmap nào, gần đây luyện gì" đều gọi build_profile() ở đây, không tự tính lại.
"""
from datetime import datetime, timezone

from . import cf_client, storage


def build_profile(handle):
    user_info = cf_client.get_user_info(handle)
    contests = cf_client.get_user_rating(handle)
    submissions = cf_client.get_user_status(handle)

    now_ts = datetime.now(timezone.utc).timestamp()
    days_since_last_contest = None
    if contests:
        days_since_last_contest = int((now_ts - contests[-1]["ratingUpdateTimeSeconds"]) / 86400)

    solved = set()
    tag_ac, tag_wa = {}, {}
    tag_ac_ratings = {}
    rating_buckets = {"800-1500": 0, "1600-1900": 0, "2000-2200": 0, "2300-2500": 0, "2600+": 0}
    ratings_list = []
    ac_180 = 0
    limit_180 = now_ts - 180 * 86400

    for s in submissions:
        prob = s.get("problem", {})
        cid, idx = prob.get("contestId"), prob.get("index")
        if not cid or not idx:
            continue
        pid = f"{cid}{idx}"
        t = s.get("creationTimeSeconds", 0)
        verdict = s.get("verdict")
        tags = prob.get("tags", [])
        r = prob.get("rating")

        if verdict == "OK":
            if pid not in solved:
                solved.add(pid)
                if t >= limit_180:
                    ac_180 += 1
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
                for tg in tags:
                    tag_ac[tg] = tag_ac.get(tg, 0) + 1
                    if r:
                        tag_ac_ratings.setdefault(tg, []).append(r)
        else:
            for tg in tags:
                tag_wa[tg] = tag_wa.get(tg, 0) + 1

    tag_penalty = []
    for tg, ac in tag_ac.items():
        wa = tag_wa.get(tg, 0)
        score = round(wa / max(ac, 1), 3)
        ceiling = max(tag_ac_ratings.get(tg, [0]))
        tag_penalty.append({"tag": tg, "ac": ac, "wa": wa, "score": score, "ceiling": ceiling})
    tag_penalty.sort(key=lambda x: x["score"], reverse=True)

    strong = sorted(
        [t for t in tag_penalty if t["ac"] >= 5],
        key=lambda x: (-x["ac"], x["score"]),
    )[:5]
    weak = sorted(
        [t for t in tag_penalty if (t["ac"] + t["wa"]) >= 3],
        key=lambda x: -x["score"],
    )[:5]

    ratings_list.sort()
    median_rating = ratings_list[len(ratings_list) // 2] if ratings_list else user_info.get("rating", 1200)

    hist = storage.load(handle)

    return {
        "handle": handle,
        "rank": user_info.get("rank", "unrated").title(),
        "rating": user_info.get("rating", 1200),
        "max_rating": user_info.get("maxRating", user_info.get("rating", 1200)),
        "solved_ids": solved,
        "tag_ac": tag_ac,
        "tag_wa": tag_wa,
        "tag_penalty": tag_penalty,
        "strong_topics": strong,
        "weak_topics": weak,
        "rating_distribution": rating_buckets,
        "median_rating": median_rating,
        "ac_180_days": ac_180,
        "days_since_last_contest": days_since_last_contest,
        "roadmap": hist.get("roadmap"),
        "recent_recommended_ids": set(storage.recent_recommended_ids(handle, 40)),
        "recent_recommended_tags": storage.recent_recommended_tags(handle),
        "mistakes": hist.get("mistakes", []),
        "topic_progress": hist.get("topic_progress", {}),
        "training_sessions": hist.get("training_sessions", []),
        "flashcards": hist.get("flashcards", []),
    }
