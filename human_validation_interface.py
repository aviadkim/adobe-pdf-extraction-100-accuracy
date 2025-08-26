#!/usr/bin/env python3
"""
Human Validation Interface for Financial Data Extraction
Allows manual review and correction of extracted data
"""

import os
import json
import pandas as pd
import webbrowser
from pathlib import Path

class HumanValidationInterface:
    """Interactive interface for validating and correcting extracted data"""
    
    def __init__(self):
        """Initialize validation interface"""
        self.extracted_data_dir = "extracted_data"
        self.figures_dir = "output_advanced/messos 30.5/figures"
        self.validation_dir = "human_validated"
        os.makedirs(self.validation_dir, exist_ok=True)
        
        self.report = None
        self.financial_data = None
        self.corrections = {}
        
    def load_extracted_data(self):
        """Load all extracted data"""
        report_file = os.path.join(self.extracted_data_dir, "comprehensive_extraction_report.json")
        financial_file = os.path.join(self.extracted_data_dir, "financial_elements.csv")
        
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                self.report = json.load(f)
        
        if os.path.exists(financial_file):
            self.financial_data = pd.read_csv(financial_file)
        
        return self.report is not None and self.financial_data is not None
    
    def create_validation_interface(self):
        """Create interactive HTML validation interface"""
        if not self.load_extracted_data():
            print("❌ Could not load extracted data")
            return None
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Financial Data Validation Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
                .container { max-width: 1600px; margin: 0 auto; background: white; }
                .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
                .sidebar { position: fixed; left: 0; top: 0; width: 300px; height: 100vh; background: #34495e; color: white; padding: 20px; overflow-y: auto; }
                .main-content { margin-left: 320px; padding: 20px; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: white; }
                .validation-item { margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9; }
                .correct { border-color: #28a745; background: #d4edda; }
                .incorrect { border-color: #dc3545; background: #f8d7da; }
                .needs-review { border-color: #ffc107; background: #fff3cd; }
                .image-preview { max-width: 100%; height: auto; border: 1px solid #ccc; margin: 10px 0; }
                .edit-field { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 3px; }
                .btn { padding: 10px 15px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
                .btn-success { background: #28a745; color: white; }
                .btn-warning { background: #ffc107; color: black; }
                .btn-danger { background: #dc3545; color: white; }
                .btn-primary { background: #007bff; color: white; }
                .nav-item { padding: 10px; margin: 5px 0; background: #3498db; border-radius: 3px; cursor: pointer; }
                .nav-item:hover { background: #2980b9; }
                .confidence-bar { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }
                .confidence-fill { height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); }
                .data-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                .data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .data-table th { background: #f8f9fa; }
                .editable { background: #fff3cd; cursor: pointer; }
                .editable:hover { background: #ffeaa7; }
            </style>
            <script>
                let corrections = {};
                
                function markCorrect(itemId) {
                    const item = document.getElementById(itemId);
                    item.className = 'validation-item correct';
                    corrections[itemId] = { status: 'correct', value: item.querySelector('.extracted-value').textContent };
                    updateProgress();
                }
                
                function markIncorrect(itemId) {
                    const item = document.getElementById(itemId);
                    item.className = 'validation-item incorrect';
                    const correctedValue = prompt('Enter the correct value:');
                    if (correctedValue) {
                        corrections[itemId] = { status: 'corrected', value: correctedValue };
                        item.querySelector('.correction-note').innerHTML = `<strong>Corrected to:</strong> ${correctedValue}`;
                    }
                    updateProgress();
                }
                
                function needsReview(itemId) {
                    const item = document.getElementById(itemId);
                    item.className = 'validation-item needs-review';
                    const note = prompt('Add a review note:');
                    if (note) {
                        corrections[itemId] = { status: 'review', note: note };
                        item.querySelector('.correction-note').innerHTML = `<strong>Review Note:</strong> ${note}`;
                    }
                    updateProgress();
                }
                
                function editValue(itemId, field) {
                    const currentValue = document.getElementById(itemId + '_' + field).textContent;
                    const newValue = prompt(`Edit ${field}:`, currentValue);
                    if (newValue && newValue !== currentValue) {
                        document.getElementById(itemId + '_' + field).textContent = newValue;
                        if (!corrections[itemId]) corrections[itemId] = {};
                        corrections[itemId][field] = newValue;
                        markIncorrect(itemId);
                    }
                }
                
                function updateProgress() {
                    const totalItems = document.querySelectorAll('.validation-item').length;
                    const reviewedItems = Object.keys(corrections).length;
                    const progress = (reviewedItems / totalItems) * 100;
                    
                    document.getElementById('progress-bar').style.width = progress + '%';
                    document.getElementById('progress-text').textContent = `${reviewedItems}/${totalItems} items reviewed (${Math.round(progress)}%)`;
                }
                
                function exportCorrections() {
                    const dataStr = JSON.stringify(corrections, null, 2);
                    const dataBlob = new Blob([dataStr], {type: 'application/json'});
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = 'validation_corrections.json';
                    link.click();
                }
                
                function showImage(imagePath) {
                    window.open(imagePath, '_blank');
                }
            </script>
        </head>
        <body>
            <div class="sidebar">
                <h3>🔍 Validation Progress</h3>
                <div class="confidence-bar">
                    <div class="confidence-fill" id="progress-bar" style="width: 0%;"></div>
                </div>
                <p id="progress-text">0/0 items reviewed (0%)</p>
                
                <h3>📋 Navigation</h3>
                <div class="nav-item" onclick="document.getElementById('client-info').scrollIntoView()">Client Information</div>
                <div class="nav-item" onclick="document.getElementById('financial-data').scrollIntoView()">Financial Data</div>
                <div class="nav-item" onclick="document.getElementById('image-analysis').scrollIntoView()">Image Analysis</div>
                <div class="nav-item" onclick="document.getElementById('table-data').scrollIntoView()">Table Data</div>
                
                <h3>🛠️ Actions</h3>
                <button class="btn btn-primary" onclick="exportCorrections()">Export Corrections</button>
                <button class="btn btn-success" onclick="alert('Validation complete! Check exported corrections.')">Complete Validation</button>
                
                <h3>📊 Legend</h3>
                <div style="padding: 5px; margin: 5px 0; background: #d4edda; border-radius: 3px;">✅ Correct</div>
                <div style="padding: 5px; margin: 5px 0; background: #f8d7da; border-radius: 3px;">❌ Incorrect</div>
                <div style="padding: 5px; margin: 5px 0; background: #fff3cd; border-radius: 3px;">⚠️ Needs Review</div>
            </div>
            
            <div class="main-content">
                <div class="header">
                    <h1>🏦 Financial Data Validation Interface</h1>
                    <p>Review and correct extracted data from Messos PDF</p>
                    <p><strong>Overall Extraction Confidence: """ + f"{self.report['extraction_confidence']:.1%}" + """</strong></p>
                </div>
        """
        
        # Add client information section
        client_info = self.report.get('client_information', {})
        html_content += f"""
                <div class="section" id="client-info">
                    <h2>🏦 Client Information</h2>
                    <div class="validation-item" id="client_1">
                        <h4>Company Name</h4>
                        <p class="extracted-value" id="client_1_company" onclick="editValue('client_1', 'company')">{client_info.get('company_name', 'Not found')}</p>
                        <div class="correction-note"></div>
                        <button class="btn btn-success" onclick="markCorrect('client_1')">✅ Correct</button>
                        <button class="btn btn-danger" onclick="markIncorrect('client_1')">❌ Incorrect</button>
                        <button class="btn btn-warning" onclick="needsReview('client_1')">⚠️ Review</button>
                    </div>
                    
                    <div class="validation-item" id="client_2">
                        <h4>Client Number</h4>
                        <p class="extracted-value" id="client_2_number" onclick="editValue('client_2', 'number')">{client_info.get('client_number', 'Not found')}</p>
                        <div class="correction-note"></div>
                        <button class="btn btn-success" onclick="markCorrect('client_2')">✅ Correct</button>
                        <button class="btn btn-danger" onclick="markIncorrect('client_2')">❌ Incorrect</button>
                        <button class="btn btn-warning" onclick="needsReview('client_2')">⚠️ Review</button>
                    </div>
                    
                    <div class="validation-item" id="client_3">
                        <h4>Valuation Date</h4>
                        <p class="extracted-value" id="client_3_date" onclick="editValue('client_3', 'date')">{client_info.get('valuation_date', 'Not found')}</p>
                        <div class="correction-note"></div>
                        <button class="btn btn-success" onclick="markCorrect('client_3')">✅ Correct</button>
                        <button class="btn btn-danger" onclick="markIncorrect('client_3')">❌ Incorrect</button>
                        <button class="btn btn-warning" onclick="needsReview('client_3')">⚠️ Review</button>
                    </div>
                    
                    <div class="validation-item" id="client_4">
                        <h4>Valuation Currency</h4>
                        <p class="extracted-value" id="client_4_currency" onclick="editValue('client_4', 'currency')">{client_info.get('valuation_currency', 'Not found')}</p>
                        <div class="correction-note"></div>
                        <button class="btn btn-success" onclick="markCorrect('client_4')">✅ Correct</button>
                        <button class="btn btn-danger" onclick="markIncorrect('client_4')">❌ Incorrect</button>
                        <button class="btn btn-warning" onclick="needsReview('client_4')">⚠️ Review</button>
                    </div>
                </div>
        """
        
        # Add financial data section
        html_content += """
                <div class="section" id="financial-data">
                    <h2>💰 Financial Data Elements</h2>
                    <p>Review each extracted financial element for accuracy:</p>
        """
        
        for idx, row in self.financial_data.iterrows():
            html_content += f"""
                    <div class="validation-item" id="financial_{idx}">
                        <h4>Category: {row['category'].title()}</h4>
                        <p><strong>Text:</strong> <span class="extracted-value editable" id="financial_{idx}_text" onclick="editValue('financial_{idx}', 'text')">{row['text'][:100]}{'...' if len(row['text']) > 100 else ''}</span></p>
                        <p><strong>Page:</strong> {row['page']}</p>
                        <p><strong>Position:</strong> ({row['x']:.0f}, {row['y']:.0f})</p>
                        <div class="correction-note"></div>
                        <button class="btn btn-success" onclick="markCorrect('financial_{idx}')">✅ Correct</button>
                        <button class="btn btn-danger" onclick="markIncorrect('financial_{idx}')">❌ Incorrect</button>
                        <button class="btn btn-warning" onclick="needsReview('financial_{idx}')">⚠️ Review</button>
                    </div>
            """
        
        # Add image analysis section
        html_content += """
                <div class="section" id="image-analysis">
                    <h2>🖼️ Image Analysis & Table Candidates</h2>
                    <p>Review extracted images and their potential for containing financial tables:</p>
        """
        
        for idx, img in enumerate(self.report.get('image_analysis', [])):
            if img['confidence'] > 0.7:  # Only show high confidence images
                img_path = os.path.join(self.figures_dir, img['filename'])
                html_content += f"""
                        <div class="validation-item" id="image_{idx}">
                            <h4>{img['filename']} - {img['category']}</h4>
                            <p><strong>Confidence:</strong> {img['confidence']:.1%}</p>
                            <p><strong>Size:</strong> {img['file_size']:,} bytes ({img['dimensions']})</p>
                            <p><strong>Predicted Content:</strong> {', '.join(img['likely_content'])}</p>
                            <img src="{img_path}" class="image-preview" onclick="showImage('{img_path}')" style="max-width: 400px; cursor: pointer;" title="Click to view full size">
                            <div class="correction-note"></div>
                            <button class="btn btn-success" onclick="markCorrect('image_{idx}')">✅ Contains Table Data</button>
                            <button class="btn btn-danger" onclick="markIncorrect('image_{idx}')">❌ No Table Data</button>
                            <button class="btn btn-warning" onclick="needsReview('image_{idx}')">⚠️ Needs OCR</button>
                        </div>
                """
        
        # Add table data section
        html_content += """
                <div class="section" id="table-data">
                    <h2>📊 Reconstructed Table Data</h2>
                    <p>Review spatial analysis results for table reconstruction:</p>
        """
        
        tables = self.report.get('reconstructed_tables', [])
        if tables:
            for idx, table in enumerate(tables):
                html_content += f"""
                        <div class="validation-item" id="table_{idx}">
                            <h4>Table {idx + 1} (Page {table['page']})</h4>
                            <p><strong>Dimensions:</strong> {table['rows']} rows × {table['columns']} columns</p>
                            <table class="data-table">
                """
                
                for row_idx, row_data in enumerate(table['data'][:5]):  # Show first 5 rows
                    html_content += "<tr>"
                    for cell in row_data:
                        html_content += f"<td class='editable' onclick='editValue(\"table_{idx}\", \"cell_{row_idx}\")'>{cell[:30]}{'...' if len(cell) > 30 else ''}</td>"
                    html_content += "</tr>"
                
                html_content += """
                            </table>
                            <div class="correction-note"></div>
                            <button class="btn btn-success" onclick="markCorrect('table_""" + str(idx) + """')">✅ Correct Structure</button>
                            <button class="btn btn-danger" onclick="markIncorrect('table_""" + str(idx) + """')">❌ Incorrect Structure</button>
                            <button class="btn btn-warning" onclick="needsReview('table_""" + str(idx) + """')">⚠️ Needs Manual Entry</button>
                        </div>
                """
        else:
            html_content += """
                    <div class="validation-item needs-review">
                        <h4>No Tables Reconstructed from Text</h4>
                        <p>The spatial analysis did not find clear table structures in the text elements. This suggests the main financial data is in the image files.</p>
                        <p><strong>Recommendation:</strong> Focus on the high-confidence images above for manual data entry or OCR processing.</p>
                    </div>
            """
        
        html_content += """
                </div>
                
                <div class="section">
                    <h2>✅ Validation Complete</h2>
                    <p>Once you've reviewed all items above:</p>
                    <ol>
                        <li>Click "Export Corrections" to save your validation results</li>
                        <li>Use the exported JSON file to update the extraction system</li>
                        <li>Re-run extraction with human corrections applied</li>
                    </ol>
                    <button class="btn btn-primary" onclick="exportCorrections()" style="font-size: 18px; padding: 15px 30px;">📥 Export All Corrections</button>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        html_file = os.path.join(self.validation_dir, "validation_interface.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def create_summary_report(self):
        """Create a summary report of what was extracted"""
        summary = {
            "extraction_date": "2025-01-22",
            "source_document": "messos 30.5.pdf",
            "extraction_confidence": f"{self.report['extraction_confidence']:.1%}",
            "client_information": self.report.get('client_information', {}),
            "data_quality": {
                "text_elements_found": len(self.financial_data),
                "high_confidence_images": len([img for img in self.report.get('image_analysis', []) if img['confidence'] > 0.8]),
                "tables_reconstructed": len(self.report.get('reconstructed_tables', [])),
                "manual_review_needed": len(self.report.get('image_analysis', [])) > 0
            },
            "next_steps": [
                "Review client information accuracy",
                "Validate financial data elements",
                "Process high-confidence images with OCR or manual entry",
                "Cross-reference extracted data with original PDF",
                "Export corrected data for final use"
            ]
        }
        
        summary_file = os.path.join(self.validation_dir, "extraction_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary


def main():
    """Create and launch human validation interface"""
    print("🔍 **HUMAN VALIDATION INTERFACE**")
    print("=" * 50)
    
    validator = HumanValidationInterface()
    
    # Create validation interface
    html_file = validator.create_validation_interface()
    summary = validator.create_summary_report()
    
    if html_file:
        # Open in browser
        file_path = os.path.abspath(html_file)
        webbrowser.open(f"file://{file_path}")
        
        print(f"✅ Validation interface created and opened")
        print(f"📁 Interface: {html_file}")
        print(f"📊 Summary: {validator.validation_dir}/extraction_summary.json")
        
        print(f"\n📋 **WHAT TO VALIDATE:**")
        print(f"✅ Client Information: Company name, client number, dates")
        print(f"💰 Financial Elements: {len(validator.financial_data)} items to review")
        print(f"🖼️ Image Analysis: {len([img for img in validator.report.get('image_analysis', []) if img['confidence'] > 0.7])} high-confidence images")
        print(f"📊 Table Data: {len(validator.report.get('reconstructed_tables', []))} reconstructed tables")
        
        print(f"\n🎯 **VALIDATION WORKFLOW:**")
        print(f"1. Review each section in the interface")
        print(f"2. Mark items as ✅ Correct, ❌ Incorrect, or ⚠️ Needs Review")
        print(f"3. Edit values by clicking on them")
        print(f"4. Export corrections when complete")
        print(f"5. Use corrections to improve future extractions")
        
        print(f"\n🚀 **INTERFACE IS READY FOR HUMAN VALIDATION!**")
        
    else:
        print("❌ Failed to create validation interface")


if __name__ == "__main__":
    main()
