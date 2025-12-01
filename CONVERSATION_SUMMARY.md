# Conversation Summary - Giai đoạn 2 ✅

## Đã hoàn thành:

### **Automatic Conversation Summary**
Bot tự động tóm tắt cuộc trò chuyện sau mỗi 5 tin nhắn để duy trì ngữ cảnh dài hạn.

---

## Cách hoạt động:

### 1. **Trigger tự động**
Mỗi khi bot trả lời, hệ thống kiểm tra số lượng tin nhắn:
```python
if message_count % 5 == 0:
    summary = generate_conversation_summary(conversation_id)
    conversation.summary = summary
    db.session.commit()
```

### 2. **Tạo Summary với GPT**
GPT đọc toàn bộ hội thoại và tạo tóm tắt ngắn gọn:
```
• Triệu chứng: Sốt 38°C, đau đầu, ho khan
• Đã dùng: Paracetamol 3 ngày
• Tình trạng: Chưa đỡ
• Khuyến cáo: Cần đi khám nếu không cải thiện
```

### 3. **Sử dụng trong Prompt**
Summary được thêm vào prompt của lần chat tiếp theo:
```
【Tóm tắt cuộc trò chuyện trước đó】
• Triệu chứng: Sốt 38°C...
• Đã dùng: Paracetamol...

【Lịch sử hội thoại gần đây】
User: "Vậy tôi nên đi khám ở đâu?"
Bot: "Bạn có thể đến bệnh viện..."
```

---

## Lợi ích:

✅ **Nhớ ngữ cảnh dài hạn** (20-30+ messages)  
✅ **Tiết kiệm token** (không cần load toàn bộ lịch sử cũ)  
✅ **Hiệu quả** (chỉ tóm tắt lại sau mỗi 5 tin nhắn)

---

## Cần thực hiện:

Do đã thay đổi cấu trúc database (thêm cột `summary`), bạn cần chạy script migration:

```bash
python add_summary_column.py
```

Sau đó restart server:
```bash
python main.py
```

---

## Test:

1. Chat liên tục 6-7 câu.
2. Kiểm tra log server, bạn sẽ thấy:
   `✓ Generated summary for conversation X`
   `✓ Updated conversation summary`
3. Ở câu thứ 6, bot vẫn nhớ thông tin từ câu 1 nhờ summary!
