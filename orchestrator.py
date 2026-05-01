"""
Orchestrator: Điều phối toàn bộ pipeline
- Module 1 → 2 → 3 → 4 chạy theo chuỗi
- Tự động chạy theo khung giờ cài đặt sẵn
- Logging tập trung
"""

import logging
import schedule
import time
from datetime import datetime

from config import BATCH_SIZE, SCHEDULE_TIMES
from module1_fetcher import fetch_new_urls, get_pending_urls
from module2_scraper import process_pending_articles

# ── Logging setup ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("orchestrator")


def run_pipeline() -> None:
    logger.info("=" * 50)
    logger.info(f"Pipeline started at {datetime.now()}")

    # Module 1: Fetch & dedup
    new_urls = fetch_new_urls()
    logger.info(f"M1: {len(new_urls)} new URLs queued")

    # Lấy pending từ DB (bao gồm cả lần trước còn sót)
    pending = get_pending_urls(limit=BATCH_SIZE)
    if not pending:
        logger.info("No pending URLs to process, exiting")
        return

    # Streaming pipeline: scrape → summarize → save TỪNG BÀI
    # (mỗi bài xong là lưu DB ngay, không chờ cả batch)
    process_pending_articles(pending)

    logger.info("Pipeline completed")


if __name__ == "__main__":
    import os
    # Chạy ngay lần đầu khi khởi động
    run_pipeline()

    # Nếu chạy trên GitHub Actions thì dừng luôn ở đây, không vào vòng lặp
    if os.getenv("GITHUB_ACTIONS") == "true":
        logger.info("Chạy trên GitHub Actions: Đã hoàn tất 1 chu kỳ, tự động thoát.")
        exit(0)

    # Schedule theo khung giờ cố định
    for t in SCHEDULE_TIMES:
        schedule.every().day.at(t).do(run_pipeline)

    logger.info(f"Scheduler started — pipeline sẽ chạy lúc: {', '.join(SCHEDULE_TIMES)}")
    logger.info("Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)

