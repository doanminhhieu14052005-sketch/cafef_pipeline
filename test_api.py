import requests
from bs4 import BeautifulSoup
import time

def deep_scrape_cafef():
    print("🚀 KHỞI ĐỘNG CỖ MÁY CÀO DỮ LIỆU SÂU (DEEP SCRAPER) 🚀\n")
    
    # Cào thử từ trang 1 đến trang 5
    for page in range(1, 3):
        # Lắp số trang vào đường link bạn vừa tìm được
        api_url = f"https://cafef.vn/timelinelist/18833/{page}.chn"
        print(f"Đang đào dữ liệu Trang {page}...")
        
        # Thêm User-Agent để ngụy trang thành trình duyệt thật
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        resp = requests.get(api_url, headers=headers)
        
        if resp.status_code == 200:
            # --- BƯỚC TEST: In thử 500 ký tự đầu tiên của API ra xem nó là cái gì ---
            # print("Dữ liệu thô:", resp.text[:500]) 
            # (Bạn có thể bỏ dấu # ở trên để xem tận mắt mã HTML nó trả về nhé)
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # --- SỬA Ở ĐÂY: Dùng lại "Radar" chuẩn của luồng tin chính ---
            articles = soup.select("div.tlitem, div.item-news")
            
            print(f"  -> Nhặt được {len(articles)} bài báo.\n")
            
            if articles:
                # Tìm thẻ a theo chuẩn Module 1
                
                first_a_tag = articles[0].select_one("h3 a, h2 a, .title a, a")
                if first_a_tag:
                    title = first_a_tag.get("title") or first_a_tag.get_text(strip=True)
                    print(f"  -> Báo cáo trang {page}: {title}\n")
        
        # Ngủ 1 giây để tránh bị CafeF block IP
        time.sleep(1)

if __name__ == "__main__":
    deep_scrape_cafef()