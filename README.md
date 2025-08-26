# Adobe PDF Extract API - Table Extraction Tool

🚀 **Extract tables and structured data from PDF files using Adobe's powerful PDF Extract API**

This project provides a complete, ready-to-use solution for extracting tables from PDFs with proper error handling, credential management, and organized output.

## 🎯 Features

- ✅ **Table Extraction**: Extract tables in CSV or Excel format
- ✅ **Text Extraction**: Extract formatted text and structure
- ✅ **Batch Processing**: Process multiple PDFs
- ✅ **Secure Credentials**: Safe credential management
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Free Tier**: 500 documents/month with Adobe's free tier

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or download this project
# Navigate to the project directory

# Run the setup script
python setup.py
```

### 2. Get Adobe PDF Services API Credentials

1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
2. Create a new project → PDF Services API → PDF Extract API
3. Download the credentials ZIP file
4. Extract `pdfservices-api-credentials.json` to the `credentials/` folder

### 3. Validate Setup

```bash
# Check if everything is configured correctly
python config.py
```

### 4. Extract Tables from PDF

```bash
# Basic usage
python pdf_extractor.py input_pdfs/your_file.pdf

# Advanced usage with options
python pdf_extractor.py input_pdfs/your_file.pdf \
    --output-dir custom_output \
    --table-format xlsx \
    --no-text
```

## 📁 Project Structure

```
adobe-pdf-extract/
├── credentials/
│   ├── pdfservices-api-credentials.json  ← Your API credentials
│   └── README.md                         ← Credential setup guide
├── input_pdfs/
│   └── your_pdfs_here.pdf               ← Place PDFs to process
├── output/
│   └── extracted_data/                  ← Results saved here
├── pdf_extractor.py                     ← Main extraction script
├── config.py                           ← Configuration & validation
├── setup.py                            ← Environment setup
├── requirements.txt                     ← Python dependencies
└── README.md                           ← This file
```

## 🔧 Usage Examples

### Basic Table Extraction

```bash
# Extract tables as CSV (default)
python pdf_extractor.py input_pdfs/financial_report.pdf
```

**Output:**
```
✅ Extraction successful!
📁 Output directory: output
📋 Extracted files:
  JSON: output/financial_report/structuredData.json
  CSV: output/financial_report/tables/table_1.csv
```

### Excel Format with Custom Output

```bash
# Extract tables as Excel files
python pdf_extractor.py input_pdfs/data_sheet.pdf \
    --table-format xlsx \
    --output-dir results/excel_exports
```

### Tables Only (No Text)

```bash
# Extract only tables, skip text content
python pdf_extractor.py input_pdfs/table_heavy.pdf --no-text
```

## 🐍 Python API Usage

```python
from pdf_extractor import PDFExtractor

# Initialize extractor
extractor = PDFExtractor()

# Extract tables
result = extractor.extract_tables(
    input_pdf_path="input_pdfs/sample.pdf",
    output_dir="output",
    table_format="csv",
    extract_text=True
)

if result["success"]:
    print("✅ Extraction completed!")
    print(f"Files: {result['extracted_files']}")
else:
    print(f"❌ Error: {result['error']}")
```

## 📊 Output Formats

### JSON Structure Data
```json
{
  "elements": [
    {
      "Text": "Table content...",
      "Bounds": [x, y, width, height],
      "Font": {...},
      "Page": 1
    }
  ],
  "tables": [
    {
      "data": [...],
      "headers": [...],
      "page": 1
    }
  ]
}
```

### CSV Tables
- Each table saved as separate CSV file
- Headers preserved
- Clean, structured data ready for analysis

### Excel Tables
- Multiple tables in separate sheets
- Formatting preserved
- Ready for business use

## ⚙️ Configuration

### Environment Variables

Create a `.env` file for custom settings:

```env
ADOBE_CREDENTIALS_PATH=credentials/pdfservices-api-credentials.json
DEFAULT_OUTPUT_DIR=output
DEFAULT_TABLE_FORMAT=csv
LOG_LEVEL=INFO
```

### Custom Configuration

Create `config.json` for advanced settings:

```json
{
  "extraction": {
    "default_table_format": "xlsx",
    "extract_text_by_default": false,
    "max_file_size_mb": 50
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

## 🔍 Troubleshooting

### Common Issues

**❌ "Credentials file not found"**
```bash
# Solution: Download credentials from Adobe Developer Console
# Place pdfservices-api-credentials.json in credentials/ folder
```

**❌ "Adobe PDF Services SDK not installed"**
```bash
# Solution: Install the SDK
pip install pdfservices-sdk
```

**❌ "Invalid JSON format in credentials file"**
```bash
# Solution: Validate your credentials file
python config.py
```

### Validation Commands

```bash
# Check entire environment
python config.py

# Test with sample PDF
python pdf_extractor.py --help

# Verify dependencies
pip list | grep pdfservices
```

## 💰 Pricing & Limits

### Free Tier
- **500 documents/month** - Perfect for testing
- All features included
- No credit card required

### Paid Plans
- **Volume discounts** available
- **Enterprise features** for high-volume usage
- **Priority support**

## 🔗 Useful Links

- [Adobe PDF Extract API Documentation](https://developer.adobe.com/document-services/docs/overview/pdf-extract-api/)
- [Adobe Developer Console](https://developer.adobe.com/console)
- [PDF Services SDK Documentation](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎉 Ready to extract tables from your PDFs? Start with the Quick Start guide above!**
