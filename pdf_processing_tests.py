#!/usr/bin/env python3
"""
ADVANCED PDF PROCESSING TESTS
Test multiple PDFs through Adobe and Azure pipelines
"""

import os
import json
import time
import requests
from datetime import datetime

class PDFProcessingTests:
    """Advanced PDF processing test suite"""
    
    def __init__(self):
        self.test_results = {
            'pdf_tests': [],
            'total_pdfs_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_processing_time': 0
        }
    
    def create_test_pdf_files(self):
        """Create multiple test PDF files for comprehensive testing"""
        
        print("Creating test PDF files...")
        
        # Test PDF 1: Simple document
        simple_pdf = '''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] 
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 100 >>
stream
BT
/F1 24 Tf
50 700 Td
(Portfolio Value: 1,000,000) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000251 00000 n 
0000000402 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
482
%%EOF'''
        
        with open('test_portfolio_1.pdf', 'w') as f:
            f.write(simple_pdf)
        
        # Test PDF 2: Financial table structure
        table_pdf = '''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] 
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
50 700 Td
(Bonds: 5,000,000 CHF) Tj
0 -20 Td
(Equities: 2,500,000 CHF) Tj
0 -20 Td
(Structured Products: 3,200,000 CHF) Tj
0 -20 Td
(Total: 10,700,000 CHF) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000251 00000 n 
0000000502 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
582
%%EOF'''
        
        with open('test_portfolio_2.pdf', 'w') as f:
            f.write(table_pdf)
        
        # Test PDF 3: Swiss number format
        swiss_pdf = '''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] 
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 150 >>
stream
BT
/F1 12 Tf
50 700 Td
(Investment Portfolio) Tj
0 -40 Td
(Total Value: 15'234'567.89 CHF) Tj
0 -20 Td
(Cash: 1'456'789.12 CHF) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000251 00000 n 
0000000452 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
532
%%EOF'''
        
        with open('test_portfolio_3.pdf', 'w') as f:
            f.write(swiss_pdf)
        
        # Test PDF 4: Multi-asset portfolio
        multi_asset_pdf = '''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] 
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 300 >>
stream
BT
/F1 10 Tf
50 700 Td
(PORTFOLIO SUMMARY) Tj
0 -30 Td
(Bonds Portfolio: 8'500'000 CHF) Tj
0 -15 Td
(Equities Portfolio: 3'200'000 CHF) Tj
0 -15 Td
(Structured Products: 4'800'000 CHF) Tj
0 -15 Td
(Liquidity: 250'000 CHF) Tj
0 -15 Td
(Other Assets: 180'000 CHF) Tj
0 -15 Td
(Alternative Investments: 1'070'000 CHF) Tj
0 -30 Td
(TOTAL PORTFOLIO: 18'000'000 CHF) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000251 00000 n 
0000000602 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
682
%%EOF'''
        
        with open('test_portfolio_4.pdf', 'w') as f:
            f.write(multi_asset_pdf)
        
        # Test PDF 5: Empty/minimal content
        empty_pdf = '''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
187
%%EOF'''
        
        with open('test_portfolio_empty.pdf', 'w') as f:
            f.write(empty_pdf)
        
        print("Created 5 test PDF files")
        return [
            'test_portfolio_1.pdf',
            'test_portfolio_2.pdf', 
            'test_portfolio_3.pdf',
            'test_portfolio_4.pdf',
            'test_portfolio_empty.pdf'
        ]
    
    def process_pdf_through_system(self, pdf_file, user_email="testuser@example.com"):
        """Process a PDF through the complete system"""
        
        start_time = time.time()
        
        try:
            # Test PDF processing through SaaS system
            with open(pdf_file, 'rb') as f:
                files = {'pdf': (pdf_file, f, 'application/pdf')}
                response = requests.post(
                    f'http://localhost:5001/mcp/user/{user_email}/process-pdf',
                    files=files,
                    timeout=30
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'pdf_file': pdf_file,
                    'processing_time': processing_time,
                    'pages_processed': result.get('pages_processed', 0),
                    'quota_used': result.get('quota_used', 0),
                    'extracted_data': result.get('extracted_data', {}),
                    'confidence': result.get('extracted_data', {}).get('accuracy', 'N/A')
                }
            else:
                return {
                    'success': False,
                    'pdf_file': pdf_file,
                    'processing_time': processing_time,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                'success': False,
                'pdf_file': pdf_file,
                'processing_time': processing_time,
                'error': str(e)
            }
    
    def test_all_pdfs(self):
        """Test all PDF files through the system"""
        
        print("\n" + "="*60)
        print("PDF PROCESSING PIPELINE TESTS")
        print("="*60)
        
        # Create test PDF files
        test_pdfs = self.create_test_pdf_files()
        
        # Test existing real PDF if available
        if os.path.exists('input_pdfs/messos 30.5.pdf'):
            test_pdfs.insert(0, 'input_pdfs/messos 30.5.pdf')
        
        # Process each PDF
        for i, pdf_file in enumerate(test_pdfs, 1):
            print(f"\nTest {i}: Processing {pdf_file}")
            
            result = self.process_pdf_through_system(pdf_file)
            self.test_results['pdf_tests'].append(result)
            
            if result['success']:
                self.test_results['successful_extractions'] += 1
                print(f"  SUCCESS: {result['pages_processed']} pages, "
                      f"{result['processing_time']:.2f}s, "
                      f"Confidence: {result['confidence']}")
            else:
                self.test_results['failed_extractions'] += 1
                print(f"  FAILED: {result['error']}")
            
            self.test_results['total_processing_time'] += result['processing_time']
            self.test_results['total_pdfs_processed'] += 1
        
        # Test concurrent processing
        self.test_concurrent_pdf_processing(test_pdfs)
        
        return self.test_results
    
    def test_concurrent_pdf_processing(self, pdf_files):
        """Test concurrent PDF processing"""
        
        print(f"\nConcurrent Processing Test:")
        print("Processing multiple PDFs simultaneously...")
        
        import threading
        import concurrent.futures
        
        start_time = time.time()
        
        # Process 3 PDFs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for pdf_file in pdf_files[:3]:  # Test first 3 PDFs
                future = executor.submit(self.process_pdf_through_system, pdf_file, f"concurrent{len(futures)}@test.com")
                futures.append(future)
            
            # Collect results
            concurrent_results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                concurrent_results.append(result)
        
        concurrent_time = time.time() - start_time
        successful_concurrent = sum(1 for r in concurrent_results if r['success'])
        
        print(f"  Concurrent processing: {successful_concurrent}/{len(concurrent_results)} succeeded")
        print(f"  Total concurrent time: {concurrent_time:.2f}s")
        print(f"  Average per PDF: {concurrent_time/len(concurrent_results):.2f}s")
        
        self.test_results['concurrent_test'] = {
            'total_time': concurrent_time,
            'pdfs_processed': len(concurrent_results),
            'successful': successful_concurrent,
            'average_time_per_pdf': concurrent_time/len(concurrent_results)
        }
    
    def generate_pdf_test_report(self):
        """Generate comprehensive PDF test report"""
        
        print("\n" + "="*60)
        print("PDF PROCESSING TEST SUMMARY")
        print("="*60)
        
        print(f"Total PDFs Processed: {self.test_results['total_pdfs_processed']}")
        print(f"Successful Extractions: {self.test_results['successful_extractions']}")
        print(f"Failed Extractions: {self.test_results['failed_extractions']}")
        print(f"Success Rate: {(self.test_results['successful_extractions']/self.test_results['total_pdfs_processed']*100):.1f}%")
        print(f"Total Processing Time: {self.test_results['total_processing_time']:.2f}s")
        print(f"Average Time per PDF: {(self.test_results['total_processing_time']/self.test_results['total_pdfs_processed']):.2f}s")
        
        if 'concurrent_test' in self.test_results:
            concurrent = self.test_results['concurrent_test']
            print(f"\nConcurrent Processing:")
            print(f"  Concurrent PDFs: {concurrent['pdfs_processed']}")
            print(f"  Successful: {concurrent['successful']}")
            print(f"  Total Time: {concurrent['total_time']:.2f}s")
            print(f"  Avg Time per PDF: {concurrent['average_time_per_pdf']:.2f}s")
        
        print("\nDetailed Results:")
        for i, result in enumerate(self.test_results['pdf_tests'], 1):
            status = "SUCCESS" if result['success'] else "FAILED"
            print(f"  {i}. {result['pdf_file']}: {status} ({result['processing_time']:.2f}s)")
            if not result['success']:
                print(f"     Error: {result['error']}")
        
        print("="*60)
        
        # Save detailed report
        with open('test_results/pdf_processing_report.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print("PDF processing report saved: test_results/pdf_processing_report.json")

if __name__ == "__main__":
    os.makedirs('test_results', exist_ok=True)
    
    pdf_tester = PDFProcessingTests()
    results = pdf_tester.test_all_pdfs()
    pdf_tester.generate_pdf_test_report()