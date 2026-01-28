import pandas as pd
import os

def inspect_excel():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(current_dir)
        file_path = os.path.join(workspace_root, 'src', 'scape', 'test.xlsx')
        
        print(f"Inspecting file: {file_path}")
        
        if not os.path.exists(file_path):
            print("File not found!")
            return

        # Read the Excel file
        df = pd.read_excel(file_path)
        
        print("\nColumn Names:")
        print(df.columns.tolist())
        
        print(f"\nTotal Rows: {len(df)}")
        
        print("\nFirst 3 rows:")
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")

if __name__ == "__main__":
    inspect_excel()
