"""
Module 3: AI Summarizer & Extractor
- Gọi LLM (Ollama local hoặc Gemini) với structured prompt
- Validate output bằng Pydantic
- Retry tối đa 3 lần nếu JSON lỗi
"""

import gc
import json
import logging
import re
import time
from typing import Literal, Optional

import httpx
from pydantic import BaseModel, ValidationError, field_validator

from config import (
    LLM_BACKEND, LLM_MAX_RETRIES,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    GEMINI_API_KEY,
    MAX_INPUT_CHARS_OLLAMA, MAX_INPUT_CHARS_GEMINI,
    VRAM_COOLDOWN_SECONDS, ENABLE_GC_CLEANUP,
)

logger = logging.getLogger(__name__)


# ── Pydantic Schema ───────────────────────────────────────────────

class ArticleSummary(BaseModel):
    summary: list[str]          # 3 gạch đầu dòng
    tickers: list[str]          # ["FPT", "HPG"] hoặc []
    impact: Literal["Positive", "Negative", "Neutral"]
    key_metrics: dict[str, str] # {"Doanh thu": "1000 tỷ"} hoặc {}
    sector: Optional[str] = None  # "Ngân hàng", "Bất động sản"...

    @field_validator("tickers")
    @classmethod
    def uppercase_tickers(cls, v):
        return [t.upper().strip() for t in v if t.strip()]

    @field_validator("summary", mode="before")
    @classmethod
    def process_summary(cls, v):
        if isinstance(v, str):
            v = [v]
        if isinstance(v, list):
            v = [str(x).strip() for x in v if str(x).strip()]
            if not v:
                return ["Không có thông tin tóm tắt."]
            return v[:5] # Lấy tối đa 5 điểm nếu AI lỡ viết quá dài
        return v


# ── Prompt ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài chính Việt Nam.
Nhiệm vụ: Đọc bài báo tài chính và trả về JSON THUẦN TÚY (không có markdown, không có ```).

Schema bắt buộc:
{
  "summary": ["điểm 1", "điểm 2", "điểm 3"],
  "tickers": ["MÃ1", "MÃ2"],
  "impact": "Positive" | "Negative" | "Neutral",
  "key_metrics": {"Chỉ số": "Giá trị"},
  "sector": "Tên ngành hoặc null"
}

Quy tắc:
- summary: 2–3 gạch đầu dòng, mỗi điểm dưới 25 từ
- tickers: HỈ chứa các mã chứng khoán HOSE/HNX (viết hoa). NẾU BÀI BÁO KHÔNG ĐỀ CẬP ĐẾN MÃ CHỨNG KHOÁN NÀO, BẮT BUỘC TRẢ VỀ: "tickers": []. TUYỆT ĐỐI KHÔNG trả về null.
- impact: đánh giá tác động đến thị trường/doanh nghiệp
- key_metrics: chỉ trích xuất nếu bài có số liệu cụ thể
- sector: Tên ngành liên quan. Nếu bài báo nói về vĩ mô chung chung, trả về: "sector": null.
- KHÔNG giải thích thêm, chỉ JSON"""

USER_TEMPLATE = """Bài báo:
---
{text}
---
JSON:"""


# ── LLM Backends ─────────────────────────────────────────────────

def _call_ollama(text: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(text=text[:MAX_INPUT_CHARS_OLLAMA])},
        ],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    with httpx.Client(timeout=120) as client:
        resp = client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


def _call_gemini(text: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": (
            SYSTEM_PROMPT + "\n\n" +
            USER_TEMPLATE.format(text=text[:MAX_INPUT_CHARS_GEMINI])
        )}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _extract_json(raw: str) -> str:
    """
    Trích xuất JSON object đầu tiên từ output LLM.
    Dùng brace-counting thay vì greedy regex để tránh bắt nhầm
    ký tự } trong text thừa phía sau JSON.
    """
    # Bước 1: Xóa markdown fences (cả mở và đóng)
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    # Bước 2: Tìm JSON object bằng đếm ngoặc {}
    start = raw.find("{")
    if start == -1:
        return raw  # Không tìm thấy { → trả nguyên

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(raw)):
        ch = raw[i]

        if escape_next:
            escape_next = False
            continue

        if ch == "\\":
            if in_string:
                escape_next = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start:i + 1]

    # Fallback: không tìm thấy cặp {} hoàn chỉnh → trả nguyên
    return raw


# ── Main ─────────────────────────────────────────────────────────

def summarize(raw_text: str) -> Optional[ArticleSummary]:
    """
    Gọi LLM, parse + validate JSON.
    Retry tối đa LLM_MAX_RETRIES lần.
    """
    call_fn = _call_ollama if LLM_BACKEND == "ollama" else _call_gemini

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            raw = call_fn(raw_text)
            json_str = _extract_json(raw)
            data = json.loads(json_str)
            result = ArticleSummary.model_validate(data)
            logger.info(f"Summarized OK (attempt {attempt})")
            return result

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Parse error attempt {attempt}: {e}")
        except httpx.HTTPError as e:
            error_msg = str(e).lower()
            logger.error(f"LLM HTTP error attempt {attempt}: {e}")
            
            # Xử lý 429 Rate Limit
            if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
                logger.warning("⚠️ Bị giới hạn tốc độ API (429). Đang nghỉ 15s...")
                time.sleep(15)
                continue

            # Phát hiện OOM → chờ VRAM giải phóng rồi retry
            if "out of memory" in error_msg or "oom" in error_msg:
                logger.warning(
                    f"⚠️ VRAM OOM detected! Waiting {VRAM_COOLDOWN_SECONDS}s..."
                )
                time.sleep(VRAM_COOLDOWN_SECONDS)
                gc.collect()

    logger.error("Summarizer failed after max retries")
    return None


def _cleanup_memory():
    """Dọn dẹp memory sau mỗi lần summarize."""
    if ENABLE_GC_CLEANUP:
        gc.collect()
        # Nếu có torch (dùng GPU trực tiếp), xóa cache CUDA
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass  # Không có torch → bỏ qua (Ollama tự quản lý VRAM)


def summarize_single(article: dict) -> dict:
    """
    Summarize 1 bài + cleanup VRAM sau khi xong.
    Dùng cho streaming pipeline (scrape → summarize → save từng bài).
    """
    summary = summarize(article["raw_text"])
    if summary:
        article["summary_json"] = summary.model_dump()
        article["status"] = "done"
    else:
        article["summary_json"] = None
        article["status"] = "failed"

    _cleanup_memory()
    return article


def summarize_batch(articles: list[dict]) -> list[dict]:
    """Thêm summary_json vào mỗi article dict (batch mode, backward compat)."""
    results = []
    for article in articles:
        article = summarize_single(article)
        results.append(article)
    return results