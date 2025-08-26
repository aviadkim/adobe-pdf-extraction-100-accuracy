#!/usr/bin/env python3
"""
Batch processing example for Adobe PDF Extract API
Process multiple PDF files in a directory
"""

import os
import sys
import glob
from pathlib import Path

# Add parent directory to path to import pdf_extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_extractor import PDFExtractor

def batch_process_pdfs(input_dir: str, output_dir: str = "output/batch", table_format: str = "csv"):
    """
    Process all PDF files in a directory
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory for output files
        table_format: Format for table extraction ('csv' or 'xlsx')
    """
    
    # Find all PDF files
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {input_dir}")
        return
    
    print(f"🔍 Found {len(pdf_files)} PDF files to process")
    
    # Initialize extractor
    try:
        extractor = PDFExtractor()
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return
    
    # Process each file
    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n📄 Processing {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        
        try:
            result = extractor.extract_tables(
                input_pdf_path=pdf_file,
                output_dir=output_dir,
                table_format=table_format,
                extract_text=True
            )
            
            results.append({
                "file": pdf_file,
                "success": result["success"],
                "result": result
            })
            
            if result["success"]:
                print(f"  ✅ Success")
            else:
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            results.append({
                "file": pdf_file,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"\n📊 Batch Processing Summary:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📁 Output directory: {output_dir}")
    
    # List failed files
    if failed > 0:
        print(f"\n❌ Failed files:")
        for result in results:
            if not result["success"]:
                print(f"  • {os.path.basename(result['file'])}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch process PDF files")
    parser.add_argument("input_dir", help="Directory containing PDF files")
    parser.add_argument("--output-dir", "-o", default="output/batch", help="Output directory")
    parser.add_argument("--table-format", "-f", choices=["csv", "xlsx"], default="csv", help="Table format")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_dir):
        print(f"❌ Input directory not found: {args.input_dir}")
        sys.exit(1)
    
    batch_process_pdfs(args.input_dir, args.output_dir, args.table_format)
