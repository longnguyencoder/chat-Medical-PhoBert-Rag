import chromadb
from chromadb.utils import embedding_functions
import os
import json

def read_chroma_data():
    # Khởi tạo ChromaDB client
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    chroma_client = chromadb.PersistentClient(path=os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db'))

    # Sử dụng sentence-transformers làm embedding function
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    # Lấy collection
    collection = chroma_client.get_collection(
        name="diadiem_collection",
        embedding_function=sentence_transformer_ef
    )

    # Lấy tất cả dữ liệu
    results = collection.get()

    # In thông tin tổng quan
    print(f"Tổng số địa điểm: {len(results['ids'])}")
    print("\nDanh sách các địa điểm:")
    print("-" * 50)

    # In chi tiết từng địa điểm
    for i, (id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
        print(f"\nĐịa điểm {i}:")
        print(f"ID: {id}")
        print(f"Tên địa điểm: {metadata['ten_dia_diem']}")
        print(f"Mô tả: {metadata['mo_ta']}")
        print(f"Document: {document}")
        print("-" * 50)

    # Lưu dữ liệu ra file JSON để dễ xem
    output_data = []
    for id, metadata, document in zip(results['ids'], results['metadatas'], results['documents']):
        output_data.append({
            'id': id,
            'ten_dia_diem': metadata['ten_dia_diem'],
            'mo_ta': metadata['mo_ta'],
            'document': document
        })

    output_file = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nĐã lưu dữ liệu chi tiết vào file: {output_file}")
 