#!/usr/bin/env python3
"""
AUTOMATED AZURE SETUP FOR 100% ACCURACY
Creates Azure Computer Vision resource automatically and sets up credentials
"""

import os
import json
import requests
import subprocess
import time
from datetime import datetime

class AutomatedAzureSetup:
    """Automated Azure Computer Vision setup"""
    
    def __init__(self):
        self.subscription_id = None
        self.resource_group = "adobe-ocr-resources"
        self.location = "eastus"
        self.service_name = "adobe-ocr-vision"
        
    def check_azure_cli(self):
        """Check if Azure CLI is installed"""
        try:
            result = subprocess.run(['az', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Azure CLI found!")
                return True
        except FileNotFoundError:
            pass
            
        print("❌ Azure CLI not found. Installing...")
        return self.install_azure_cli()
    
    def install_azure_cli(self):
        """Install Azure CLI automatically"""
        print("🔧 Installing Azure CLI...")
        try:
            # Download and run Azure CLI installer
            installer_url = "https://aka.ms/installazurecliwindows"
            installer_path = "AzureCLI.msi"
            
            print("⬇️ Downloading Azure CLI installer...")
            response = requests.get(installer_url, stream=True)
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("🚀 Running installer (this may take a few minutes)...")
            subprocess.run(['msiexec', '/i', installer_path, '/quiet'], check=True)
            
            # Clean up
            os.remove(installer_path)
            
            print("✅ Azure CLI installed successfully!")
            print("🔄 Please restart your command prompt and run this script again.")
            return False
            
        except Exception as e:
            print(f"❌ Failed to install Azure CLI: {e}")
            print("📋 Please install manually from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows")
            return False
    
    def azure_login(self):
        """Login to Azure"""
        print("🔐 Logging into Azure...")
        try:
            # Check if already logged in
            result = subprocess.run(['az', 'account', 'show'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                account_info = json.loads(result.stdout)
                print(f"✅ Already logged in as: {account_info.get('user', {}).get('name', 'Unknown')}")
                self.subscription_id = account_info.get('id')
                return True
            else:
                # Need to login
                print("🌐 Opening browser for Azure login...")
                subprocess.run(['az', 'login'], check=True)
                
                # Get subscription info
                result = subprocess.run(['az', 'account', 'show'], 
                                      capture_output=True, text=True)
                account_info = json.loads(result.stdout)
                self.subscription_id = account_info.get('id')
                print(f"✅ Logged in successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Azure login failed: {e}")
            return False
    
    def create_resource_group(self):
        """Create resource group for Computer Vision"""
        print(f"📁 Creating resource group: {self.resource_group}")
        try:
            cmd = [
                'az', 'group', 'create',
                '--name', self.resource_group,
                '--location', self.location
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Resource group created!")
                return True
            else:
                # Check if it already exists
                if "already exists" in result.stderr:
                    print("✅ Resource group already exists!")
                    return True
                print(f"❌ Failed to create resource group: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Resource group creation failed: {e}")
            return False
    
    def create_computer_vision_service(self):
        """Create Computer Vision service"""
        print(f"🧠 Creating Computer Vision service: {self.service_name}")
        
        try:
            cmd = [
                'az', 'cognitiveservices', 'account', 'create',
                '--name', self.service_name,
                '--resource-group', self.resource_group,
                '--kind', 'ComputerVision',
                '--sku', 'F0',  # Free tier
                '--location', self.location,
                '--custom-domain', self.service_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Computer Vision service created!")
                return True
            else:
                if "already exists" in result.stderr or "AlreadyExists" in result.stderr:
                    print("✅ Computer Vision service already exists!")
                    return True
                print(f"❌ Failed to create service: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Service creation failed: {e}")
            return False
    
    def get_credentials(self):
        """Get API key and endpoint"""
        print("🔑 Getting API credentials...")
        
        try:
            # Get API key
            cmd = [
                'az', 'cognitiveservices', 'account', 'keys', 'list',
                '--name', self.service_name,
                '--resource-group', self.resource_group
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to get API keys: {result.stderr}")
                return None, None
            
            keys = json.loads(result.stdout)
            api_key = keys['key1']
            
            # Get endpoint
            cmd = [
                'az', 'cognitiveservices', 'account', 'show',
                '--name', self.service_name,
                '--resource-group', self.resource_group
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to get endpoint: {result.stderr}")
                return None, None
            
            account_info = json.loads(result.stdout)
            endpoint = account_info['properties']['endpoint']
            
            print("✅ Credentials retrieved!")
            return api_key, endpoint
            
        except Exception as e:
            print(f"❌ Failed to get credentials: {e}")
            return None, None
    
    def save_credentials(self, api_key, endpoint):
        """Save credentials to environment and config file"""
        print("💾 Saving credentials...")
        
        # Save to environment variables
        os.environ['AZURE_COMPUTER_VISION_KEY'] = api_key
        os.environ['AZURE_COMPUTER_VISION_ENDPOINT'] = endpoint
        
        # Create credentials directory
        creds_dir = "credentials"
        os.makedirs(creds_dir, exist_ok=True)
        
        # Save to config file
        config = {
            "azure_computer_vision": {
                "api_key": api_key,
                "endpoint": endpoint,
                "resource_group": self.resource_group,
                "service_name": self.service_name,
                "subscription_id": self.subscription_id,
                "created_date": datetime.now().isoformat(),
                "free_tier": True,
                "monthly_quota": 5000
            }
        }
        
        with open(f"{creds_dir}/azure_credentials.json", "w") as f:
            json.dump(config, f, indent=2)
        
        # Create batch file to set environment variables permanently
        batch_content = f"""@echo off
echo Setting Azure Computer Vision credentials...
setx AZURE_COMPUTER_VISION_KEY "{api_key}"
setx AZURE_COMPUTER_VISION_ENDPOINT "{endpoint}"
echo Credentials set! Please restart your command prompt.
pause
"""
        
        with open("set_azure_credentials.bat", "w") as f:
            f.write(batch_content)
        
        print("✅ Credentials saved!")
        print(f"📝 API Key: {api_key[:20]}...")
        print(f"🌐 Endpoint: {endpoint}")
        print("💡 Run 'set_azure_credentials.bat' to set permanently")
        
    def setup_complete(self):
        """Complete Azure setup process"""
        print("\n" + "="*60)
        print("🚀 AUTOMATED AZURE COMPUTER VISION SETUP")
        print("="*60)
        
        # Step 1: Check Azure CLI
        if not self.check_azure_cli():
            return False
        
        # Step 2: Login to Azure
        if not self.azure_login():
            return False
        
        # Step 3: Create resource group
        if not self.create_resource_group():
            return False
        
        # Step 4: Create Computer Vision service
        if not self.create_computer_vision_service():
            return False
        
        # Step 5: Get credentials
        api_key, endpoint = self.get_credentials()
        if not api_key or not endpoint:
            return False
        
        # Step 6: Save credentials
        self.save_credentials(api_key, endpoint)
        
        print("\n" + "="*60)
        print("🎉 AZURE COMPUTER VISION SETUP COMPLETE!")
        print("="*60)
        print("✅ Free tier: 5,000 transactions/month")
        print("✅ API Key configured")
        print("✅ Endpoint configured")
        print("✅ Ready for hybrid Adobe + Azure extraction")
        print("="*60)
        
        return True

def main():
    """Run automated Azure setup"""
    setup = AutomatedAzureSetup()
    success = setup.setup_complete()
    
    if success:
        print("🎯 Next step: Run 'python production_100_accuracy.py' to test!")
    else:
        print("❌ Setup failed. Check the errors above.")

if __name__ == "__main__":
    main()