import logging
from collections import Counter
from module1_fetcher import init_db, fetch_new_urls
from config import SCRAPE_DEPTH

# 1. Thiết lập logging để thấy được quá trình tool đang chạy
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def test_run():
    print(f"--- KHỞI CHẠY KIỂM TRA MODULE 1 (Độ sâu: {SCRAPE_DEPTH} trang) ---")
    conn = init_db()
      
    try:
        # 3. Chạy hàm tổng tư lệnh để cào link
        print("\nĐang quét các danh mục CafeF... Vui lòng đợi...")
        new_articles = fetch_new_urls(conn)
        
        # ==========================================
        # PHẦN MỚI 1: BẢNG THỐNG KÊ TỔNG QUAN
        # ==========================================
        print(f"\n✅ Kết quả: Tìm thấy tổng cộng {len(new_articles)} bài báo mới.")
        
        if new_articles:
            # Dùng Counter để đếm tự động số bài của từng category
            category_counts = Counter(art.get('category', 'Không rõ') for art in new_articles)
            
            print("\n📊 THỐNG KÊ THEO CHUYÊN MỤC:")
            for cat, count in category_counts.items():
                print(f"  🔹 Mục [{cat.upper()}]: {count} bài")
            print("=" * 40)
        
        # ==========================================
        # PHẦN MỚI 2: IN CHI TIẾT KÈM PHÂN LOẠI
        # ==========================================
        for i, art in enumerate(new_articles, 1):
            # Lấy tên chuyên mục, viết hoa lên cho nổi bật (VD: VI_MO)
            cat_name = art.get('category', 'KHÔNG RÕ').upper()
            
            print(f"{i}. [{cat_name}] Title: {art['title']}")
            print(f"   URL: {art['url']}")
            print(f"   Time: {art['published_at']}")
            print(f"   Bốc từ: {art.get('source_box', 'Không rõ')}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Lỗi khi chạy thử: {e}")
    finally:
        # 5. Đóng kết nối
        conn.close()
        print("\n--- KẾT THÚC KIỂM TRA ---")

if __name__ == "__main__":
    test_run()