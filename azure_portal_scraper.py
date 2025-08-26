#!/usr/bin/env python3
"""
AZURE PORTAL WEB SCRAPER
Automatically creates Azure Document Intelligence resource through web scraping
"""

import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import subprocess

class AzurePortalScraper:
    """Scrapes Azure portal to create Document Intelligence resource"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.azure_config = None
        
    def setup_chrome_driver(self):
        """Setup Chrome driver for web scraping"""
        
        print("🔧 Setting up Chrome driver...")
        
        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Try to find Chrome driver
        try:
            # Try different possible locations
            possible_drivers = [
                "chromedriver.exe",
                "C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe",
                "C:\\chromedriver\\chromedriver.exe"
            ]
            
            driver_path = None
            for path in possible_drivers:
                if os.path.exists(path):
                    driver_path = path
                    break
            
            if driver_path:
                self.driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
            else:
                # Try without specifying path (if in PATH)
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.wait = WebDriverWait(self.driver, 30)
            
            # Remove automation detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome driver ready")
            return True
            
        except Exception as e:
            print(f"❌ Chrome driver setup failed: {e}")
            print("💡 Installing ChromeDriver...")
            return self.install_chrome_driver()
    
    def install_chrome_driver(self):
        """Install ChromeDriver automatically"""
        
        try:
            # Install webdriver-manager
            subprocess.run(['pip', 'install', 'webdriver-manager'], check=True)
            
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Remove automation detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ ChromeDriver installed and ready")
            return True
            
        except Exception as e:
            print(f"❌ ChromeDriver installation failed: {e}")
            return False
    
    def scrape_azure_portal_setup(self):
        """Scrape Azure portal to create Document Intelligence resource"""
        
        print("🌐 **AZURE PORTAL WEB SCRAPING**")
        print("=" * 50)
        
        if not self.setup_chrome_driver():
            return None
        
        try:
            # Step 1: Navigate to Azure portal
            print("🔗 Step 1: Navigating to Azure portal...")
            self.driver.get("https://portal.azure.com")
            
            # Wait for login page
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            print("🔑 Please log in to Azure portal manually...")
            print("⏳ Waiting for you to complete login...")
            
            # Wait for user to login manually
            self.wait_for_azure_login()
            
            # Step 2: Create Resource Group
            print("🏗️ Step 2: Creating resource group...")
            rg_created = self.create_resource_group()
            
            if not rg_created:
                print("❌ Resource group creation failed")
                return None
            
            # Step 3: Create Document Intelligence resource
            print("🧠 Step 3: Creating Document Intelligence resource...")
            di_config = self.create_document_intelligence_resource()
            
            if di_config:
                print("✅ Azure Document Intelligence resource created successfully!")
                return di_config
            else:
                print("❌ Document Intelligence resource creation failed")
                return None
                
        except Exception as e:
            print(f"❌ Azure portal scraping failed: {e}")
            return None
        
        finally:
            if self.driver:
                print("🔒 Closing browser...")
                time.sleep(2)
                self.driver.quit()
    
    def wait_for_azure_login(self):
        """Wait for user to complete Azure login"""
        
        # Wait for Azure portal dashboard to load
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check if we're on the Azure dashboard
                if "portal.azure.com" in self.driver.current_url:
                    # Look for dashboard elements
                    dashboard_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "[data-testid='dashboard'], .fxs-portal-dashboard, .azc-dashboard")
                    
                    if dashboard_elements:
                        print("✅ Azure login completed!")
                        time.sleep(3)
                        return True
                
                # Check for "Create a resource" button
                create_resource_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Create a resource')] | //a[contains(text(), 'Create a resource')]")
                
                if create_resource_buttons:
                    print("✅ Azure dashboard loaded!")
                    time.sleep(2)
                    return True
                
                time.sleep(2)
                
            except Exception:
                time.sleep(2)
                continue
        
        print("⏰ Login timeout - please ensure you're logged in")
        return False
    
    def create_resource_group(self):
        """Create Azure resource group"""
        
        try:
            # Navigate to resource groups
            print("📁 Creating resource group...")
            
            # Try multiple ways to find "Create a resource" or "Resource groups"
            try:
                # Method 1: Direct navigation
                self.driver.get("https://portal.azure.com/#create/Microsoft.ResourceGroup")
                time.sleep(5)
            except:
                # Method 2: Search for resource groups
                try:
                    search_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 
                        "input[placeholder*='Search'], input[aria-label*='Search']")))
                    search_box.clear()
                    search_box.send_keys("resource groups")
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(3)
                    
                    # Click on Resource groups
                    rg_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                        "//a[contains(text(), 'Resource groups')] | //span[contains(text(), 'Resource groups')]")))
                    rg_link.click()
                    time.sleep(3)
                    
                    # Click Create
                    create_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(text(), 'Create')] | //a[contains(text(), 'Create')]")))
                    create_button.click()
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"⚠️ Alternative navigation method failed: {e}")
                    return False
            
            # Fill resource group form
            print("📝 Filling resource group form...")
            
            # Resource group name
            try:
                name_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "input[name*='name'], input[id*='name'], input[placeholder*='name']")))
                name_input.clear()
                name_input.send_keys("pdf-parser-rg")
                time.sleep(1)
            except:
                print("⚠️ Could not find resource group name field")
            
            # Select region
            try:
                region_dropdown = self.driver.find_element(By.CSS_SELECTOR, 
                    "select[name*='region'], select[id*='region'], select[name*='location']")
                select = Select(region_dropdown)
                select.select_by_visible_text("East US")
                time.sleep(1)
            except:
                print("⚠️ Could not find region dropdown")
            
            # Click Review + Create
            try:
                review_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'Review + create')] | //button[contains(text(), 'Review + Create')]")))
                review_button.click()
                time.sleep(3)
            except:
                print("⚠️ Could not find Review + Create button")
            
            # Click Create
            try:
                create_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'Create')]")))
                create_button.click()
                time.sleep(5)
                
                print("✅ Resource group creation initiated")
                return True
                
            except:
                print("⚠️ Could not find final Create button")
                return False
                
        except Exception as e:
            print(f"❌ Resource group creation failed: {e}")
            return False
    
    def create_document_intelligence_resource(self):
        """Create Document Intelligence resource"""
        
        try:
            print("🧠 Creating Document Intelligence resource...")
            
            # Navigate to create Document Intelligence
            self.driver.get("https://portal.azure.com/#create/Microsoft.CognitiveServicesFormRecognizer")
            time.sleep(5)
            
            # Fill the form
            print("📝 Filling Document Intelligence form...")
            
            # Resource name
            try:
                name_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "input[name*='name'], input[id*='name']")))
                name_input.clear()
                name_input.send_keys("pdf-parser-di")
                time.sleep(1)
            except:
                print("⚠️ Could not find resource name field")
            
            # Select subscription (usually auto-selected)
            time.sleep(1)
            
            # Select resource group
            try:
                rg_dropdown = self.driver.find_element(By.CSS_SELECTOR, 
                    "select[name*='resourceGroup'], select[id*='resourceGroup']")
                select = Select(rg_dropdown)
                select.select_by_visible_text("pdf-parser-rg")
                time.sleep(1)
            except:
                print("⚠️ Could not find resource group dropdown")
            
            # Select region
            try:
                region_dropdown = self.driver.find_element(By.CSS_SELECTOR, 
                    "select[name*='region'], select[id*='region'], select[name*='location']")
                select = Select(region_dropdown)
                select.select_by_visible_text("East US")
                time.sleep(1)
            except:
                print("⚠️ Could not find region dropdown")
            
            # Select pricing tier (F0 - Free)
            try:
                pricing_dropdown = self.driver.find_element(By.CSS_SELECTOR, 
                    "select[name*='sku'], select[id*='sku'], select[name*='pricing']")
                select = Select(pricing_dropdown)
                select.select_by_value("F0")  # Free tier
                time.sleep(1)
            except:
                print("⚠️ Could not find pricing tier dropdown")
            
            # Click Review + Create
            try:
                review_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'Review + create')] | //button[contains(text(), 'Review + Create')]")))
                review_button.click()
                time.sleep(3)
            except:
                print("⚠️ Could not find Review + Create button")
            
            # Click Create
            try:
                create_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'Create')]")))
                create_button.click()
                time.sleep(10)
                
                print("✅ Document Intelligence resource creation initiated")
                
                # Wait for deployment to complete
                print("⏳ Waiting for deployment to complete...")
                self.wait_for_deployment_completion()
                
                # Get the resource keys and endpoint
                return self.extract_resource_credentials()
                
            except:
                print("⚠️ Could not find final Create button")
                return None
                
        except Exception as e:
            print(f"❌ Document Intelligence creation failed: {e}")
            return None
    
    def wait_for_deployment_completion(self):
        """Wait for Azure deployment to complete"""
        
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Look for deployment completion indicators
                success_elements = self.driver.find_elements(By.XPATH, 
                    "//span[contains(text(), 'deployment is complete')] | " +
                    "//span[contains(text(), 'Deployment succeeded')] | " +
                    "//button[contains(text(), 'Go to resource')]")
                
                if success_elements:
                    print("✅ Deployment completed successfully!")
                    time.sleep(2)
                    return True
                
                time.sleep(5)
                
            except Exception:
                time.sleep(5)
                continue
        
        print("⏰ Deployment timeout - but resource might still be created")
        return False
    
    def extract_resource_credentials(self):
        """Extract API keys and endpoint from the created resource"""
        
        try:
            print("🔑 Extracting API credentials...")
            
            # Click "Go to resource" if available
            try:
                go_to_resource = self.driver.find_element(By.XPATH, 
                    "//button[contains(text(), 'Go to resource')] | //a[contains(text(), 'Go to resource')]")
                go_to_resource.click()
                time.sleep(5)
            except:
                # Navigate to the resource manually
                self.driver.get("https://portal.azure.com/#@/resource/subscriptions/*/resourceGroups/pdf-parser-rg/providers/Microsoft.CognitiveServices/accounts/pdf-parser-di")
                time.sleep(5)
            
            # Navigate to Keys and Endpoint
            try:
                keys_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                    "//a[contains(text(), 'Keys and Endpoint')] | //span[contains(text(), 'Keys and Endpoint')]")))
                keys_link.click()
                time.sleep(3)
            except:
                print("⚠️ Could not find Keys and Endpoint link")
                return None
            
            # Extract endpoint
            endpoint = None
            try:
                endpoint_element = self.driver.find_element(By.CSS_SELECTOR, 
                    "input[readonly][value*='cognitiveservices.azure.com'], " +
                    "span[title*='cognitiveservices.azure.com']")
                endpoint = endpoint_element.get_attribute("value") or endpoint_element.text
            except:
                print("⚠️ Could not find endpoint")
            
            # Extract key
            key = None
            try:
                key_element = self.driver.find_element(By.CSS_SELECTOR, 
                    "input[readonly][name*='key'], input[readonly][id*='key']")
                key = key_element.get_attribute("value")
            except:
                print("⚠️ Could not find API key")
            
            if endpoint and key:
                azure_config = {
                    'endpoint': endpoint,
                    'key': key,
                    'resource_name': 'pdf-parser-di',
                    'resource_group': 'pdf-parser-rg',
                    'created_via': 'web_scraping'
                }
                
                print("✅ API credentials extracted successfully!")
                return azure_config
            else:
                print("❌ Could not extract complete credentials")
                return None
                
        except Exception as e:
            print(f"❌ Credential extraction failed: {e}")
            return None


def main():
    """Test the Azure portal scraper"""
    
    scraper = AzurePortalScraper()
    
    print("🌐 **AZURE PORTAL WEB SCRAPER**")
    print("=" * 50)
    print("🎯 This will automatically create Azure Document Intelligence resource")
    print("📋 You will need to:")
    print("   1. Have an Azure account")
    print("   2. Log in manually when prompted")
    print("   3. Wait for the automation to complete")
    print()
    
    input("Press Enter to start Azure portal scraping...")
    
    # Scrape Azure portal
    azure_config = scraper.scrape_azure_portal_setup()
    
    if azure_config:
        # Save configuration
        config_path = "azure_scraped_config.json"
        with open(config_path, 'w') as f:
            json.dump(azure_config, f, indent=2)
        
        print(f"\n🎉 **AZURE SETUP COMPLETE!**")
        print(f"📊 **CONFIGURATION:**")
        print(f"   Endpoint: {azure_config['endpoint']}")
        print(f"   Key: {azure_config['key'][:10]}...")
        print(f"   Resource: {azure_config['resource_name']}")
        print(f"   Resource Group: {azure_config['resource_group']}")
        print(f"\n📁 Configuration saved to: {config_path}")
        
        return azure_config
    else:
        print("\n❌ **AZURE SETUP FAILED**")
        print("💡 **ALTERNATIVES:**")
        print("   1. Try manual Azure portal setup")
        print("   2. Use Azure CLI after fixing PATH")
        print("   3. Continue with Adobe-only parsing")
        
        return None


if __name__ == "__main__":
    main()
