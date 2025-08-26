#!/usr/bin/env python3
"""
Table analysis example for Adobe PDF Extract API
Analyze extracted table data using pandas
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

def analyze_extracted_data(output_dir: str):
    """
    Analyze extracted table data from PDF extraction results
    
    Args:
        output_dir: Directory containing extraction results
    """
    
    print(f"🔍 Analyzing extracted data in: {output_dir}")
    
    # Find all extraction result directories
    result_dirs = [d for d in os.listdir(output_dir) 
                   if os.path.isdir(os.path.join(output_dir, d))]
    
    if not result_dirs:
        print(f"❌ No extraction results found in {output_dir}")
        return
    
    print(f"📁 Found {len(result_dirs)} extraction result directories")
    
    for result_dir in result_dirs:
        result_path = os.path.join(output_dir, result_dir)
        print(f"\n📊 Analyzing: {result_dir}")
        
        # Look for JSON file with structured data
        json_files = [f for f in os.listdir(result_path) if f.endswith('.json')]
        csv_files = [f for f in os.listdir(result_path) if f.endswith('.csv')]
        
        # Analyze JSON structure
        if json_files:
            json_file = os.path.join(result_path, json_files[0])
            analyze_json_structure(json_file)
        
        # Analyze CSV tables
        if csv_files:
            for csv_file in csv_files:
                csv_path = os.path.join(result_path, csv_file)
                analyze_csv_table(csv_path)


def analyze_json_structure(json_file: str):
    """Analyze the JSON structure from PDF extraction"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  📄 JSON Structure Analysis:")
        
        # Count elements by type
        elements = data.get('elements', [])
        element_types = {}
        
        for element in elements:
            elem_type = element.get('Path', 'Unknown')
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        for elem_type, count in element_types.items():
            print(f"    • {elem_type}: {count} elements")
        
        # Analyze tables specifically
        tables = [elem for elem in elements if 'Table' in elem.get('Path', '')]
        if tables:
            print(f"    📊 Found {len(tables)} table elements")
            
            for i, table in enumerate(tables):
                bounds = table.get('Bounds', [])
                if bounds and len(bounds) >= 4:
                    print(f"      Table {i+1}: {bounds[2]:.0f}x{bounds[3]:.0f} pixels")
        
    except Exception as e:
        print(f"    ❌ Error analyzing JSON: {e}")


def analyze_csv_table(csv_file: str):
    """Analyze a CSV table file"""
    try:
        df = pd.read_csv(csv_file)
        
        print(f"  📊 CSV Table Analysis: {os.path.basename(csv_file)}")
        print(f"    • Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"    • Columns: {list(df.columns)}")
        
        # Check for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            print(f"    • Numeric columns: {numeric_cols}")
            
            # Basic statistics for numeric columns
            for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                if not df[col].empty:
                    print(f"      {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")
        
        # Check for missing data
        missing_data = df.isnull().sum().sum()
        if missing_data > 0:
            print(f"    ⚠️  Missing values: {missing_data}")
        
        # Sample data preview
        if not df.empty:
            print(f"    📋 Sample data (first 2 rows):")
            for i, row in df.head(2).iterrows():
                print(f"      Row {i+1}: {dict(row)}")
        
    except Exception as e:
        print(f"    ❌ Error analyzing CSV: {e}")


def create_summary_report(output_dir: str, report_file: str = "analysis_report.txt"):
    """Create a summary report of all extracted data"""
    
    report_path = os.path.join(output_dir, report_file)
    
    with open(report_path, 'w') as f:
        f.write("Adobe PDF Extract API - Analysis Report\n")
        f.write("=" * 50 + "\n\n")
        
        # Find all result directories
        result_dirs = [d for d in os.listdir(output_dir) 
                       if os.path.isdir(os.path.join(output_dir, d))]
        
        f.write(f"Total PDF files processed: {len(result_dirs)}\n\n")
        
        for result_dir in result_dirs:
            result_path = os.path.join(output_dir, result_dir)
            f.write(f"File: {result_dir}\n")
            f.write("-" * 30 + "\n")
            
            # Count files by type
            files = os.listdir(result_path)
            json_files = [f for f in files if f.endswith('.json')]
            csv_files = [f for f in files if f.endswith('.csv')]
            xlsx_files = [f for f in files if f.endswith('.xlsx')]
            
            f.write(f"JSON files: {len(json_files)}\n")
            f.write(f"CSV files: {len(csv_files)}\n")
            f.write(f"Excel files: {len(xlsx_files)}\n")
            
            # Analyze CSV files
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(os.path.join(result_path, csv_file))
                    f.write(f"  {csv_file}: {df.shape[0]} rows × {df.shape[1]} columns\n")
                except:
                    f.write(f"  {csv_file}: Error reading file\n")
            
            f.write("\n")
    
    print(f"📄 Summary report created: {report_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze extracted PDF data")
    parser.add_argument("output_dir", help="Directory containing extraction results")
    parser.add_argument("--report", "-r", action="store_true", help="Create summary report")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        print(f"❌ Output directory not found: {args.output_dir}")
        sys.exit(1)
    
    # Install pandas if not available
    try:
        import pandas as pd
    except ImportError:
        print("❌ pandas not installed. Installing...")
        os.system("pip install pandas")
        import pandas as pd
    
    analyze_extracted_data(args.output_dir)
    
    if args.report:
        create_summary_report(args.output_dir)
