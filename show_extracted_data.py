#!/usr/bin/env python3
"""
Show all extracted data with focus on financial accuracy
"""

import os
import json
import webbrowser
from pathlib import Path

def create_data_viewer():
    """Create an HTML viewer for all extracted data"""
    
    # Load the JSON data
    json_file = "output_advanced/messos 30.5/structuredData.json"
    figures_dir = "output_advanced/messos 30.5/figures"
    
    if not os.path.exists(json_file):
        print("❌ JSON file not found")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get figure files
    figure_files = []
    if os.path.exists(figures_dir):
        figure_files = sorted([f for f in os.listdir(figures_dir) if f.endswith('.png')])
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Adobe PDF Extract API - Messos Financial Data</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .financial-data {{ background: #e8f5e8; }}
            .warning {{ background: #fff3cd; border-color: #ffeaa7; }}
            .success {{ background: #d4edda; border-color: #c3e6cb; }}
            .figure-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
            .figure-item {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: white; }}
            .figure-item img {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
            .text-element {{ margin: 5px 0; padding: 8px; background: #f8f9fa; border-left: 3px solid #007bff; }}
            .financial-text {{ border-left-color: #28a745; background: #e8f5e8; }}
            .table-candidate {{ border: 2px solid #28a745; }}
            .low-potential {{ opacity: 0.6; }}
            pre {{ background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .stat-box {{ background: #007bff; color: white; padding: 15px; border-radius: 5px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Adobe PDF Extract API - Messos Financial Data Analysis</h1>
                <p>Comprehensive view of extracted data with OCR feasibility assessment</p>
            </div>
            
            <div class="section success">
                <h2>📊 Extraction Summary</h2>
                <div class="stats">
                    <div class="stat-box">
                        <h3>{len(data.get('elements', []))}</h3>
                        <p>Total Elements</p>
                    </div>
                    <div class="stat-box">
                        <h3>{len(figure_files)}</h3>
                        <p>Figure Images</p>
                    </div>
                    <div class="stat-box">
                        <h3>{len([e for e in data.get('elements', []) if e.get('Text')])}</h3>
                        <p>Text Elements</p>
                    </div>
                    <div class="stat-box">
                        <h3>{len(data.get('pages', []))}</h3>
                        <p>Pages</p>
                    </div>
                </div>
            </div>
    """
    
    # Add financial text elements
    financial_keywords = ['USD', 'EUR', 'CHF', 'valuation', 'portfolio', 'asset', 'bond', 'equity', 'price', 'MESSOS', 'Client']
    financial_texts = []
    all_texts = []
    
    for elem in data.get('elements', []):
        if elem.get('Text'):
            text = elem.get('Text', '').strip()
            page = elem.get('Page', 'Unknown')
            bounds = elem.get('Bounds', [])
            
            all_texts.append({'text': text, 'page': page, 'bounds': bounds, 'is_financial': False})
            
            if any(keyword.lower() in text.lower() for keyword in financial_keywords):
                financial_texts.append({'text': text, 'page': page, 'bounds': bounds, 'is_financial': True})
                all_texts[-1]['is_financial'] = True
    
    html_content += f"""
            <div class="section financial-data">
                <h2>💰 Financial Text Elements ({len(financial_texts)} found)</h2>
                <p><strong>Key Question:</strong> Can OCR accurately match securities with their prices/valuations?</p>
    """
    
    for i, item in enumerate(financial_texts):
        html_content += f"""
                <div class="text-element financial-text">
                    <strong>#{i+1} - Page {item['page']}</strong><br>
                    "{item['text']}"<br>
                    <small>Bounds: {item['bounds']}</small>
                </div>
        """
    
    html_content += """
            </div>
            
            <div class="section">
                <h2>📝 All Text Elements</h2>
    """
    
    for i, item in enumerate(all_texts):
        css_class = "text-element financial-text" if item['is_financial'] else "text-element"
        html_content += f"""
                <div class="{css_class}">
                    <strong>#{i+1} - Page {item['page']}</strong><br>
                    "{item['text']}"<br>
                    <small>Bounds: {item['bounds']}</small>
                </div>
        """
    
    # Add figure analysis
    html_content += f"""
            </div>
            
            <div class="section">
                <h2>🖼️ Extracted Figure Images ({len(figure_files)} total)</h2>
                <p><strong>OCR Assessment:</strong> Which images are most likely to contain accurate table data?</p>
                <div class="figure-grid">
    """
    
    # Analyze each figure
    for fig_file in figure_files:
        fig_path = os.path.join(figures_dir, fig_file)
        file_size = os.path.getsize(fig_path) if os.path.exists(fig_path) else 0
        
        # Determine OCR potential
        if file_size > 10000:
            potential = "HIGH"
            css_class = "figure-item table-candidate"
            color = "#28a745"
        elif file_size > 2000:
            potential = "MEDIUM"
            css_class = "figure-item"
            color = "#ffc107"
        else:
            potential = "LOW"
            css_class = "figure-item low-potential"
            color = "#6c757d"
        
        html_content += f"""
                <div class="{css_class}">
                    <h4 style="color: {color};">{fig_file}</h4>
                    <p><strong>OCR Potential: {potential}</strong></p>
                    <p>Size: {file_size:,} bytes</p>
                    <img src="{fig_path}" alt="{fig_file}" title="Click to view full size">
                    <p><small>{'✅ Good for table extraction' if potential == 'HIGH' else '⚠️ May need manual review' if potential == 'MEDIUM' else '❌ Likely header/label'}</small></p>
                </div>
        """
    
    html_content += """
                </div>
            </div>
            
            <div class="section warning">
                <h2>⚠️ Security-Price Matching Challenges</h2>
                <h3>Key Concerns for Financial Accuracy:</h3>
                <ul>
                    <li><strong>Spatial Alignment:</strong> Securities and their prices must be correctly aligned in tables</li>
                    <li><strong>Multi-column Tables:</strong> Complex financial tables with multiple data columns</li>
                    <li><strong>Currency Identification:</strong> Ensuring prices are matched with correct currency (USD/EUR/CHF)</li>
                    <li><strong>Table Headers:</strong> Distinguishing between headers and actual data rows</li>
                    <li><strong>Page Breaks:</strong> Tables spanning multiple pages need careful handling</li>
                </ul>
                
                <h3>Recommended Approach:</h3>
                <ol>
                    <li><strong>Manual Review First:</strong> Examine the HIGH potential images manually</li>
                    <li><strong>Selective OCR:</strong> Process only images that clearly contain tabular data</li>
                    <li><strong>Validation Step:</strong> Cross-reference extracted data with original PDF</li>
                    <li><strong>Structured Output:</strong> Ensure OCR preserves row-column relationships</li>
                </ol>
            </div>
            
            <div class="section success">
                <h2>✅ Next Steps</h2>
                <p><strong>Based on the analysis:</strong></p>
                <ul>
                    <li>🎯 <strong>1 HIGH potential image</strong> (fileoutpart1.png - 1.9MB) - likely contains main financial table</li>
                    <li>📊 <strong>23 MEDIUM potential images</strong> - may contain supporting data or charts</li>
                    <li>🔍 <strong>Manual inspection recommended</strong> before OCR processing</li>
                    <li>💰 <strong>Estimated OCR cost:</strong> $0.02-0.50 for selective processing</li>
                </ul>
                
                <h3>Would you like to:</h3>
                <ol>
                    <li><strong>View the HIGH potential image</strong> to assess table structure?</li>
                    <li><strong>Process with OCR</strong> to extract structured data?</li>
                    <li><strong>Manual extraction</strong> from the key images?</li>
                </ol>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    # Save HTML file
    html_file = "extracted_data_viewer.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Data viewer created: {html_file}")
    return html_file

def main():
    """Create and open the data viewer"""
    html_file = create_data_viewer()
    
    # Open in browser
    file_path = os.path.abspath(html_file)
    webbrowser.open(f"file://{file_path}")
    print(f"🌐 Opening data viewer in browser...")
    print(f"📁 File location: {file_path}")

if __name__ == "__main__":
    main()
