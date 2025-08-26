#!/usr/bin/env python3
"""
AZURE API DIRECT ACCESS
Alternative approach: Use Azure REST API directly without portal scraping
"""

import os
import json
import requests
import time
import subprocess
from typing import Dict, Optional

class AzureDirectAPIAccess:
    """Direct Azure API access without portal scraping"""
    
    def __init__(self):
        self.access_token = None
        self.subscription_id = None
        self.tenant_id = None
        
    def get_azure_access_token(self) -> Optional[str]:
        """Get Azure access token using device code flow"""
        
        print("🔑 **AZURE DEVICE CODE AUTHENTICATION**")
        print("=" * 50)
        
        # Azure AD endpoints
        tenant_id = "common"  # Use common for multi-tenant
        client_id = "YOUR_SECRET_HERE"  # Azure CLI client ID
        
        # Step 1: Get device code
        device_code_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/devicecode"
        
        device_code_data = {
            'client_id': client_id,
            'scope': 'https://management.azure.com/.default offline_access'
        }
        
        try:
            print("📱 Getting device code...")
            response = requests.post(device_code_url, data=device_code_data)
            
            if response.status_code != 200:
                print(f"❌ Device code request failed: {response.text}")
                return None
            
            device_info = response.json()
            
            print(f"\n🔗 **PLEASE COMPLETE AUTHENTICATION:**")
            print(f"   1. Go to: {device_info['verification_uri']}")
            print(f"   2. Enter code: {device_info['user_code']}")
            print(f"   3. Sign in with your Azure account")
            print(f"   4. Wait for this script to continue...")
            print()
            
            # Step 2: Poll for token
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            
            token_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': client_id,
                'device_code': device_info['device_code']
            }
            
            # Poll for token
            interval = device_info.get('interval', 5)
            expires_in = device_info.get('expires_in', 900)
            
            for _ in range(expires_in // interval):
                time.sleep(interval)
                
                token_response = requests.post(token_url, data=token_data)
                token_result = token_response.json()
                
                if token_response.status_code == 200:
                    print("✅ Authentication successful!")
                    self.access_token = token_result['access_token']
                    return self.access_token
                
                elif token_result.get('error') == 'authorization_pending':
                    print("⏳ Waiting for authentication...")
                    continue
                
                elif token_result.get('error') == 'slow_down':
                    time.sleep(interval)
                    continue
                
                else:
                    print(f"❌ Authentication failed: {token_result.get('error_description', 'Unknown error')}")
                    return None
            
            print("⏰ Authentication timeout")
            return None
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def get_subscription_id(self) -> Optional[str]:
        """Get Azure subscription ID"""
        
        if not self.access_token:
            return None
        
        try:
            print("📋 Getting subscription ID...")
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            subscriptions_url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
            response = requests.get(subscriptions_url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get subscriptions: {response.text}")
                return None
            
            subscriptions = response.json().get('value', [])
            
            if not subscriptions:
                print("❌ No subscriptions found")
                return None
            
            # Use the first subscription
            subscription = subscriptions[0]
            self.subscription_id = subscription['subscriptionId']
            
            print(f"✅ Using subscription: {subscription['displayName']} ({self.subscription_id})")
            return self.subscription_id
            
        except Exception as e:
            print(f"❌ Error getting subscription: {e}")
            return None
    
    def create_resource_group(self, rg_name: str = "pdf-parser-rg", location: str = "eastus") -> bool:
        """Create Azure resource group"""
        
        if not self.access_token or not self.subscription_id:
            return False
        
        try:
            print(f"🏗️ Creating resource group: {rg_name}")
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            rg_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourcegroups/{rg_name}?api-version=2021-04-01"
            
            rg_data = {
                'location': location,
                'tags': {
                    'purpose': 'pdf-parser',
                    'created-by': 'automation'
                }
            }
            
            response = requests.put(rg_url, headers=headers, json=rg_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Resource group created: {rg_name}")
                return True
            else:
                print(f"❌ Resource group creation failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating resource group: {e}")
            return False
    
    def create_document_intelligence_resource(self, 
                                            resource_name: str = "pdf-parser-di",
                                            rg_name: str = "pdf-parser-rg",
                                            location: str = "eastus") -> Optional[Dict]:
        """Create Document Intelligence resource"""
        
        if not self.access_token or not self.subscription_id:
            return None
        
        try:
            print(f"🧠 Creating Document Intelligence resource: {resource_name}")
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Create the resource
            resource_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.CognitiveServices/accounts/{resource_name}?api-version=2023-05-01"
            
            resource_data = {
                'kind': 'FormRecognizer',
                'location': location,
                'sku': {
                    'name': 'F0'  # Free tier
                },
                'properties': {
                    'customSubDomainName': resource_name
                },
                'tags': {
                    'purpose': 'pdf-parser',
                    'created-by': 'automation'
                }
            }
            
            response = requests.put(resource_url, headers=headers, json=resource_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Document Intelligence resource created: {resource_name}")
                
                # Wait a moment for resource to be ready
                time.sleep(10)
                
                # Get the keys
                return self.get_resource_keys(resource_name, rg_name)
            else:
                print(f"❌ Resource creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating resource: {e}")
            return None
    
    def get_resource_keys(self, resource_name: str, rg_name: str) -> Optional[Dict]:
        """Get API keys for the created resource"""
        
        try:
            print("🔑 Getting API keys...")
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get keys
            keys_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.CognitiveServices/accounts/{resource_name}/listKeys?api-version=2023-05-01"
            
            response = requests.post(keys_url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get keys: {response.text}")
                return None
            
            keys_data = response.json()
            
            # Get endpoint
            resource_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.CognitiveServices/accounts/{resource_name}?api-version=2023-05-01"
            
            resource_response = requests.get(resource_url, headers=headers)
            
            if resource_response.status_code != 200:
                print(f"❌ Failed to get resource details: {resource_response.text}")
                return None
            
            resource_data = resource_response.json()
            endpoint = resource_data['properties']['endpoint']
            
            azure_config = {
                'endpoint': endpoint,
                'key': keys_data['key1'],
                'key2': keys_data['key2'],
                'resource_name': resource_name,
                'resource_group': rg_name,
                'subscription_id': self.subscription_id,
                'location': resource_data['location'],
                'created_via': 'direct_api'
            }
            
            print("✅ API keys retrieved successfully!")
            return azure_config
            
        except Exception as e:
            print(f"❌ Error getting keys: {e}")
            return None
    
    def setup_azure_document_intelligence(self) -> Optional[Dict]:
        """Complete Azure Document Intelligence setup"""
        
        print("🚀 **AZURE DOCUMENT INTELLIGENCE SETUP**")
        print("=" * 50)
        
        # Step 1: Authenticate
        if not self.get_azure_access_token():
            return None
        
        # Step 2: Get subscription
        if not self.get_subscription_id():
            return None
        
        # Step 3: Create resource group
        if not self.create_resource_group():
            return None
        
        # Step 4: Create Document Intelligence resource
        azure_config = self.create_document_intelligence_resource()
        
        if azure_config:
            print(f"\n🎉 **AZURE SETUP COMPLETE!**")
            print(f"📊 **CONFIGURATION:**")
            print(f"   Endpoint: {azure_config['endpoint']}")
            print(f"   Key: {azure_config['key'][:10]}...")
            print(f"   Resource: {azure_config['resource_name']}")
            print(f"   Resource Group: {azure_config['resource_group']}")
            print(f"   Location: {azure_config['location']}")
            
            return azure_config
        else:
            print("\n❌ **AZURE SETUP FAILED**")
            return None


def main():
    """Test Azure direct API access"""
    
    azure_api = AzureDirectAPIAccess()
    
    print("🔗 **AZURE DIRECT API ACCESS**")
    print("=" * 50)
    print("🎯 This will create Azure Document Intelligence using REST API")
    print("📋 You will need to:")
    print("   1. Have an Azure account with subscription")
    print("   2. Complete device code authentication")
    print("   3. Wait for resource creation")
    print()
    
    input("Press Enter to start Azure setup...")
    
    # Setup Azure Document Intelligence
    azure_config = azure_api.setup_azure_document_intelligence()
    
    if azure_config:
        # Save configuration
        config_path = "azure_direct_config.json"
        with open(config_path, 'w') as f:
            json.dump(azure_config, f, indent=2)
        
        print(f"\n📁 Configuration saved to: {config_path}")
        
        # Test the API
        print("\n🧪 Testing the API...")
        test_api(azure_config)
        
        return azure_config
    else:
        print("\n💡 **ALTERNATIVES:**")
        print("   1. Try Azure CLI: az login && az cognitiveservices account create")
        print("   2. Use Azure portal manually")
        print("   3. Continue with Adobe-only parsing")
        
        return None


def test_api(azure_config: Dict):
    """Test the Azure Document Intelligence API"""
    
    try:
        endpoint = azure_config['endpoint']
        key = azure_config['key']
        
        # Test API with a simple call
        test_url = f"{endpoint}/formrecognizer/info?api-version=2023-07-31"
        
        headers = {
            'Ocp-Apim-Subscription-Key': key
        }
        
        response = requests.get(test_url, headers=headers)
        
        if response.status_code == 200:
            print("✅ API test successful!")
            api_info = response.json()
            print(f"   Custom models limit: {api_info.get('customDocumentModels', {}).get('limit', 'N/A')}")
        else:
            print(f"⚠️ API test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")


if __name__ == "__main__":
    main()
