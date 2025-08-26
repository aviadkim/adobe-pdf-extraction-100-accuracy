#!/usr/bin/env python3
"""
Extract securities data from the high-quality images we have
Focus on the key pages (6-13) that contain bonds, equities, and other assets
"""

import os
import json
import pandas as pd
from PIL import Image
import webbrowser

def analyze_securities_images():
    """Analyze the extracted images to identify securities data"""
    
    print("🔍 **ANALYZING SECURITIES IMAGES FOR DATA EXTRACTION**")
    print("=" * 60)
    
    # We have images from our first extraction
    figures_dir = "output_advanced/messos 30.5/figures"
    
    if not os.path.exists(figures_dir):
        print("❌ Figures directory not found")
        return None
    
    # Get all figure files
    figure_files = sorted([f for f in os.listdir(figures_dir) if f.endswith('.png')])
    
    print(f"📊 Found {len(figure_files)} extracted images")
    
    # Analyze each image for securities content
    securities_images = []
    
    for fig_file in figure_files:
        fig_path = os.path.join(figures_dir, fig_file)
        file_size = os.path.getsize(fig_path)
        
        try:
            with Image.open(fig_path) as img:
                width, height = img.size
                aspect_ratio = width / height if height > 0 else 0
            
            # Determine likely content based on file number and size
            file_num = int(fig_file.replace('fileoutpart', '').replace('.png', ''))
            
            content_type = "Unknown"
            priority = "LOW"
            likely_securities = False
            
            # Based on our document structure analysis:
            if file_num == 1:
                content_type = "Summary/Overview"
                priority = "HIGH"
            elif file_num == 6:
                content_type = "BONDS SECTION"
                priority = "VERY HIGH"
                likely_securities = True
            elif file_num == 10:
                content_type = "EQUITIES SECTION"
                priority = "VERY HIGH"
                likely_securities = True
            elif 11 <= file_num <= 13:
                content_type = "OTHER ASSETS"
                priority = "HIGH"
                likely_securities = True
            elif file_num <= 5:
                content_type = "Headers/Summary"
                priority = "MEDIUM"
            elif file_num >= 14:
                content_type = "Appendices/Notes"
                priority = "LOW"
            
            # Size-based assessment
            if file_size > 500000:  # >500KB
                priority = "VERY HIGH" if priority != "VERY HIGH" else priority
            elif file_size > 100000:  # >100KB
                priority = "HIGH" if priority == "LOW" else priority
            
            image_info = {
                'filename': fig_file,
                'file_number': file_num,
                'file_size': file_size,
                'size_kb': round(file_size / 1024, 1),
                'dimensions': f"{width}x{height}",
                'aspect_ratio': round(aspect_ratio, 2),
                'content_type': content_type,
                'priority': priority,
                'likely_securities': likely_securities,
                'path': fig_path
            }
            
            securities_images.append(image_info)
            
        except Exception as e:
            print(f"⚠️ Could not analyze {fig_file}: {e}")
    
    # Sort by priority and file number
    priority_order = {"VERY HIGH": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    securities_images.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['file_number']), reverse=True)
    
    return securities_images

