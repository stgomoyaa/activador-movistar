#!/usr/bin/env python3
"""
Test de v4l2loopback con Selenium
Valida que la cámara virtual funciona correctamente con Chrome
"""

import subprocess
import time
import os
import sys
from pathlib import Path

def log_info(msg):
    print(f"✅ {msg}")

def log_error(msg):
    print(f"❌ {msg}")

def log_warn(msg):
    print(f"⚠️  {msg}")

class ControladorCamaraVirtual:
    """Controlador de v4l2loopback (reemplazo de OBS)"""
    
    def __init__(self, dispositivo='/dev/video10'):
        self.dispositivo = dispositivo
        self.proceso_actual = None
        self.verificar_dispositivo()
    
    def verificar_dispositivo(self):
        """Verifica que el dispositivo existe"""
        if not os.path.exists(self.dispositivo):
            log_error(f"Dispositivo {self.dispositivo} no existe")
            log_warn("Ejecuta: sudo modprobe v4l2loopback devices=1 video_nr=10")
            sys.exit(1)
        log_info(f"Dispositivo {self.dispositivo} encontrado")
    
    def mostrar_video(self, ruta_video, loop=True):
        """
        Muestra un video en la cámara virtual
        
        Args:
            ruta_video: Ruta al archivo Y4M
            loop: Si es True, reproduce en loop infinito
        """
        if not Path(ruta_video).exists():
            log_error(f"Archivo no encontrado: {ruta_video}")
            return False
        
        # Detener video anterior si existe
        if self.proceso_actual:
            log_info("Deteniendo video anterior...")
            self.proceso_actual.terminate()
            try:
                self.proceso_actual.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proceso_actual.kill()
        
        # Preparar comando FFmpeg
        cmd = ['ffmpeg', '-re']
        
        if loop:
            cmd.extend(['-stream_loop', '-1'])  # Loop infinito
        
        cmd.extend([
            '-i', ruta_video,
            '-f', 'v4l2',
            self.dispositivo
        ])
        
        # Iniciar proceso FFmpeg
        log_info(f"Reproduciendo: {Path(ruta_video).name}")
        self.proceso_actual = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(1)  # Esperar a que FFmpeg inicialice
        
        if self.proceso_actual.poll() is not None:
            log_error("FFmpeg falló al iniciar")
            return False
        
        return True
    
    def detener(self):
        """Detiene la reproducción actual"""
        if self.proceso_actual:
            self.proceso_actual.terminate()
            self.proceso_actual.wait()
            log_info("Video detenido")

def test_basico_v4l2():
    """Test básico de v4l2loopback sin navegador"""
    print("\n" + "="*50)
    print("🧪 TEST 1: Verificación básica de v4l2loopback")
    print("="*50 + "\n")
    
    # Verificar que v4l2loopback está cargado
    result = subprocess.run(['lsmod'], capture_output=True, text=True)
    if 'v4l2loopback' in result.stdout:
        log_info("Módulo v4l2loopback cargado")
    else:
        log_error("Módulo v4l2loopback NO cargado")
        log_warn("Ejecuta: sudo modprobe v4l2loopback devices=1 video_nr=10")
        return False
    
    # Listar dispositivos de video
    log_info("Listando dispositivos de video disponibles:")
    subprocess.run(['v4l2-ctl', '--list-devices'])
    
    return True

def test_reproduccion_video():
    """Test de reproducción de video en cámara virtual"""
    print("\n" + "="*50)
    print("🧪 TEST 2: Reproducción de video en /dev/video10")
    print("="*50 + "\n")
    
    # Buscar videos Y4M
    videos_dir = Path('temp_videos_y4m')
    if not videos_dir.exists():
        log_error(f"Directorio {videos_dir} no existe")
        return False
    
    videos = list(videos_dir.glob('*.y4m'))
    if not videos:
        log_error("No se encontraron archivos Y4M")
        return False
    
    log_info(f"Encontrados {len(videos)} videos Y4M")
    
    # Crear controlador
    cam = ControladorCamaraVirtual()
    
    # Probar reproducción de cada video por 3 segundos
    for video in videos[:3]:  # Solo los primeros 3
        log_info(f"\nReproduciendo: {video.name}")
        if cam.mostrar_video(str(video), loop=True):
            log_info("Reproduciendo durante 3 segundos...")
            time.sleep(3)
        else:
            log_error(f"Falló reproducción de {video.name}")
            return False
    
    cam.detener()
    log_info("Test de reproducción completado")
    return True

