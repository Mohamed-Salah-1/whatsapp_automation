
from wa_automation import WhatsAppAutomation
import time
import os

def explore():
    # We use the existing User_Data to avoid QR scan if possible
    # But note that the original cleanup() deletes it. 
    # Let's hope there's something there or we'll have to wait for scan.
    
    # We'll initialize WITHOUT the cleanup at the end for now
    whatsapp = WhatsAppAutomation(user_data_dir="./User_Data")
    
    try:
        # Give it a moment to load
        time.sleep(10)
        
        # Save a screenshot to see where we are
        whatsapp.driver.save_screenshot("whatsapp_initial.png")
        print("Screenshot saved to whatsapp_initial.png")
        
        # Let's try to list some elements to see the structure
        # (This is just for my exploration)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # We don't call cleanup() here to preserve data if we manually scan
        # But we should quit the driver
        if whatsapp.driver:
            whatsapp.driver.quit()

if __name__ == "__main__":
    explore()
