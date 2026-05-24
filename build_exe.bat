@echo off
REM Build WhatsApp Sender GUI into a single .exe
REM
REM Prerequisites:
REM   pip install pyinstaller selenium webdriver-manager
REM
REM Then run this batch file.

pyinstaller --onefile --windowed --name "WhatsApp_Sender" whatsapp_sender_gui.py

echo.
echo Done! The .exe is at: dist\WhatsApp_Sender.exe
pause
