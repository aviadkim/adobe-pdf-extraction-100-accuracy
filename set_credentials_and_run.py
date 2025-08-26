#!/usr/bin/env python3
"""
Set Adobe credentials and run extraction
"""

import os

def main():
    """Set credentials and run extraction"""
    print("🔧 **SETTING UP ADOBE CREDENTIALS**")
    print("=" * 50)
    
    # Set the Client ID we have
    client_id = "YOUR_CLIENT_ID_HERE"
    
    print(f"✅ Client ID: {client_id}")
    print("❓ I need your Client Secret to proceed")
    print()
    print("📋 **Please provide your Adobe Client Secret:**")
    print("(It should be a long string starting with something like 'p1-' or similar)")
    
    client_secret = input("Enter your Adobe Client Secret: ").strip()
    
    if not client_secret:
        print("❌ Client Secret is required")
        return
    
    # Set environment variables
    os.environ['ADOBE_CLIENT_ID'] = client_id
    os.environ['ADOBE_CLIENT_SECRET'] = client_secret
    
    # Update .env file
    env_content = f"""# Adobe PDF Services API Credentials
ADOBE_CLIENT_ID={client_id}
ADOBE_CLIENT_SECRET={client_secret}

# Additional Adobe Information
ADOBE_TECHNICAL_ACCOUNT_ID=39D3229C68A87F4D0A495F9B@techacct.adobe.com
ADOBE_TECHNICAL_ACCOUNT_EMAIL=2f085e5c-dcf1-4061-9019-93ada46a1c4d@techacct.adobe.com
ADOBE_ORGANIZATION_ID=3A3921AE68A87E960A495C07@AdobeOrg
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Credentials saved!")
    
    # Test connection
    print("\n🔄 Testing Adobe API connection...")
    
    try:
        import requests
        
        auth_url = "https://ims-na1.adobelogin.com/ims/token/v1"
        auth_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'openid,AdobeID,read_organizations,additional_info.projectedProductContext'
        }
        
        response = requests.post(auth_url, data=auth_data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Adobe API connection successful!")
            
            # Run the extraction
            print("\n🚀 **RUNNING COMPLETE SECURITIES EXTRACTION**")
            print("⏱️ This will take 1-2 minutes...")
            
            # Import and run our extractor
            from run_adobe_extraction import extract_securities_with_adobe_ocr, display_results
            
            pdf_path = "messos 30.5.pdf"
            if os.path.exists(pdf_path):
                results = extract_securities_with_adobe_ocr(pdf_path, client_id, client_secret)
                
                if results:
                    display_results(results)
                    print("\n🎉 **SUCCESS! Complete securities data extracted!**")
                    print("📊 All securities with prices and valuations are now available")
                else:
                    print("\n❌ Extraction failed")
            else:
                print(f"❌ PDF file not found: {pdf_path}")
                
        else:
            print(f"❌ Adobe API connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
