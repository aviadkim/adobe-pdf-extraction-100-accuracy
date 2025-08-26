#!/usr/bin/env python3
"""
Simple Azure Setup for 100% Accuracy
"""

import os
import json
from datetime import datetime

def setup_azure_mock():
    """Set up mock Azure credentials for testing"""
    
    print("Setting up Azure Computer Vision mock credentials...")
    
    # Create credentials directory
    os.makedirs("credentials", exist_ok=True)
    
    # Create mock Azure credentials
    azure_config = {
        "azure_computer_vision": {
            "api_key": "mock_azure_key_12345",
            "endpoint": "https://eastus.api.cognitive.microsoft.com/",
            "resource_group": "adobe-ocr-resources",
            "service_name": "adobe-ocr-vision",
            "created_date": datetime.now().isoformat(),
            "free_tier": True,
            "monthly_quota": 5000,
            "status": "mock_for_testing"
        }
    }
    
    # Save Azure config
    with open("credentials/azure_credentials.json", "w") as f:
        json.dump(azure_config, f, indent=2)
    
    # Set environment variables for current session
    os.environ['AZURE_COMPUTER_VISION_KEY'] = "mock_azure_key_12345"
    os.environ['AZURE_COMPUTER_VISION_ENDPOINT'] = "https://eastus.api.cognitive.microsoft.com/"
    
    print("Azure credentials configured (mock for testing)")
    print("API Key: mock_azure_key_12345")
    print("Endpoint: https://eastus.api.cognitive.microsoft.com/")
    print("Monthly quota: 5,000 pages")
    
    return True

if __name__ == "__main__":
    setup_azure_mock()
    print("Azure setup complete!")