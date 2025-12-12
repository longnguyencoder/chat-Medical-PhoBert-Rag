# 📊 PhoBERT Medical Chatbot Evaluation

Hệ thống đánh giá mô hình Medical Chatbot sử dụng PhoBERT RAG.

## 📁 Cấu Trúc Thư Mục

```
evaluation/
├── evaluate_model.py                          # Script Python chạy local
├── phobert_medical_chatbot_evaluation.ipynb  # Jupyter Notebook (cho Colab)
├── README.md                                  # File này
└── test_data/
    └── sample_test_questions.csv             # Sample test data
```

## 🚀 Cách Sử Dụng (Local - Windows)

### **Bước 1: Cài Đặt Dependencies**

```bash
# Đảm bảo đã activate virtual environment
cd d:\ChatbotMedical_server\ChatbotMedical_server

# Cài đặt thêm packages cho evaluation (nếu chưa có)
pip install tqdm pandas numpy
```

### **Bước 2: Chuẩn Bị Test Data**

Tạo file CSV với format:

```csv
question,expected_answer,relevant_doc_ids,category
"Sốt xuất huyết có triệu chứng gì?","Sốt cao, đau đầu...","doc_123,doc_456","symptoms"
```

Hoặc dùng sample data có sẵn: `test_data/sample_test_questions.csv`

### **Bước 3: Chạy Evaluation**

```bash
# Chạy với sample data
python evaluation/evaluate_model.py --test_file evaluation/test_data/sample_test_questions.csv

# Chạy với file tùy chỉnh
python evaluation/evaluate_model.py --test_file path/to/your/test.csv --output results.csv

# Chạy với K values khác
python evaluation/evaluate_model.py --test_file test.csv --k_values 1 3 5 10
```

### **Bước 4: Xem Kết Quả**

Kết quả sẽ hiển thị trên console:

```
============================================================
📊 EVALUATION RESULTS
============================================================

🔍 RETRIEVAL METRICS:
   Precision@1: 0.8000
   Precision@3: 0.7333
   Recall@3: 0.9000
   MRR: 0.8500

💬 RESPONSE QUALITY METRICS:
   Semantic Similarity: 0.7823
   Entity Accuracy: 0.8500

⚡ PERFORMANCE METRICS:
   Avg Response Time: 2.34s

🎯 INTERPRETATION:
   ✅ Retrieval: GOOD (Precision@3 ≥ 0.7)
   ✅ Response Quality: GOOD (Semantic Similarity ≥ 0.7)
   ✅ Medical Accuracy: GOOD (Entity Accuracy ≥ 0.8)

📈 OVERALL SCORE: 3/3
   🎉 Model is GOOD - Ready for production!
============================================================
```

Files được tạo:
- `evaluation_results.csv`: Kết quả chi tiết từng câu hỏi
- `evaluation_results_summary.json`: Metrics tổng hợp

---

## 📊 Metrics Giải Thích

### **Retrieval Metrics** (Đánh giá khả năng tìm kiếm)

| Metric | Ý Nghĩa | Tốt |
|--------|---------|-----|
| **Precision@K** | Tỷ lệ tài liệu đúng trong top K | ≥ 0.7 |
| **Recall@K** | Tỷ lệ tìm được tài liệu đúng | ≥ 0.8 |
| **MRR** | Vị trí của kết quả đúng đầu tiên | ≥ 0.8 |
| **NDCG@K** | Chất lượng ranking tổng thể | ≥ 0.8 |

### **Response Quality Metrics** (Chất lượng câu trả lời)

| Metric | Ý Nghĩa | Tốt |
|--------|---------|-----|
| **Semantic Similarity** | Độ giống về ý nghĩa (PhoBERT) | ≥ 0.7 |
| **Entity Accuracy** | Tỷ lệ thuật ngữ y tế đúng | ≥ 0.8 |

### **Performance Metrics**

| Metric | Ý Nghĩa | Tốt |
|--------|---------|-----|
| **Response Time** | Thời gian phản hồi | < 3s |

---

## 🎯 Đánh Giá Mô Hình

### ✅ **Mô Hình TỐT** (Score ≥ 2/3)

Đạt ít nhất 2 trong 3 tiêu chí:
- ✅ Precision@3 ≥ 0.7
- ✅ Semantic Similarity ≥ 0.7
- ✅ Entity Accuracy ≥ 0.8

→ **Có thể deploy production!**

### ⚠️ **Mô Hình TRUNG BÌNH** (Score = 1/3)

Chỉ đạt 1 tiêu chí → **Cần cải thiện**

**Nếu Retrieval kém:**
- Fine-tune PhoBERT
- Tăng BM25 weight
- Thêm query expansion

**Nếu Response Quality kém:**
- Cải thiện prompt GPT
- Tăng số context documents
- Giảm temperature

### ❌ **Mô Hình YẾU** (Score = 0/3)

Không đạt tiêu chí nào → **Cần cải thiện lớn**

---

## 🔧 Tùy Chỉnh

### **1. Thay Đổi K Values**

```bash
python evaluation/evaluate_model.py --test_file test.csv --k_values 1 3 5 10
```

### **2. Chỉ Test Retrieval (Không Cần OpenAI API)**

Mở file `evaluate_model.py`, comment dòng generation:

```python
# Line ~120
try:
    generated_answer = generate_natural_response(...)
except:
    generated_answer = "[Generation skipped]"  # ← Sẽ skip generation
```

### **3. Thêm Medical Keywords**

Mở file `evaluate_model.py`, sửa hàm `extract_medical_entities`:

```python
medical_keywords = [
    'sốt', 'đau', 'viêm', 'nhiễm', 'bệnh', 'thuốc',
    # Thêm keywords của bạn
    'tiểu đường', 'huyết áp', 'cholesterol'
]
```

---

## ❓ FAQ

### **Q: Script báo lỗi "No module named 'tqdm'"?**
**A:** Cài đặt: `pip install tqdm pandas numpy`

### **Q: Script chạy lâu quá?**
**A:** 
- Giảm số test questions
- Comment generation (chỉ test retrieval)
- Sử dụng GPU nếu có

### **Q: Không có OpenAI API key?**
**A:** Script vẫn chạy được, chỉ skip phần generation. Metrics retrieval vẫn tính được.

### **Q: Làm sao lấy `relevant_doc_ids`?**
**A:**
1. Chạy retrieval cho câu hỏi
2. Xem top 5 results
3. Chọn doc IDs đúng
4. Ghi vào CSV

### **Q: Kết quả khác với Colab?**
**A:** Có thể do:
- Phiên bản thư viện khác nhau
- CPU vs GPU (embeddings có thể khác nhau chút)
- Random seed trong GPT

---

## 📞 Hỗ Trợ

Nếu gặp lỗi, kiểm tra:

1. ✅ Virtual environment đã activate
2. ✅ ChromaDB có dữ liệu (`collection.count() > 0`)
3. ✅ Test file format đúng (CSV/JSON)
4. ✅ `.env` có `OPENAI_API_KEY` (nếu test generation)

---

**Good luck! 🚀**