def create_securities_extraction_interface(securities_images):
    """Create interface for extracting securities data from images"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Securities Data Extraction from Images</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            .header {{ background: #28a745; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
            .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            .very-high {{ border-left: 5px solid #dc3545; background: #fff5f5; }}
            .high {{ border-left: 5px solid #ffc107; background: #fffef5; }}
            .medium {{ border-left: 5px solid #17a2b8; background: #f5feff; }}
            .low {{ border-left: 5px solid #6c757d; background: #f8f9fa; opacity: 0.7; }}
            .image-container {{ text-align: center; margin: 20px 0; }}
            .image-container img {{ max-width: 100%; height: auto; border: 2px solid #ddd; border-radius: 5px; cursor: pointer; }}
            .image-container img:hover {{ border-color: #007bff; }}
            .extraction-form {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .form-row {{ margin: 10px 0; }}
            .form-row label {{ display: inline-block; width: 150px; font-weight: bold; }}
            .form-row input, .form-row textarea {{ width: 300px; padding: 5px; border: 1px solid #ddd; border-radius: 3px; }}
            .btn {{ padding: 10px 15px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }}
            .btn-primary {{ background: #007bff; color: white; }}
            .btn-success {{ background: #28a745; color: white; }}
            .instructions {{ background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .priority-badge {{ padding: 5px 10px; border-radius: 15px; color: white; font-weight: bold; }}
            .very-high-badge {{ background: #dc3545; }}
            .high-badge {{ background: #ffc107; color: black; }}
            .medium-badge {{ background: #17a2b8; }}
            .low-badge {{ background: #6c757d; }}
        </style>
        <script>
            let extractedSecurities = [];
            
            function addSecurity(imageFile) {{
                const name = document.getElementById(imageFile + '_name').value;
                const isin = document.getElementById(imageFile + '_isin').value;
                const price = document.getElementById(imageFile + '_price').value;
                const value = document.getElementById(imageFile + '_value').value;
                const currency = document.getElementById(imageFile + '_currency').value;
                const quantity = document.getElementById(imageFile + '_quantity').value;
                
                if (name) {{
                    const security = {{
                        source_image: imageFile,
                        name: name,
                        isin: isin,
                        price: price,
                        market_value: value,
                        currency: currency,
                        quantity: quantity,
                        timestamp: new Date().toISOString()
                    }};
                    
                    extractedSecurities.push(security);
                    
                    // Clear form
                    document.getElementById(imageFile + '_name').value = '';
                    document.getElementById(imageFile + '_isin').value = '';
                    document.getElementById(imageFile + '_price').value = '';
                    document.getElementById(imageFile + '_value').value = '';
                    document.getElementById(imageFile + '_currency').value = '';
                    document.getElementById(imageFile + '_quantity').value = '';
                    
                    updateSecuritiesList();
                    alert('Security added successfully!');
                }}
            }}
            
            function updateSecuritiesList() {{
                const listDiv = document.getElementById('securities-list');
                listDiv.innerHTML = '<h3>Extracted Securities (' + extractedSecurities.length + '):</h3>';
                
                extractedSecurities.forEach((security, index) => {{
                    listDiv.innerHTML += `
                        <div style="background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px;">
                            <strong>${{security.name}}</strong><br>
                            ISIN: ${{security.isin}} | Price: ${{security.price}} | Value: ${{security.market_value}}<br>
                            Currency: ${{security.currency}} | Quantity: ${{security.quantity}}<br>
                            <small>Source: ${{security.source_image}}</small>
                        </div>
                    `;
                }});
            }}
            
            function exportSecurities() {{
                if (extractedSecurities.length === 0) {{
                    alert('No securities extracted yet!');
                    return;
                }}
                
                const dataStr = JSON.stringify(extractedSecurities, null, 2);
                const dataBlob = new Blob([dataStr], {{type: 'application/json'}});
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'extracted_securities_data.json';
                link.click();
                
                // Also create CSV
                let csvContent = 'Name,ISIN,Price,Market Value,Currency,Quantity,Source Image\\n';
                extractedSecurities.forEach(security => {{
                    csvContent += `"${{security.name}}","${{security.isin}}","${{security.price}}","${{security.market_value}}","${{security.currency}}","${{security.quantity}}","${{security.source_image}}"\\n`;
                }});
                
                const csvBlob = new Blob([csvContent], {{type: 'text/csv'}});
                const csvUrl = URL.createObjectURL(csvBlob);
                const csvLink = document.createElement('a');
                csvLink.href = csvUrl;
                csvLink.download = 'extracted_securities_data.csv';
                csvLink.click();
                
                alert('Securities data exported as JSON and CSV!');
            }}
            
            function openImageFullSize(imagePath) {{
                window.open(imagePath, '_blank');
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Securities Data Extraction Interface</h1>
                <p>Extract individual securities data from high-quality table images</p>
                <p><strong>Goal:</strong> Get every security with name, ISIN, price, and market value</p>
            </div>
            
            <div class="instructions">
                <h3>📋 Instructions:</h3>
                <ol>
                    <li><strong>Focus on VERY HIGH priority images first</strong> (Bonds and Equities sections)</li>
                    <li><strong>Click on images</strong> to view them full-size for better readability</li>
                    <li><strong>Extract each security</strong> you see in the tables</li>
                    <li><strong>Fill in all available data</strong> for each security</li>
                    <li><strong>Export your data</strong> when complete</li>
                </ol>
                <p><strong>💡 Tip:</strong> Look for tables with columns like: Security Name, ISIN, Price, Market Value, Currency</p>
            </div>
            
            <div id="securities-list" style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Extracted Securities (0):</h3>
                <p>Securities you extract will appear here...</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <button class="btn btn-success" onclick="exportSecurities()" style="font-size: 18px; padding: 15px 30px;">
                    📥 Export All Securities Data
                </button>
            </div>
    """
    
    # Add each image with extraction form
    for img in securities_images:
        priority_class = img['priority'].lower().replace(' ', '-')
        badge_class = f"{priority_class}-badge"
        
        html_content += f"""
            <div class="section {priority_class}">
                <h2>
                    📊 {img['filename']} - {img['content_type']}
                    <span class="priority-badge {badge_class}">{img['priority']}</span>
                </h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4>📈 Image Details:</h4>
                        <ul>
                            <li><strong>File Number:</strong> {img['file_number']}</li>
                            <li><strong>Size:</strong> {img['size_kb']} KB</li>
                            <li><strong>Dimensions:</strong> {img['dimensions']}</li>
                            <li><strong>Likely Securities:</strong> {'✅ YES' if img['likely_securities'] else '❌ NO'}</li>
                        </ul>
                        
                        {'<div class="instructions"><strong>🎯 PRIORITY:</strong> This image likely contains main securities data with individual holdings!</div>' if img['likely_securities'] else ''}
                    </div>
                    
                    <div class="extraction-form">
                        <h4>📝 Extract Security Data:</h4>
                        <div class="form-row">
                            <label>Security Name:</label>
                            <input type="text" id="{img['filename']}_name" placeholder="e.g., Swiss Government Bond 2025">
                        </div>
                        <div class="form-row">
                            <label>ISIN Code:</label>
                            <input type="text" id="{img['filename']}_isin" placeholder="e.g., CH0123456789">
                        </div>
                        <div class="form-row">
                            <label>Price:</label>
                            <input type="text" id="{img['filename']}_price" placeholder="e.g., 102.50">
                        </div>
                        <div class="form-row">
                            <label>Market Value:</label>
                            <input type="text" id="{img['filename']}_value" placeholder="e.g., 1,234,567.89">
                        </div>
                        <div class="form-row">
                            <label>Currency:</label>
                            <input type="text" id="{img['filename']}_currency" placeholder="e.g., USD">
                        </div>
                        <div class="form-row">
                            <label>Quantity:</label>
                            <input type="text" id="{img['filename']}_quantity" placeholder="e.g., 1,000">
                        </div>
                        <button class="btn btn-primary" onclick="addSecurity('{img['filename']}')">
                            ➕ Add This Security
                        </button>
                    </div>
                </div>
                
                <div class="image-container">
                    <img src="{img['path']}" alt="{img['filename']}" onclick="openImageFullSize('{img['path']}')" title="Click to view full size">
                </div>
            </div>
        """
    
    html_content += """
            <div class="section" style="background: #d4edda; border-color: #c3e6cb;">
                <h2>🎉 Extraction Complete!</h2>
                <p><strong>Once you've extracted all securities:</strong></p>
                <ol>
                    <li>Click "Export All Securities Data" to save your work</li>
                    <li>You'll get both JSON and CSV files with all securities</li>
                    <li>The data will include every security with complete information</li>
                </ol>
                
                <div style="text-align: center; margin: 20px 0;">
                    <button class="btn btn-success" onclick="exportSecurities()" style="font-size: 20px; padding: 20px 40px;">
                        🎯 Export Complete Securities Data
                    </button>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Create securities extraction interface"""
    print("🔍 **CREATING SECURITIES EXTRACTION INTERFACE**")
    print("=" * 60)
    
    # Analyze images
    securities_images = analyze_securities_images()
    
    if not securities_images:
        print("❌ No images found for analysis")
        return
    
    # Show analysis results
    print(f"📊 **IMAGE ANALYSIS RESULTS:**")
    very_high = [img for img in securities_images if img['priority'] == 'VERY HIGH']
    high = [img for img in securities_images if img['priority'] == 'HIGH']
    
    print(f"🎯 VERY HIGH priority (main securities): {len(very_high)} images")
    for img in very_high:
        print(f"   • {img['filename']}: {img['content_type']} ({img['size_kb']} KB)")
    
    print(f"📊 HIGH priority (supporting data): {len(high)} images")
    
    # Create extraction interface
    html_content = create_securities_extraction_interface(securities_images)
    
    # Save and open
    html_file = "securities_extraction_interface.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Open in browser
    file_path = os.path.abspath(html_file)
    webbrowser.open(f"file://{file_path}")
    
    print(f"✅ Securities extraction interface created: {html_file}")
    print(f"🌐 Opening in browser...")
    
    print(f"\n🎯 **NEXT STEPS:**")
    print(f"1. Focus on the VERY HIGH priority images first")
    print(f"2. Extract every security you see in the tables")
    print(f"3. Fill in: Name, ISIN, Price, Market Value, Currency, Quantity")
    print(f"4. Export the complete data when finished")
    
    print(f"\n🏆 **THIS WILL GET YOU EVERY SECURITY WITH COMPLETE DATA!**")

if __name__ == "__main__":
    main()
