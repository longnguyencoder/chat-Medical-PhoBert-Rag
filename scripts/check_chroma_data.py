import chromadb
import os
import sys

# Add the src directory to the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

def check_chroma_db():
    try:
        workspace_root = os.path.dirname(current_dir)
        chroma_db_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
        
        print(f"Checking ChromaDB at: {chroma_db_path}")
        
        if not os.path.exists(chroma_db_path):
            print("ChromaDB directory not found.")
            return

        client = chromadb.PersistentClient(path=chroma_db_path)
        
        try:
            collection = client.get_collection("medical_collection")
            count = collection.count()
            print(f"Collection 'medical_collection' found.")
            print(f"Total documents: {count}")
            
            # Retrieve a few items to verify
            if count > 0:
                results = collection.peek(limit=1)
                print("\nSample document:")
                print(results)
                
        except Exception as e:
            print(f"Error accessing collection: {e}")
            print("Collection 'medical_collection' might not exist.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_chroma_db()
