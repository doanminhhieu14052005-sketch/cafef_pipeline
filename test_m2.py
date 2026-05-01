import sqlite3
import json
import os
from tqdm import tqdm # Nhớ chạy: pip install tqdm

# Import các hàm từ file của Hiếu (sửa lại tên file import nếu cần)
from module1_fetcher import get_pending_articles, mark_article_done
from module2_scraper import scrape_article 

def run_module2_test():
    print("--- KHỞI CHẠY KIỂM TRA MODULE 2 ---")
    
    # 1. Kết nối DB
    conn = sqlite3.connect("data/dedup.db")
     
    # 2. Lấy 5 bài pending để test thử
    test_limit = 20
    items_to_scrape = get_pending_articles(conn, limit=test_limit)
    
    if not items_to_scrape:
        print("Không có bài báo nào ở trạng thái 'pending' để cào!")
        return

    print(f"Đã lấy {len(items_to_scrape)} bài báo từ Database. Bắt đầu cào...")
    
    # Chuẩn bị file đầu ra
    output_file = "data/test_raw_articles.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    success_count = 0
    
    # Mở file để ghi nối tiếp (append)
    with open(output_file, 'a', encoding='utf-8') as f:
        # Vòng lặp băng chuyền
        for item in tqdm(items_to_scrape, desc="Tiến độ"):
            url = item["url"]
            url_hash = item["url_hash"]
            
            # Gọi Module 2 làm việc
            scraped_data = scrape_article(url)
            
            if scraped_data:
                # Trộn metadata (vỏ) và nội dung (ruột)
                full_article = {**item, **scraped_data}
                
                # Lưu file (mỗi bài báo là 1 dòng JSON)
                f.write(json.dumps(full_article, ensure_ascii=False) + "\n")
                
                # CHỐT SỔ: Đánh dấu đã cào xong trong DB
                mark_article_done(conn, url_hash)
                success_count += 1
            else:
                print(f"\n[LỖI] Không cào được nội dung từ: {url}")

    conn.close()
    print(f"\n✅ HOÀN THÀNH TEST: Thành công {success_count}/{len(items_to_scrape)} bài.")
    print(f"📁 Dữ liệu đã lưu tại: {output_file}")

if __name__ == "__main__":
    run_module2_test()