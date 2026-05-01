import json
import os
import logging
from module3_summarizer import summarize_single

# Thiết lập logging cơ bản để xem quá trình AI chạy
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_with_real_data():
    print("=== KIỂM TRA MODULE 3 VỚI DỮ LIỆU TỪ MODULE 2 ===\n")
    
    input_path = "data/test_raw_articles.jsonl"
    
    # 1. Kiểm tra file đầu vào
    if not os.path.exists(input_path):
        print(f"❌ Lỗi: Không tìm thấy file {input_path}")
        print("Vui lòng chạy Module 2 trước để tạo dữ liệu cào.")
        return

    # 2. Đọc dữ liệu (Lấy thử 2 bài đầu tiên để test)
    articles = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 2: break  # Giới hạn 2 bài để tránh tốn thời gian/VRAM ban đầu
                articles.append(json.loads(line))
    except Exception as e:
        print(f"❌ Lỗi khi đọc file JSONL: {e}")
        return

    print(f"📂 Đã đọc thành công {len(articles)} bài báo từ file dữ liệu.")
    print("🚀 Bắt đầu gọi Ollama để phân tích...\n")

    # 3. Chạy Module 3
    for idx, article in enumerate(articles, 1):
        print(f"--- Đang xử lý bài {idx}: {article.get('url')} ---")
        
        # Gọi hàm xử lý từ file module3_summarizer.py của Hiếu
        processed_article = summarize_single(article)
        
        # 4. Hiển thị kết quả bóc tách
        if processed_article["ai_status"] == "done":
            print("✅ Kết quả bóc tách JSON:")
            print(json.dumps(processed_article["summary_json"], indent=4, ensure_ascii=False))
        else:
            print("⚠️ AI thất bại trong việc xử lý bài này.")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    test_with_real_data()