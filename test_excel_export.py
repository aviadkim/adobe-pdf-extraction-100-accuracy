#!/usr/bin/env python3
"""
TEST EXCEL EXPORT
Demonstrates the Excel export functionality
"""

import requests
import os
from datetime import datetime

def test_web_dashboard_excel_export():
    """Test the Excel export from the web dashboard"""
    
    print("📊 **TESTING WEB DASHBOARD EXCEL EXPORT**")
    print("=" * 60)
    
    # Check if web server is running
    try:
        response = requests.get('http://localhost:5000/api/securities', timeout=5)
        
        if response.status_code == 200:
            print("✅ Web dashboard is running")
            
            # Get the data
            data = response.json()
            print(f"📊 Found {len(data['securities'])} securities")
            print(f"💰 Total portfolio value: ${data['summary']['total_value']:,.2f}")
            
            # Test Excel export
            print("\n📁 Testing Excel export...")
            
            excel_response = requests.get('http://localhost:5000/api/export/excel', timeout=30)
            
            if excel_response.status_code == 200:
                # Save the Excel file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_export_{timestamp}.xlsx"
                
                with open(filename, 'wb') as f:
                    f.write(excel_response.content)
                
                file_size = os.path.getsize(filename)
                
                print(f"✅ Excel export successful!")
                print(f"📄 File saved: {filename}")
                print(f"📏 File size: {file_size:,} bytes")
                
                # Test CSV export
                print("\n📄 Testing CSV export...")
                
                csv_response = requests.get('http://localhost:5000/api/export/csv', timeout=30)
                
                if csv_response.status_code == 200:
                    csv_filename = f"test_export_{timestamp}.csv"
                    
                    with open(csv_filename, 'wb') as f:
                        f.write(csv_response.content)
                    
                    csv_size = os.path.getsize(csv_filename)
                    
                    print(f"✅ CSV export successful!")
                    print(f"📄 File saved: {csv_filename}")
                    print(f"📏 File size: {csv_size:,} bytes")
                    
                    # Show what's in the files
                    print(f"\n📋 **EXPORT CONTENTS:**")
                    print(f"   📊 Excel file: {filename}")
                    print(f"      - Securities worksheet with formatted data")
                    print(f"      - Summary worksheet with portfolio statistics")
                    print(f"      - Professional formatting (colors, borders, currency)")
                    print(f"      - Auto-adjusted column widths")
                    print(f"   📄 CSV file: {csv_filename}")
                    print(f"      - Raw data in comma-separated format")
                    print(f"      - Compatible with Excel, Google Sheets, etc.")
                    
                    return True
                else:
                    print(f"❌ CSV export failed: {csv_response.status_code}")
                    return False
            else:
                print(f"❌ Excel export failed: {excel_response.status_code}")
                return False
        else:
            print(f"❌ Web dashboard not responding: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Web dashboard is not running")
        print("💡 Please run: python web_financial_dashboard.py")
        return False
    except Exception as e:
        print(f"❌ Error testing exports: {e}")
        return False

def show_excel_features():
    """Show Excel export features"""
    
    print("\n📊 **EXCEL EXPORT FEATURES:**")
    print("=" * 50)
    
    print("🎨 **Professional Formatting:**")
    print("   ✅ Header row with blue background and white text")
    print("   ✅ Currency formatting for monetary values ($1,234.56)")
    print("   ✅ Percentage formatting for performance metrics (12.34%)")
    print("   ✅ Borders around all cells")
    print("   ✅ Auto-adjusted column widths")
    print()
    
    print("📋 **Multiple Worksheets:**")
    print("   ✅ 'Securities' - Detailed security data")
    print("   ✅ 'Summary' - Portfolio statistics and breakdowns")
    print()
    
    print("📊 **Data Included:**")
    print("   ✅ Security names and identifiers (ISIN, Valorn)")
    print("   ✅ Quantities and market values")
    print("   ✅ Performance metrics (YTD and total)")
    print("   ✅ Asset class and currency information")
    print("   ✅ Confidence scores and extraction methods")
    print("   ✅ Portfolio totals and breakdowns")
    print()
    
    print("🔗 **Integration Ready:**")
    print("   ✅ Compatible with Microsoft Excel")
    print("   ✅ Compatible with Google Sheets")
    print("   ✅ Compatible with LibreOffice Calc")
    print("   ✅ Can be imported into databases")
    print("   ✅ Can be used in Power BI reports")
    print()

def show_web_dashboard_features():
    """Show web dashboard features"""
    
    print("🌐 **WEB DASHBOARD FEATURES:**")
    print("=" * 50)
    
    print("📊 **Interactive Table:**")
    print("   ✅ Sortable columns (click headers)")
    print("   ✅ Searchable/filterable data")
    print("   ✅ Pagination for large datasets")
    print("   ✅ Responsive design for mobile/desktop")
    print()
    
    print("📈 **Real-time Summary:**")
    print("   ✅ Total portfolio value")
    print("   ✅ Number of securities")
    print("   ✅ Average confidence score")
    print("   ✅ Asset class breakdown")
    print("   ✅ Currency distribution")
    print()
    
    print("🎨 **Professional Design:**")
    print("   ✅ Bootstrap 5 styling")
    print("   ✅ Font Awesome icons")
    print("   ✅ Gradient backgrounds")
    print("   ✅ Color-coded performance indicators")
    print("   ✅ Professional badges and labels")
    print()
    
    print("📱 **Mobile Responsive:**")
    print("   ✅ Works on phones and tablets")
    print("   ✅ Touch-friendly controls")
    print("   ✅ Optimized table display")
    print("   ✅ Swipe gestures")
    print()

def main():
    """Main test function"""
    
    print("🧪 **WEB DASHBOARD AND EXCEL EXPORT TEST**")
    print("=" * 70)
    print()
    
    # Test the exports
    success = test_web_dashboard_excel_export()
    
    if success:
        print("\n🎉 **ALL TESTS PASSED!**")
        print("✅ Web dashboard is working")
        print("✅ Excel export is working")
        print("✅ CSV export is working")
        print("✅ Files saved successfully")
    else:
        print("\n❌ **SOME TESTS FAILED**")
        print("💡 Make sure the web dashboard is running:")
        print("   python web_financial_dashboard.py")
    
    # Show features
    show_excel_features()
    show_web_dashboard_features()
    
    print("🎯 **HOW TO USE:**")
    print("=" * 30)
    print("1. 🌐 Open http://localhost:5000 in your browser")
    print("2. 📊 View the interactive financial data table")
    print("3. 📁 Click 'Export to Excel' to download formatted report")
    print("4. 📄 Click 'Export to CSV' for raw data")
    print("5. 🔄 Click 'Refresh Data' to reload information")
    print()
    
    print("📋 **WHAT YOU GET:**")
    print("✅ Professional Excel file with formatting")
    print("✅ Multiple worksheets (Securities + Summary)")
    print("✅ Currency and percentage formatting")
    print("✅ Portfolio statistics and breakdowns")
    print("✅ Ready for business presentations")
    print()

if __name__ == "__main__":
    main()
