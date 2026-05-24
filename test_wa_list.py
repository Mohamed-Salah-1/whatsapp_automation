
import time
import os
from wa_automation import WhatsAppAutomation

def test():
    print("Initializing WhatsApp...")
    # Use User_Data to keep session
    tool = WhatsAppAutomation(user_data_dir="./User_Data")
    
    try:
        print("Waiting for load...")
        time.sleep(15) 
        
        # Take a screenshot to see what's happening
        tool.driver.save_screenshot("wa_test.png")
        print("Screenshot saved to wa_test.png")
        
        # Check if we can see the chat list
        try:
            chat_list = tool.driver.find_elements("css selector", "div[aria-label='Chat list']")
            if chat_list:
                print("Successfully found Chat List!")
            else:
                print("Chat list not found yet.")
        except Exception as e:
            print(f"Error checking chat list: {e}")
            
    finally:
        if tool.driver:
            tool.driver.quit()

if __name__ == "__main__":
    test()
