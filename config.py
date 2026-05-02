import os
from dotenv import load_dotenv

load_dotenv()

# === CafeF ===
CAFEF_CATEGORIES = {
    "vi_mo": {
        "url": "https://cafef.vn/vi-mo-dau-tu.chn",
        "api_id": "18833"
    },
    "doanh_nghiep": {
        "url": "https://cafef.vn/doanh-nghiep.chn",
        "api_id": "18831"
    }
}

# Thêm biến cấu hình độ sâu mặc định
SCRAPE_DEPTH = 3  # Ví dụ: Mặc định mỗi lần sẽ cào 3 trang bài báo cũ

REQUEST_DELAY = (1.5, 3.0)  # seconds, random uniform
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

# === MongoDB ===
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = "cafef_news"
MONGO_COLLECTION = "articles"

# === LLM ===
LLM_BACKEND = os.getenv("LLM_BACKEND", "groq")  # "ollama" | "gemini" | "groq"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
LLM_MAX_RETRIES = 3

# === Pipeline ===
# Các khung giờ pipeline tự động chạy (format "HH:MM")
SCHEDULE_TIMES = ["07:00", "12:00", "18:00"]
BATCH_SIZE = 100  # Số bài xử lý AI mỗi lần chạy

# === VRAM Protection ===
MAX_INPUT_CHARS_OLLAMA = 3000   # Giới hạn chars gửi vào Ollama (tránh tràn VRAM)
MAX_INPUT_CHARS_GEMINI = 12000   # Tăng nhẹ cho Gemini
MAX_INPUT_CHARS_GROQ = 15000     # Groq thường có context window tốt
VRAM_COOLDOWN_SECONDS = 30      # Thời gian chờ nếu gặp OOM error
ENABLE_GC_CLEANUP = True        # Chạy gc.collect() sau mỗi bài summarize