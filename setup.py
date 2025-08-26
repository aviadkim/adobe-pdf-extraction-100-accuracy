#!/usr/bin/env python3
"""
Setup script for Adobe PDF Extract API project
"""

import subprocess
import sys
import os

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    if not os.path.exists('venv'):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    if os.name == 'nt':  # Windows
        pip_path = os.path.join('venv', 'Scripts', 'pip')
    else:  # Unix/Linux/macOS
        pip_path = os.path.join('venv', 'bin', 'pip')
    
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
    print("✅ Requirements installed")

def check_credentials():
    """Check if credentials file exists"""
    cred_path = os.path.join('credentials', 'pdfservices-api-credentials.json')
    if os.path.exists(cred_path):
        print("✅ Credentials file found")
        return True
    else:
        print("⚠️  Credentials file not found")
        print("Please download your credentials from Adobe Developer Console")
        print(f"and place them at: {cred_path}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Adobe PDF Extract API project...")
    
    try:
        create_virtual_environment()
        install_requirements()
        check_credentials()
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Download credentials from Adobe Developer Console")
        print("2. Place pdfservices-api-credentials.json in the credentials/ folder")
        print("3. Run: python pdf_extractor.py --help")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
