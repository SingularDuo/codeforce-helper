"""
Module dùng CHUNG cho mọi feature khi cần gọi LLM (Groq API).
Không feature nào được tự gọi requests tới Groq trực tiếp -> tránh duplicate logic.
"""
import requests
from .config import GROQ_API_KEY, GROQ_MODEL


class GroqClientError(Exception):
    pass


def call_groq(system_prompt: str, user_prompt: str, temperature: float = 0.4, model: str = None) -> str:
    if not GROQ_API_KEY:
        raise GroqClientError(
            "Chưa cấu hình GROQ_API_KEY. Hãy export biến môi trường GROQ_API_KEY trước khi chạy "
            "(vd: export GROQ_API_KEY=gsk_xxx)."
        )
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model or GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        data = resp.json()
    except Exception as e:
        raise GroqClientError(f"Lỗi kết nối Groq API: {e}")

    if resp.status_code != 200:
        raise GroqClientError(data.get("error", {}).get("message", f"HTTP {resp.status_code}"))
    return data["choices"][0]["message"]["content"]
