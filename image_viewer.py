#!/usr/bin/env python3
"""
Image viewer for extracted table images
"""

import os
import webbrowser
from PIL import Image

def create_image_viewer():
    """Create HTML viewer for all extracted images in order"""
    
    figures_dir = "output_advanced/messos 30.5/figures"
    
    if not os.path.exists(figures_dir):
        print("❌ Figures directory not found")
        return
    
    # Get all figure files and sort them
    figure_files = sorted([f for f in os.listdir(figures_dir) if f.endswith('.png')])
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Messos PDF - Extracted Table Images</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
            .image-section { margin: 30px 0; padding: 20px; border: 2px solid #ddd; border-radius: 8px; }
            .high-potential { border-color: #28a745; background: #f8fff8; }
            .medium-potential { border-color: #ffc107; background: #fffef8; }
            .low-potential { border-color: #6c757d; background: #f8f9fa; opacity: 0.8; }
            .image-container { text-align: center; margin: 20px 0; }
            .image-container img { max-width: 100%; height: auto; border: 1px solid #ccc; border-radius: 4px; }
            .image-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .ocr-assessment { padding: 15px; border-radius: 5px; margin: 10px 0; }
            .high-score { background: #d4edda; border: 1px solid #c3e6cb; }
            .medium-score { background: #fff3cd; border: 1px solid #ffeaa7; }
            .low-score { background: #f8d7da; border: 1px solid #f5c6cb; }
            .navigation { position: fixed; top: 20px; right: 20px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .navigation a { display: block; margin: 5px 0; color: #007bff; text-decoration: none; }
            .navigation a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Messos PDF - Extracted Table Images</h1>
                <p>All 28 extracted images in order with OCR assessment</p>
                <p><strong>Goal:</strong> Identify which images contain securities with their prices/valuations</p>
            </div>
            
            <div class="navigation">
                <h4>Quick Navigation</h4>
    """
    
    # Add navigation links
    for fig_file in figure_files:
        file_num = fig_file.replace('fileoutpart', '').replace('.png', '')
        html_content += f'<a href="#{fig_file}">Image {file_num}</a>\n'
    
    html_content += """
            </div>
    """
    
    # Process each image
    for i, fig_file in enumerate(figure_files):
        fig_path = os.path.join(figures_dir, fig_file)
        file_num = fig_file.replace('fileoutpart', '').replace('.png', '')
        
        # Get image info
        file_size = os.path.getsize(fig_path)
        
        try:
            with Image.open(fig_path) as img:
                width, height = img.size
                aspect_ratio = width / height if height > 0 else 0
        except:
            width, height, aspect_ratio = 0, 0, 0
        
        # Assess OCR potential
        ocr_score = 0
        assessment_notes = []
        
        # Size assessment
        if file_size > 100000:  # >100KB
            ocr_score += 3
            assessment_notes.append("✅ Large file - likely complex table")
        elif file_size > 10000:  # >10KB
            ocr_score += 2
            assessment_notes.append("✅ Good size for table data")
        elif file_size > 2000:  # >2KB
            ocr_score += 1
            assessment_notes.append("⚠️ Medium size - possible table")
        else:
            assessment_notes.append("❌ Small size - likely header/label")
        
        # Aspect ratio assessment
        if 1.2 <= aspect_ratio <= 4.0:
            ocr_score += 2
            assessment_notes.append("✅ Table-like aspect ratio")
        elif aspect_ratio > 4.0:
            ocr_score += 1
            assessment_notes.append("⚠️ Very wide - possible table")
        else:
            assessment_notes.append("❌ Square/tall - likely chart/graphic")
        
        # Dimension assessment
        if width > 500 and height > 200:
            ocr_score += 1
            assessment_notes.append("✅ Good dimensions for text extraction")
        
        # Determine potential level
        if ocr_score >= 5:
            potential_level = "HIGH"
            section_class = "image-section high-potential"
            score_class = "ocr-assessment high-score"
        elif ocr_score >= 3:
            potential_level = "MEDIUM"
            section_class = "image-section medium-potential"
            score_class = "ocr-assessment medium-score"
        else:
            potential_level = "LOW"
            section_class = "image-section low-potential"
            score_class = "ocr-assessment low-score"
        
        # Create section for this image
        html_content += f"""
            <div class="{section_class}" id="{fig_file}">
                <h2>📊 Image {file_num} - {fig_file}</h2>
                
                <div class="{score_class}">
                    <h3>🎯 OCR Assessment: {potential_level} POTENTIAL (Score: {ocr_score}/6)</h3>
                    <ul>
        """
        
        for note in assessment_notes:
            html_content += f"<li>{note}</li>\n"
        
        html_content += f"""
                    </ul>
                </div>
                
                <div class="image-info">
                    <strong>📏 Image Details:</strong><br>
                    • File Size: {file_size:,} bytes ({file_size/1024:.1f} KB)<br>
                    • Dimensions: {width} × {height} pixels<br>
                    • Aspect Ratio: {aspect_ratio:.2f}<br>
                    • Estimated Content: {"Financial Table" if potential_level == "HIGH" else "Supporting Data" if potential_level == "MEDIUM" else "Header/Label"}
                </div>
                
                <div class="image-container">
                    <img src="{fig_path}" alt="{fig_file}" title="Click to view full size">
                </div>
                
                {"<p><strong>🏆 PRIORITY FOR OCR:</strong> This image has the highest potential for containing the main securities table with prices/valuations!</p>" if potential_level == "HIGH" else ""}
            </div>
        """
    
    html_content += """
            <div class="image-section" style="background: #e8f5e8; border-color: #28a745;">
                <h2>📋 Summary & Next Steps</h2>
                <h3>🎯 OCR Processing Recommendations:</h3>
                <ol>
                    <li><strong>HIGH Priority:</strong> Process images with score ≥5 first</li>
                    <li><strong>MEDIUM Priority:</strong> Review images with score 3-4 manually</li>
                    <li><strong>LOW Priority:</strong> Skip images with score <3 (likely headers/labels)</li>
                </ol>
                
                <h3>💰 Expected Results:</h3>
                <ul>
                    <li>HIGH potential images: Accurate security-price matching</li>
                    <li>MEDIUM potential images: Supporting data, may need validation</li>
                    <li>LOW potential images: Headers, labels, non-tabular content</li>
                </ul>
                
                <h3>🚀 Ready for Phase 2: OCR Processing</h3>
                <p>Based on this analysis, we can now proceed with targeted OCR processing of the most promising images.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save HTML file
    html_file = "image_viewer.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_file

def main():
    """Create and open image viewer"""
    html_file = create_image_viewer()
    
    # Open in browser
    file_path = os.path.abspath(html_file)
    webbrowser.open(f"file://{file_path}")
    print(f"✅ Image viewer created: {html_file}")
    print(f"🌐 Opening in browser...")
    print(f"📁 File location: {file_path}")
    
    # Also show summary in console
    figures_dir = "output_advanced/messos 30.5/figures"
    figure_files = sorted([f for f in os.listdir(figures_dir) if f.endswith('.png')])
    
    print(f"\n📊 **IMAGE ANALYSIS SUMMARY**")
    print(f"=" * 50)
    print(f"Total images extracted: {len(figure_files)}")
    
    high_potential = []
    medium_potential = []
    low_potential = []
    
    for fig_file in figure_files:
        fig_path = os.path.join(figures_dir, fig_file)
        file_size = os.path.getsize(fig_path)
        
        if file_size > 100000:
            high_potential.append(fig_file)
        elif file_size > 2000:
            medium_potential.append(fig_file)
        else:
            low_potential.append(fig_file)
    
    print(f"🏆 HIGH potential (>100KB): {len(high_potential)} images")
    for img in high_potential:
        print(f"   • {img}")
    
    print(f"⚠️ MEDIUM potential (2-100KB): {len(medium_potential)} images")
    print(f"❌ LOW potential (<2KB): {len(low_potential)} images")
    
    print(f"\n🎯 **RECOMMENDATION:**")
    print(f"Start OCR processing with HIGH potential images first!")

if __name__ == "__main__":
    main()
