import os

# QUAN TRỌNG: KHÔNG hardcode API key trong source code.
# Set biến môi trường trước khi chạy:
#   export GROQ_API_KEY="gsk_..."
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Nơi lưu dữ liệu lâu dài của từng handle (profile/history/roadmap/mistakes/flashcards...)
DATA_DIR = os.environ.get(
    "CF_COACH_DATA_DIR",
    os.path.join(os.path.expanduser("~"), ".cf_coach"),
)
