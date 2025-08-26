#!/usr/bin/env python3
"""
Unit tests for configuration management
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open
from pathlib import Path

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import Config, validate_environment
from exceptions import CredentialsNotFoundError, InvalidCredentialsFormatError


class TestConfig:
    """Test cases for Config class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.get('extraction.default_output_dir') == 'output'
        assert config.get('extraction.max_file_size_mb') == 100
        assert config.get('logging.level') == 'INFO'
        assert config.get('nonexistent.key', 'default') == 'default'
    
    def test_get_extraction_settings(self):
        """Test extraction settings retrieval"""
        config = Config()
        settings = config.get_extraction_settings()
        
        assert isinstance(settings, dict)
        assert 'default_output_dir' in settings
        assert 'supported_formats' in settings
        assert settings['extract_text_by_default'] is True
    
    def test_is_valid_table_format(self):
        """Test table format validation"""
        config = Config()
        
        assert config.is_valid_table_format('csv') is True
        assert config.is_valid_table_format('xlsx') is True
        assert config.is_valid_table_format('CSV') is True
        assert config.is_valid_table_format('json') is False
        assert config.is_valid_table_format('invalid') is False
    
    def test_custom_config_loading(self):
        """Test loading custom configuration from file"""
        custom_config = {
            "extraction": {
                "max_file_size_mb": 200,
                "custom_setting": "test_value"
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            config_file = f.name
        
        try:
            config = Config(config_file)
            
            # Test merged values
            assert config.get('extraction.max_file_size_mb') == 200
            assert config.get('extraction.custom_setting') == 'test_value'
            assert config.get('logging.level') == 'DEBUG'
            
            # Test default values still present
            assert config.get('extraction.default_output_dir') == 'output'
        finally:
            os.unlink(config_file)
    
    def test_config_file_not_found(self):
        """Test handling of non-existent config file"""
        config = Config('nonexistent_config.json')
        # Should not raise exception, just use defaults
        assert config.get('logging.level') == 'INFO'


class TestCredentialsValidation:
    """Test cases for credentials validation"""
    
    @pytest.fixture
    def valid_credentials(self):
        """Valid credentials data"""
        return {
            "client_credentials": {
                "client_id": "test_client_id_12345",
                "client_secret": "test_client_secret_67890"
            },
            "service_account_credentials": {
                "organization_id": "test_org",
                "account_id": "test_account"
            }
        }
    
    @pytest.fixture
    def invalid_credentials_missing_client_id(self):
        """Invalid credentials - missing client_id"""
        return {
            "client_credentials": {
                "client_secret": "test_client_secret_67890"
            },
            "service_account_credentials": {
                "organization_id": "test_org"
            }
        }
    
    def test_validate_credentials_success(self, valid_credentials):
        """Test successful credentials validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_credentials, f)
            cred_file = f.name
        
        try:
            config = Config()
            result = config.validate_credentials(cred_file)
            
            assert result['valid'] is True
            assert result['path'] == cred_file
            assert len(result['errors']) == 0
            assert 'client_id' in result
            assert result['client_id'] == 'test_cli...'
        finally:
            os.unlink(cred_file)
    
    def test_validate_credentials_file_not_found(self):
        """Test credentials validation with missing file"""
        config = Config()
        result = config.validate_credentials('nonexistent_creds.json')
        
        assert result['valid'] is False
        assert 'not found' in result['errors'][0]
    
    def test_validate_credentials_invalid_json(self):
        """Test credentials validation with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content {')
            cred_file = f.name
        
        try:
            config = Config()
            result = config.validate_credentials(cred_file)
            
            assert result['valid'] is False
            assert any('JSON' in error for error in result['errors'])
        finally:
            os.unlink(cred_file)
    
    def test_validate_credentials_missing_fields(self, invalid_credentials_missing_client_id):
        """Test credentials validation with missing required fields"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_credentials_missing_client_id, f)
            cred_file = f.name
        
        try:
            config = Config()
            result = config.validate_credentials(cred_file)
            
            assert result['valid'] is False
            assert any('client_id' in error for error in result['errors'])
        finally:
            os.unlink(cred_file)
    
    def test_validate_credentials_empty_values(self):
        """Test credentials validation with empty values"""
        empty_creds = {
            "client_credentials": {
                "client_id": "",
                "client_secret": "test_secret"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_creds, f)
            cred_file = f.name
        
        try:
            config = Config()
            result = config.validate_credentials(cred_file)
            
            assert result['valid'] is False
            assert any('client_id' in error for error in result['errors'])
        finally:
            os.unlink(cred_file)


class TestEnvironmentValidation:
    """Test cases for environment validation"""
    
    @patch('os.path.exists')
    @patch('config.config.validate_credentials')
    def test_validate_environment_success(self, mock_validate_creds, mock_exists):
        """Test successful environment validation"""
        # Mock successful conditions
        mock_exists.return_value = True
        mock_validate_creds.return_value = {'valid': True, 'errors': []}
        
        with patch('adobe.pdfservices.operation'):
            result = validate_environment()
            
            assert result['valid'] is True
            assert len(result['errors']) == 0
            assert 'credentials' in result['checks']
            assert 'adobe_sdk' in result['checks']
    
    @patch('os.path.exists')
    @patch('config.config.validate_credentials')
    def test_validate_environment_missing_directories(self, mock_validate_creds, mock_exists):
        """Test environment validation with missing directories"""
        # Mock missing directories
        def exists_side_effect(path):
            return path != 'credentials'  # credentials directory missing
        
        mock_exists.side_effect = exists_side_effect
        mock_validate_creds.return_value = {'valid': True, 'errors': []}
        
        with patch('adobe.pdfservices.operation'):
            result = validate_environment()
            
            assert result['valid'] is True  # Missing dirs don't fail validation
            assert 'directory_credentials' in result['checks']
            assert result['checks']['directory_credentials']['exists'] is False
    
    @patch('os.path.exists')
    @patch('config.config.validate_credentials')
    def test_validate_environment_missing_sdk(self, mock_validate_creds, mock_exists):
        """Test environment validation with missing Adobe SDK"""
        mock_exists.return_value = True
        mock_validate_creds.return_value = {'valid': True, 'errors': []}
        
        # Mock ImportError for Adobe SDK
        with patch.dict('sys.modules', {'adobe.pdfservices.operation': None}):
            result = validate_environment()
            
            assert result['valid'] is False
            assert any('Adobe PDF Services SDK' in error for error in result['errors'])
            assert result['checks']['adobe_sdk']['installed'] is False
    
    @patch('os.path.exists')
    @patch('config.config.validate_credentials')
    def test_validate_environment_invalid_credentials(self, mock_validate_creds, mock_exists):
        """Test environment validation with invalid credentials"""
        mock_exists.return_value = True
        mock_validate_creds.return_value = {
            'valid': False,
            'errors': ['Invalid credentials format']
        }
        
        with patch('adobe.pdfservices.operation'):
            result = validate_environment()
            
            assert result['valid'] is False
            assert 'Invalid credentials format' in result['errors']


class TestConfigMerging:
    """Test configuration merging functionality"""
    
    def test_merge_nested_config(self):
        """Test merging of nested configuration dictionaries"""
        base_config = {
            "extraction": {
                "default_output_dir": "output",
                "max_file_size_mb": 100,
                "formats": ["csv", "xlsx"]
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        custom_config = {
            "extraction": {
                "max_file_size_mb": 200,
                "new_setting": "custom_value"
            },
            "new_section": {
                "setting": "value"
            }
        }
        
        config = Config()
        config._merge_config(base_config, custom_config)
        
        # Check merged values
        assert base_config["extraction"]["max_file_size_mb"] == 200
        assert base_config["extraction"]["new_setting"] == "custom_value"
        assert base_config["extraction"]["default_output_dir"] == "output"  # Original preserved
        assert base_config["new_section"]["setting"] == "value"
        assert base_config["logging"]["level"] == "INFO"  # Untouched section preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])