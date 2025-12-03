"""
Load and preview Excel file

This script will:
1. Load Excel file
2. Show structure and columns
3. Preview first few rows
"""

import pandas as pd
import sys

def preview_excel(excel_path: str):
    """Preview Excel file structure"""
    
    print("="*80)
    print(f"Loading Excel: {excel_path}")
    print("="*80)
    
    try:
        # Load Excel
        df = pd.read_excel(excel_path)
        
        print(f"\n✓ Loaded successfully!")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"\nColumn names:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        print(f"\n" + "="*80)
        print("First 5 rows:")
        print("="*80)
        print(df.head().to_string())
        
        print(f"\n" + "="*80)
        print("Data types:")
        print("="*80)
        print(df.dtypes)
        
        print(f"\n" + "="*80)
        print("Summary:")
        print("="*80)
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            print(f"\nMissing values:")
            print(missing[missing > 0])
        
        return df
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    excel_file = "src/scape/test.xlsx"
    df = preview_excel(excel_file)
    
    if df is not None:
        print(f"\n" + "="*80)
        print("✅ Preview completed!")
        print("="*80)
