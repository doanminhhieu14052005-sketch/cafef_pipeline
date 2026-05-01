"""
Module 1: URL Fetcher & Deduplication
- Crawl danh mục CafeF, lấy [title, url, published_at]
- Dedup bằng MongoDB url_hash (SHA256)
- Trả về queue các URL chưa xử lý
"""

import hashlib
import random
import time
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import (
    CAFEF_CATEGORIES,
    REQUEST_DELAY, REQUEST_HEADERS, SCRAPE_DEPTH
)
from module4_storage import get_collection

logger = logging.getLogger(__name__)


# ── Database helpers (MongoDB) ──────────────────────────────────

def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def is_seen(url_hash: str) -> bool:
    col = get_collection()
    return col.find_one({"url_hash": url_hash}, {"_id": 1}) is not None


def mark_seen(item: dict) -> None:
    """Insert URL mới với status=pending. Bỏ qua nếu đã tồn tại."""
    col = get_collection()
    col.update_one(
        {"url_hash": item["url_hash"]},
        {"$setOnInsert": {
            "url_hash":     item["url_hash"],
            "source_url":   item["url"],
            "title":        item.get("title", ""),
            "published_at": item.get("published_at", ""),
            "category":     item.get("category", ""),
            "raw_text":     "",
            "summary_json": None,
            "status":       "pending",
            "retry_count":  0,
            "scrape_method": "",
            "created_at":   datetime.now(timezone.utc),
        }},
        upsert=True,
    )


def get_pending_urls(limit: int = 20) -> list[dict]:
    col = get_collection()
    cursor = col.find(
        {"status": "pending", "retry_count": {"$lt": 3}},
        {"url_hash": 1, "source_url": 1, "title": 1,
         "published_at": 1, "category": 1, "_id": 0}
    ).sort("created_at", -1).limit(limit)

    return [
        {"url_hash": doc["url_hash"], "url": doc["source_url"],
         "title": doc.get("title", ""), "published_at": doc.get("published_at", ""),
         "category": doc.get("category", "")}
        for doc in cursor
    ]


def update_status(url_hash: str, status: str) -> None:
    """Cập nhật status. Nếu failed thì tăng retry_count."""
    col = get_collection()
    update: dict = {"$set": {"status": status}}
    if status == "failed":
        update["$inc"] = {"retry_count": 1}
    col.update_one({"url_hash": url_hash}, update)


# ── Fetcher ──────────────────────────────────────────────────────

def _safe_get(url: str) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None


def _parse_article_list(html: str, category: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    for item in soup.select("div.tlitem, div.item-news, div.tinmoi li, div.firstitem, div.big"):
        
        # --- Theo dõi nguồn gốc ---
        tag_name = item.name
        tag_classes = item.get("class")
        
        if tag_classes:
            source_info = f"{tag_name} class: {' '.join(tag_classes)}"
        else:
            source_info = f"{tag_name} (nằm trong tinmoi)"
        # ----------------------------------------

        a_tag = item.select_one("h3 a, h2 a, .title a")
        if not a_tag:
            a_tag = item.select_one("a")

        if not a_tag:
            continue

        url = a_tag.get("href", "")
        if not url.startswith("http"):
            url = "https://cafef.vn" + url

        title = a_tag.get_text(strip=True)
        time_tag = item.select_one("span.time, span.date, time, p.time")
        published_at = time_tag.get_text(strip=True) if time_tag else ""

        articles.append({
            "url": url,
            "title": title,
            "published_at": published_at,
            "category": category,
            "url_hash": hash_url(url),
            "source_box": source_info
        })

    return articles


def fetch_new_urls(depth: int = SCRAPE_DEPTH) -> list[dict]:
    new_items = []

    for cat_name, info in CAFEF_CATEGORIES.items():
        logger.info(f"--- Đang quét danh mục: {cat_name.upper()} ---")
        
        for page in range(1, depth + 1):
            if page == 1:
                target_url = info["url"]
            else:
                target_url = f"https://cafef.vn/timelinelist/{info['api_id']}/{page}.chn"
            
            logger.info(f"Đang quét Trang {page}: {target_url}")
            resp = _safe_get(target_url)
            if not resp:
                continue

            articles = _parse_article_list(resp.text, cat_name)

            for article in articles:
                if not is_seen(article["url_hash"]):
                    mark_seen(article)
                    new_items.append(article)
                    logger.debug(f"New [{article['source_box']}]: {article['title'][:50]}")

            time.sleep(random.uniform(*REQUEST_DELAY))

    logger.info(f"Tổng kết: Tìm thấy {len(new_items)} link mới sau khi quét {depth} trang.")
    return new_items