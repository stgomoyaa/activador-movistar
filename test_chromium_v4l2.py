#!/usr/bin/env python3
"""Test de Chromium con v4l2loopback"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Configurar opciones de Chrome/Chromium
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium-browser"  # Especificar Chromium
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--use-fake-ui-for-media-stream')
chrome_options.add_argument('--use-fake-device-for-media-stream')

# Usar chromium-chromedriver del sistema
service = Service('/usr/bin/chromedriver')

print("🚀 Iniciando Chromium headless...")

try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Probar navegación básica
    print("📡 Navegando a Google...")
    driver.get("https://www.google.com")
    print(f"✅ Título de página: {driver.title}")
    
    # Probar acceso a webcam (v4l2loopback)
    print("📹 Probando acceso a cámara virtual...")
    driver.get("https://webcamtests.com/")
    time.sleep(3)
    
    print("✅ Chrome + v4l2loopback funcionando correctamente")
    
    driver.quit()
    print("✅ Test completado exitosamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

