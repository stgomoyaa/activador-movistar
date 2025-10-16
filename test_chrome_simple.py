from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configurar Chrome headless
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Usar webdriver-manager para descargar ChromeDriver compatible
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Probar navegación
driver.get("https://www.google.com")
print(f"✅ Chrome funcionando - Título: {driver.title}")
driver.quit()
print("✅ Test exitoso")
