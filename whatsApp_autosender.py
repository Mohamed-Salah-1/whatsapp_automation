from wa_automation import WhatsAppAutomation
import time

# Initialize WhatsApp automation
whatsapp = WhatsAppAutomation()

# Send a message
# whatsapp.send_message("540275803", "Hello from WA-Automation!")  # Done

# Send an image with caption
# whatsapp.send_image("540275803", r"F:\Data Structure and Algorithm\ramadan_careem.jpeg", "رمضان كريم  وكل عام وانتم بخير و ينعاد عليكم وعلى الأهل بالخير والبركة والقبول
# ") # done

# Send a file with caption
whatsapp.send_file("966540275803", "path/to/document.pdf", "Here's the document you requested")

# Send to multiple numbers
numbers = ["966540275803"]
image = r"F:\TC_00088.jpeg"
for number in numbers:
    whatsapp.send_image(number, image,
                        '''
رمضان كريم  وكل عام وانتم بخير و ينعاد عليكم وعلى الأهل بالخير والبركة والقبول"
'''
                        )
    time.sleep(2)

# Clean up when done
whatsapp.cleanup()
print('done')
