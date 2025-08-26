#!/usr/bin/env python3
"""
Configuration management for Adobe PDF Extract API project
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for PDF extraction settings"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "credentials": {
            "path": "credentials/pdfservices-api-credentials.json",
            "required_fields": [
                "client_credentials",
                "service_account_credentials"
            ]
        },
        "extraction": {
            "default_output_dir": "output",
            "default_table_format": "csv",
            "supported_formats": ["csv", "xlsx"],
            "extract_text_by_default": True,
            "max_file_size_mb": 100
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s"
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Optional path to custom config file
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                custom_config = json.load(f)
                self._merge_config(self.config, custom_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _merge_config(self, base: Dict[str, Any], custom: Dict[str, Any]):
        """Recursively merge custom config into base config"""
        for key, value in custom.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'extraction.default_output_dir')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def validate_credentials(self, credentials_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Adobe PDF Services API credentials
        
        Args:
            credentials_path: Optional custom path to credentials file
            
        Returns:
            Validation result dictionary
        """
        cred_path = credentials_path or self.get('credentials.path')
        
        result = {
            "valid": False,
            "path": cred_path,
            "errors": []
        }
        
        # Check if file exists
        if not os.path.exists(cred_path):
            result["errors"].append(f"Credentials file not found: {cred_path}")
            return result
        
        # Check file content
        try:
            with open(cred_path, 'r') as f:
                creds = json.load(f)
            
            # Validate required fields
            required_fields = self.get('credentials.required_fields', [])
            for field in required_fields:
                if field not in creds:
                    result["errors"].append(f"Missing required field: {field}")
            
            # Additional validation
            if "client_credentials" in creds:
                client_creds = creds["client_credentials"]
                if not client_creds.get("client_id"):
                    result["errors"].append("Missing client_id in client_credentials")
                if not client_creds.get("client_secret"):
                    result["errors"].append("Missing client_secret in client_credentials")
            
            if not result["errors"]:
                result["valid"] = True
                result["client_id"] = creds.get("client_credentials", {}).get("client_id", "")[:8] + "..."
                
        except json.JSONDecodeError:
            result["errors"].append("Invalid JSON format in credentials file")
        except Exception as e:
            result["errors"].append(f"Error reading credentials: {str(e)}")
        
        return result
    
    def get_extraction_settings(self) -> Dict[str, Any]:
        """Get extraction-related settings"""
        return self.get('extraction', {})
    
    def is_valid_table_format(self, format_name: str) -> bool:
        """Check if table format is supported"""
        supported = self.get('extraction.supported_formats', [])
        return format_name.lower() in supported


# Global config instance
config = Config()


def validate_environment() -> Dict[str, Any]:
    """
    Validate the entire environment setup
    
    Returns:
        Environment validation result
    """
    result = {
        "valid": True,
        "checks": {},
        "errors": []
    }
    
    # Check credentials
    cred_result = config.validate_credentials()
    result["checks"]["credentials"] = cred_result
    if not cred_result["valid"]:
        result["valid"] = False
        result["errors"].extend(cred_result["errors"])
    
    # Check required directories
    directories = ["credentials", "input_pdfs", "output"]
    for directory in directories:
        exists = os.path.exists(directory)
        result["checks"][f"directory_{directory}"] = {
            "exists": exists,
            "path": directory
        }
        if not exists:
            result["errors"].append(f"Required directory missing: {directory}")
    
    # Check Python dependencies
    try:
        import adobe.pdfservices.operation
        result["checks"]["adobe_sdk"] = {"installed": True}
    except ImportError:
        result["checks"]["adobe_sdk"] = {"installed": False}
        result["valid"] = False
        result["errors"].append("Adobe PDF Services SDK not installed")
    
    return result


if __name__ == "__main__":
    """CLI for configuration validation"""
    import sys
    
    print("🔍 Validating environment...")
    
    validation = validate_environment()
    
    print(f"\n📋 Validation Results:")
    print(f"Overall Status: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
    
    print(f"\n📁 Directory Checks:")
    for check_name, check_result in validation["checks"].items():
        if check_name.startswith("directory_"):
            dir_name = check_name.replace("directory_", "")
            status = "✅" if check_result["exists"] else "❌"
            print(f"  {status} {dir_name}/")
    
    print(f"\n🔑 Credentials Check:")
    cred_check = validation["checks"].get("credentials", {})
    if cred_check.get("valid"):
        print(f"  ✅ Valid credentials found")
        print(f"  📄 Client ID: {cred_check.get('client_id', 'N/A')}")
    else:
        print(f"  ❌ Invalid or missing credentials")
        for error in cred_check.get("errors", []):
            print(f"     • {error}")
    
    print(f"\n📦 Dependencies Check:")
    sdk_check = validation["checks"].get("adobe_sdk", {})
    status = "✅" if sdk_check.get("installed") else "❌"
    print(f"  {status} Adobe PDF Services SDK")
    
    if validation["errors"]:
        print(f"\n❌ Issues found:")
        for error in validation["errors"]:
            print(f"  • {error}")
        
        print(f"\n💡 Next steps:")
        print(f"  1. Run: python setup.py")
        print(f"  2. Download credentials from Adobe Developer Console")
        print(f"  3. Place credentials in: credentials/pdfservices-api-credentials.json")
    else:
        print(f"\n🎉 Environment is ready!")
        print(f"  You can now run: python pdf_extractor.py <your_pdf_file>")
    
    sys.exit(0 if validation["valid"] else 1)