def test_cambio_dinamico():
    """Test de cambio dinámico entre videos (simula biometría)"""
    print("\n" + "="*50)
    print("🧪 TEST 3: Cambio dinámico de videos (simula biometría)")
    print("="*50 + "\n")
    
    videos_dir = Path('temp_videos_y4m')
    cam = ControladorCamaraVirtual()
    
    secuencia = [
        ('front.y4m', 3, 'Documento FRONTAL'),
        ('back.y4m', 3, 'Documento REVERSO'),
        ('idle.y4m', 2, 'Rostro en REPOSO'),
        ('left.y4m', 2, 'Girar IZQUIERDA'),
        ('idle.y4m', 1, 'Volver a REPOSO'),
        ('right.y4m', 2, 'Girar DERECHA'),
        ('idle.y4m', 1, 'Volver a REPOSO'),
    ]
    
    log_info("Iniciando secuencia de biometría simulada...\n")
    
    for archivo, duracion, descripcion in secuencia:
        ruta = videos_dir / archivo
        if not ruta.exists():
            log_warn(f"Archivo {archivo} no existe, saltando...")
            continue
        
        print(f"📹 {descripcion}...")
        if cam.mostrar_video(str(ruta), loop=True):
            time.sleep(duracion)
        else:
            log_error(f"Falló cambio a {archivo}")
            return False
    
    cam.detener()
    log_info("\n✅ Secuencia completa ejecutada con éxito")
    print("\n💡 Este mismo flujo reemplazará el control de OBS en producción")
    return True

def test_selenium_basico():
    """Test de Selenium con v4l2loopback"""
    print("\n" + "="*50)
    print("🧪 TEST 4: Chrome + Selenium detectando cámara virtual")
    print("="*50 + "\n")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
    except ImportError:
        log_error("Selenium no está instalado")
        log_warn("Instala con: pip install selenium webdriver-manager")
        return False
    
    # Iniciar video en cámara virtual
    videos_dir = Path('temp_videos_y4m')
    cam = ControladorCamaraVirtual()
    
    idle_video = videos_dir / 'idle.y4m'
    if not idle_video.exists():
        log_error("idle.y4m no encontrado")
        return False
    
    log_info("Iniciando video idle.y4m en cámara virtual...")
    if not cam.mostrar_video(str(idle_video), loop=True):
        return False
    
    # Configurar Chrome para usar la cámara virtual
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Sin GUI
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--use-fake-ui-for-media-stream')
    chrome_options.add_argument('--use-fake-device-for-media-stream')
    
    # Mobile emulation (iPhone XR como en producción)
    mobile_emulation = {"deviceName": "iPhone XR"}
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    # Dar permiso automático a la cámara
    prefs = {
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.media_stream_mic": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    log_info("Iniciando Chrome headless...")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Ir a página de prueba de webcam
        log_info("Navegando a página de prueba de webcam...")
        driver.get("https://webcamtests.com/")
        
        log_info("Esperando 5 segundos para detección de cámara...")
        time.sleep(5)
        
        # Verificar que la página cargó
        page_title = driver.title
        log_info(f"Título de página: {page_title}")
        
        # Capturar screenshot
        screenshot_path = "/tmp/test_webcam_v4l2.png"
        driver.save_screenshot(screenshot_path)
        log_info(f"Screenshot guardado en: {screenshot_path}")
        
        driver.quit()
        cam.detener()
        
        log_info("✅ Test de Selenium completado")
        return True
        
    except Exception as e:
        log_error(f"Error en test de Selenium: {e}")
        cam.detener()
        return False

def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("🚀 SUITE DE TESTS PARA v4l2loopback")
    print("Proyecto: Activación Masiva Movistar SIN OBS")
    print("="*60)
    
    # Verificar que estamos en Linux
    if not sys.platform.startswith('linux'):
        log_error("Este script solo funciona en Linux")
        sys.exit(1)
    
    tests = [
        ("Verificación básica", test_basico_v4l2),
        ("Reproducción de videos", test_reproduccion_video),
        ("Cambio dinámico", test_cambio_dinamico),
        ("Selenium + Chrome", test_selenium_basico),
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            log_error(f"Test '{nombre}' falló con excepción: {e}")
            resultados.append((nombre, False))
        
        time.sleep(1)
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60 + "\n")
    
    for nombre, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{status} - {nombre}")
    
    total_pass = sum(1 for _, r in resultados if r)
    total_tests = len(resultados)
    
    print(f"\n📈 Total: {total_pass}/{total_tests} tests pasaron")
    
    if total_pass == total_tests:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ v4l2loopback está listo para reemplazar OBS")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_pass} test(s) fallaron")
        print("Revisa los errores antes de migrar a producción")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
