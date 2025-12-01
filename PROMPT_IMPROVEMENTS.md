# Cải tiến Prompt - Cấp độ 1 ✅

## Những thay đổi đã thực hiện:

### 1. **System Prompt chuyên nghiệp hơn**
- Định vị rõ ràng: "Bác sĩ AI với 10 năm kinh nghiệm"
- Quy tắc bắt buộc được liệt kê rõ ràng
- Hướng dẫn phong cách trả lời cụ thể

### 2. **Quy tắc an toàn y tế**
- KHÔNG chẩn đoán chắc chắn
- KHÔNG kê đơn thuốc cụ thể
- Khuyến cáo đi khám khi có dấu hiệu nguy hiểm:
  - Sốt cao > 39°C
  - Triệu chứng kéo dài > 3 ngày
  - Khó thở, đau ngực, co giật

### 3. **Phong cách trả lời**
- Bắt đầu bằng lời chào thân thiện
- Chia thành 2-3 đoạn ngắn
- Dùng bullet points (•) khi liệt kê
- Tránh thuật ngữ phức tạp

### 4. **Ví dụ mẫu (Few-shot)**
Thêm ví dụ trả lời chuẩn để GPT học cách:
- Câu hỏi thông thường
- Triệu chứng nguy hiểm
- Không có thông tin

### 5. **Cải thiện Context**
- Format rõ ràng hơn với [Nguồn 1], [Nguồn 2]
- Hiển thị độ liên quan của mỗi nguồn

## Kết quả mong đợi:

✅ Câu trả lời chuyên nghiệp hơn  
✅ An toàn hơn (không chẩn đoán lung tung)  
✅ Dễ đọc hơn (có cấu trúc rõ ràng)  
✅ Thân thiện hơn (giọng điệu bác sĩ tư vấn)  

## Cách test:

1. Restart server: `python main.py`
2. Gửi câu hỏi qua API
3. So sánh câu trả lời trước và sau

## Ví dụ câu trả lời mới:

**Trước:**
> "Cảm cúm có triệu chứng sốt, ho, đau đầu. Nên uống thuốc."

**Sau:**
> "Chào bạn, cảm cúm thường có các triệu chứng sau:
> 
> • Sốt nhẹ (37.5-38.5°C)
> • Chảy nước mũi, nghẹt mũi
> • Đau họng, ho khan
> 
> Bạn nên nghỉ ngơi đầy đủ, uống nhiều nước. Nếu sốt cao hoặc kéo dài quá 3 ngày, hãy đến gặp bác sĩ nhé."
