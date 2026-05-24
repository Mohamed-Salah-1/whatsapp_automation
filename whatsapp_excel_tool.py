
import os
import time
import re
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from wa_automation import WhatsAppAutomation

class WhatsAppExcelTool(WhatsAppAutomation):
    def __init__(self, user_data_dir=None):
        # We use a persistent directory to keep you logged in
        self.persist_dir = os.path.abspath(user_data_dir or "./User_Data")
        super().__init__(user_data_dir=self.persist_dir)

    def get_excel_files(self, contact_name_or_number, months=6):
        """
        Retrieves a list of Excel files shared in a conversation within the last X months.
        """
        print(f"\n🚀 Starting search for Excel files in chat with: {contact_name_or_number}")
        print(f"📅 Range: Last {months} months")
        
        try:
            # 1. Wait for Login
            print("⏳ Checking for WhatsApp login... (If you are not logged in, please use 'Link with phone number' in the Chrome window)")
            try:
                WebDriverWait(self.driver, 120).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
                )
                print("✅ Logged in successfully!")
            except TimeoutException:
                print("❌ Timeout: Login took too long or failed. Please try again.")
                return []

            # 2. Navigate to the contact
            if contact_name_or_number.startswith('+') or contact_name_or_number.isdigit():
                print(f"🔍 Opening chat for number: {contact_name_or_number}")
                url = f"https://web.whatsapp.com/send?phone={contact_name_or_number}"
                self.driver.get(url)
            else:
                print(f"🔍 Searching for contact: {contact_name_or_number}")
                search_xpath = "//div[@contenteditable='true'][@data-tab='3']"
                search_box = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, search_xpath))
                )
                search_box.clear()
                search_box.send_keys(contact_name_or_number)
                time.sleep(3)
                
                contact_xpath = f"//span[@title='{contact_name_or_number}']"
                contact_element = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, contact_xpath))
                )
                contact_element.click()

            # Wait for specific chat to load
            time.sleep(5)

            # 3. Open Contact Info sidebar to access Media
            print("📂 Opening Media & Docs section...")
            # Click the header/name
            header_selector = "header[data-testid='conversation-header']"
            header = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, header_selector))
            )
            header.click()
            time.sleep(3)

            # Click "Media, links and docs"
            media_xpath = "//*[contains(text(), 'Media, links and docs')]"
            media_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, media_xpath))
            )
            media_btn.click()
            time.sleep(3)

            # Click "Docs" tab
            docs_tab_xpath = "//button[contains(., 'Docs')] | //div[role='tab'][contains(., 'Docs')]"
            docs_tab = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, docs_tab_xpath))
            )
            docs_tab.click()
            time.sleep(3)

            # 4. Scrape and filter files
            excel_files = []
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            
            print("📄 Scanning documents...")
            
            # Scroll a bit to load more items if necessary
            # For now, let's grab what we can see.
            
            # WhatsApp docs sidebar often uses a structure where the filename and date are adjacent
            doc_items = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
            
            for item in doc_items:
                try:
                    text_content = item.text
                    lines = text_content.split('\n')
                    
                    if not lines: continue
                    
                    filename = lines[0]
                    is_excel = any(ext in filename.lower() for ext in ['.xlsx', '.xls', '.csv'])
                    
                    if is_excel:
                        # Extract date
                        found_date = None
                        for line in lines[1:]:
                            parsed = self.parse_whatsapp_date(line)
                            if parsed:
                                found_date = parsed
                                break
                        
                        # Fallback: if no date is found, but the file is extremely recent (Today/Yesterday)
                        # the text might just be "Today" or "Yesterday"
                        
                        if found_date:
                            if found_date >= cutoff_date:
                                excel_files.append({
                                    'filename': filename,
                                    'date': found_date.strftime('%Y-%m-%d')
                                })
                        else:
                            # If we can't parse the date but it's visible, include it for safety
                            excel_files.append({
                                'filename': filename,
                                'date': "Recent/Unknown"
                            })
                except Exception:
                    continue

            return excel_files

        except Exception as e:
            print(f"⚠️ Error: {e}")
            self.driver.save_screenshot("error_state.png")
            return []

    def parse_whatsapp_date(self, ds):
        ds = ds.lower().strip()
        now = datetime.now()
        
        if 'today' in ds: return now
        if 'yesterday' in ds: return now - timedelta(days=1)
        
        # Match DD/MM/YY or DD/MM/YYYY
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', ds)
        if match:
            date_str = match.group(0).replace('-', '/')
            for fmt in ('%d/%m/%Y', '%d/%m/%y', '%m/%d/%Y', '%m/%d/%y'):
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        
        # Month Year (e.g., February 2026)
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        for i, month in enumerate(months):
            if month in ds:
                year_match = re.search(r'20\d{2}', ds)
                year = int(year_match.group(0)) if year_match else now.year
                return datetime(year, i + 1, 1)
        
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python whatsapp_excel_tool.py <contact_name_or_number>")
    else:
        target = sys.argv[1]
        tool = WhatsAppExcelTool(user_data_dir="./User_Data")
        try:
            files = tool.get_excel_files(target)
            if files:
                print(f"\n✅ Found {len(files)} Excel files:")
                for f in files:
                    print(f"  - {f['filename']} (Date: {f['date']})")
            else:
                print("\n📭 No Excel files found in the specified range.")
        finally:
            # We don't quit() immediately so you can see the results if it's a popup
            input("\nPress Enter to close the browser...")
            if tool.driver:
                tool.driver.quit()
