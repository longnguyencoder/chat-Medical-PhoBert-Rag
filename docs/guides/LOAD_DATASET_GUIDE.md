# Load HuggingFace Medical Dataset - Quick Guide

## 📦 Install Dependencies

```bash
pip install datasets
```

## 🚀 Usage

### **Option 1: Command Line (Recommended)**

```bash
# Basic usage
python load_huggingface_dataset.py --dataset "username/medical-qa-vietnamese"

# With custom column names
python load_huggingface_dataset.py \
  --dataset "username/medical-qa" \
  --question-col "câu_hỏi" \
  --answer-col "câu_trả_lời" \
  --split "train"

# Save to CSV first (to review)
python load_huggingface_dataset.py \
  --dataset "username/medical-qa" \
  --save-csv "data/review_before_index.csv"
```

### **Option 2: Python Script**

```python
from datasets import load_dataset
from load_huggingface_dataset import (
    load_hf_dataset,
    convert_qa_to_medical_format,
    index_to_chromadb,
    rebuild_bm25_index
)

# Load dataset
df = load_hf_dataset("username/medical-qa-vietnamese")

# Convert to medical format
medical_df = convert_qa_to_medical_format(
    df,
    question_col='question',
    answer_col='answer'
)

# Review first
print(medical_df.head())

# Index to ChromaDB
index_to_chromadb(medical_df)

# Rebuild BM25
rebuild_bm25_index()
```

## 📋 Common HuggingFace Medical Datasets

### **Vietnamese:**
- `nguyenvulebinh/vi_med_qa` - Vietnamese medical Q&A
- `5CD-AI/Viet-Doctor-Instruct` - Vietnamese medical instructions
- `vilm/vimqa` - Vietnamese medical Q&A

### **English (can translate):**
- `medalpaca/medical_meadow_medical_flashcards`
- `lavita/ChatDoctor-HealthCareMagic-100k`

## 🔍 Check Dataset Format

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("username/dataset-name", split='train')

# Check columns
print(dataset.column_names)
# Output: ['question', 'answer', 'context']

# Check first example
print(dataset[0])
```

## ⚙️ Customize Conversion

If your dataset has special format, edit `convert_qa_to_medical_format()`:

```python
def convert_qa_to_medical_format(df: pd.DataFrame):
    medical_data = []
    
    for idx, row in df.iterrows():
        # YOUR CUSTOM LOGIC HERE
        
        medical_doc = {
            'disease_name': extract_disease(row['question']),
            'description': row['answer'],
            'symptoms': extract_symptoms(row['answer']),
            'treatment': extract_treatment(row['answer']),
            # ...
        }
        
        medical_data.append(medical_doc)
    
    return pd.DataFrame(medical_data)
```

## ✅ Verification

After loading:

```bash
# Check collection size
python -c "
from src.services.medical_chatbot_service import get_or_create_collection
collection = get_or_create_collection()
print(f'Total documents: {collection.count()}')
"

# Test search
# Go to http://127.0.0.1:5000/api/docs
# Try /chat-secure with a question
```

## 📊 Expected Results

| Step | Time | Result |
|------|------|--------|
| Load dataset | 10-30s | ✓ DataFrame loaded |
| Convert format | 5-10s | ✓ Medical format |
| Index to ChromaDB | 1-5min | ✓ Embeddings created |
| Rebuild BM25 | 5-10s | ✓ BM25 index updated |

---

## 🎯 Next Steps

1. **Load your dataset:**
   ```bash
   python load_huggingface_dataset.py --dataset "YOUR_DATASET_NAME"
   ```

2. **Restart server:**
   ```bash
   python main.py
   ```

3. **Test:**
   - Go to Swagger UI
   - Try some questions
   - Check if answers improved!

---

**Bạn cho tôi biết tên dataset HuggingFace của bạn để tôi tạo command chính xác nhé!** 😊
