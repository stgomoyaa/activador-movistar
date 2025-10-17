#!/usr/bin/env python3
"""
Activador Masivo Movistar - Versión v4l2loopback (SIN OBS)
Adaptado para usar cámara virtual de Linux en lugar de OBS Studio
"""

VERSION = "1.5"

import atexit
import contextlib
import socket
import tempfile
import time
import threading
import os
import sys
import subprocess
import shutil
import uuid
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


# --- CONFIGURACIÓN ---
class Config:
    LINKS_FILE = "links_extraidos.txt"
    LOG_FILE = "log_activacion_v4l2.txt"

    # Configuración de v4l2loopback
    DISPOSITIVO_VIDEO = "/dev/video10"

    # Videos de biometría (Y4M format)
    VIDEO_IDLE = "temp_videos_y4m/idle.y4m"
    VIDEO_LEFT = "temp_videos_y4m/left.y4m"
    VIDEO_RIGHT = "temp_videos_y4m/right.y4m"
    VIDEO_FRONT = "temp_videos_y4m/front.y4m"
    VIDEO_BACK = "temp_videos_y4m/back.y4m"

    # RUT provisional para activaciones
    RUT_PROVISIONAL = "206486155"

    # Opciones base de Chrome
    CHROME_BASE_OPTIONS = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        "--log-level=3",
    ]

    # Configuración del entorno gráfico para servidores sin interfaz
    XVFB_DISPLAY = os.environ.get("ACTIVADOR_XVFB_DISPLAY", ":99")
    XVFB_SCREEN = os.environ.get("ACTIVADOR_XVFB_SCREEN", "1280x720x24")
    XVFB_EXTRA_ARGS = os.environ.get("ACTIVADOR_XVFB_EXTRA", "-ac").split()

    # Posibles ubicaciones del binario de Chromium/Chrome
    CHROME_BIN_CANDIDATES = [
        os.environ.get("CHROME_BINARY"),
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    # Posibles ubicaciones para chromedriver
    CHROMEDRIVER_CANDIDATES = [
        os.environ.get("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
    ]

    # Configuración del entorno gráfico para servidores sin interfaz
    XVFB_DISPLAY = os.environ.get("ACTIVADOR_XVFB_DISPLAY", ":99")
    XVFB_SCREEN = os.environ.get("ACTIVADOR_XVFB_SCREEN", "1280x720x24")
    XVFB_EXTRA_ARGS = os.environ.get("ACTIVADOR_XVFB_EXTRA", "-ac").split()

    # Posibles ubicaciones del binario de Chromium/Chrome
    CHROME_BIN_CANDIDATES = [
        os.environ.get("CHROME_BINARY"),
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    # Posibles ubicaciones para chromedriver
    CHROMEDRIVER_CANDIDATES = [
        os.environ.get("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
    ]

    # Configuración del entorno gráfico para servidores sin interfaz
    XVFB_DISPLAY = os.environ.get("ACTIVADOR_XVFB_DISPLAY", ":99")
    XVFB_SCREEN = os.environ.get("ACTIVADOR_XVFB_SCREEN", "1280x720x24")
    XVFB_EXTRA_ARGS = os.environ.get("ACTIVADOR_XVFB_EXTRA", "-ac").split()

    # Posibles ubicaciones del binario de Chromium/Chrome
    CHROME_BIN_CANDIDATES = [
        os.environ.get("CHROME_BINARY"),
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    # Posibles ubicaciones para chromedriver
    CHROMEDRIVER_CANDIDATES = [
        os.environ.get("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
    ]

    # Configuración del entorno gráfico para servidores sin interfaz
    XVFB_DISPLAY = os.environ.get("ACTIVADOR_XVFB_DISPLAY", ":99")
    XVFB_SCREEN = os.environ.get("ACTIVADOR_XVFB_SCREEN", "1280x720x24")
    XVFB_EXTRA_ARGS = os.environ.get("ACTIVADOR_XVFB_EXTRA", "-ac").split()

    # Posibles ubicaciones del binario de Chromium/Chrome
    CHROME_BIN_CANDIDATES = [
        os.environ.get("CHROME_BINARY"),
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    # Posibles ubicaciones para chromedriver
    CHROMEDRIVER_CANDIDATES = [
        os.environ.get("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
    ]

    # Configuración del entorno gráfico para servidores sin interfaz
    XVFB_DISPLAY = os.environ.get("ACTIVADOR_XVFB_DISPLAY", ":99")
    XVFB_SCREEN = os.environ.get("ACTIVADOR_XVFB_SCREEN", "1280x720x24")
    XVFB_EXTRA_ARGS = os.environ.get("ACTIVADOR_XVFB_EXTRA", "-ac").split()

    # Posibles ubicaciones del binario de Chromium/Chrome
    CHROME_BIN_CANDIDATES = [
        os.environ.get("CHROME_BINARY"),
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    # Posibles ubicaciones para chromedriver
    CHROMEDRIVER_CANDIDATES = [
        os.environ.get("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
    ]

    # Tiempos
    TIMEOUT_PAGINA = 60
    PAUSA_ENTRE_ACTIVACIONES = 3
    TIEMPO_ESPERA_BIOMETRIA = 400  # Aumentado para dar más tiempo


class Locators:
    """Selectores de elementos web para mantenerlos organizados."""

    RUT_INPUT = (By.ID, "rut")
    RUT_BUTTON = (By.ID, "rut-button")
    CONTINUAR_BYPASS_BTN = (
        By.XPATH,
        "//*[(self::a or self::button) and contains(., 'Continuar')]",
    )
    TERMS_CHECKBOX = (By.ID, "checkTyc")
    INICIAR_BTN = (By.ID, "next")
    EMPEZAR_VERIFICACION_BTN = (By.ID, "continue-btn")
    LISTO_BTN = (
        By.XPATH,
        "//button[@id='finish' and .//span[contains(text(), '¡Listo, ya podemos comenzar!')]]",
    )
    BODY_TAG = (By.TAG_NAME, "body")
    TEXTO_CAPTURA_ROSTRO = (By.XPATH, "//*[contains(text(), 'Captura tu rostro')]")
    CONTINUAR_ROSTRO_BTN = (By.ID, "button")
    REINTENTAR_BTN = (By.ID, "retry")
    TEXTO_ERROR_CALIDAD = (
        By.XPATH,
        "//*[contains(text(), 'Error de calidad de captura')]",
    )
    SPINNER_VERIFICANDO = (By.XPATH, "//*[contains(text(), 'verificando')]")
    TEXTO_VALIDACION_EXITOSA = (
        By.XPATH,
        "//*[contains(text(), '¡Validación exitosa!')]",
    )
    TEXTO_TIEMPO_EXCEDIDO = (
        By.XPATH,
        "//*[contains(text(), 'Tiempo de espera excedido')]",
    )
    TEXTO_FALLO_AUTENTICACION = (
        By.XPATH,
        "//*[contains(text(), 'El proceso de autenticación ha fallado')]",
    )
    VOLVER_A_INTENTAR_LINK = (By.PARTIAL_LINK_TEXT, "Volver a Intentar")
    TEXTO_FIRMA_SIMPLE = (By.XPATH, "//*[contains(text(), 'Firma Simple Requerida')]")
    VERIFICAR_Y_FIRMAR_BTN = (By.ID, "buttonSign")


# Lock para logs
log_lock = threading.Lock()
xvfb_proceso = None


def asegurar_xdg_runtime_dir():
    """Garantiza que XDG_RUNTIME_DIR exista y tenga permisos seguros."""

    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and os.path.isdir(runtime_dir):
        try:
            os.chmod(runtime_dir, 0o700)
        except PermissionError:
            pass
        return runtime_dir

    runtime_dir = f"/tmp/xdg-runtime-{os.getuid()}"
    os.makedirs(runtime_dir, exist_ok=True)
    os.chmod(runtime_dir, 0o700)
    os.environ["XDG_RUNTIME_DIR"] = runtime_dir
    return runtime_dir


def _reservar_puerto_libre():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock.getsockname()[1]


def _detener_xvfb():
    """Detiene el proceso de Xvfb si fue iniciado por el script."""
    global xvfb_proceso
    if xvfb_proceso and xvfb_proceso.poll() is None:
        try:
            xvfb_proceso.terminate()
            xvfb_proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            xvfb_proceso.kill()
        finally:
            xvfb_proceso = None


atexit.register(_detener_xvfb)


def escribir_log(mensaje):
    """Escribe un mensaje en el archivo de log con timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}\n"
    with log_lock:
        with open(Config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
    print(f"[{timestamp}] {mensaje}")


def asegurar_entorno_grafico():
    """Garantiza que exista un DISPLAY disponible, iniciando Xvfb si es necesario."""
    global xvfb_proceso

    if os.environ.get("DISPLAY"):
        return os.environ["DISPLAY"]

    display = Config.XVFB_DISPLAY

    if xvfb_proceso and xvfb_proceso.poll() is None:
        os.environ["DISPLAY"] = display
        return display

    try:
        resultado = subprocess.run(
            ["pgrep", "-f", f"Xvfb {display}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if resultado.returncode == 0:
            os.environ["DISPLAY"] = display
            return display
    except Exception:
        pass

    if not shutil.which("Xvfb"):
        escribir_log(
            "❌ Xvfb no está instalado. Instala con 'sudo apt install xvfb' para ejecutar Chromium en servidores."
        )
        return None

    comando = [
        "Xvfb",
        display,
        "-screen",
        "0",
        Config.XVFB_SCREEN,
        *Config.XVFB_EXTRA_ARGS,
    ]

    try:
        xvfb_proceso = subprocess.Popen(
            comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(1)
        if xvfb_proceso.poll() is not None:
            escribir_log(
                "❌ No se pudo iniciar Xvfb automáticamente. Revisa permisos o instala el paquete."
            )
            xvfb_proceso = None
            return None
        os.environ["DISPLAY"] = display
        escribir_log(f"🖥️ Xvfb iniciado automáticamente en {display}")
        return display
    except FileNotFoundError:
        escribir_log(
            "❌ Xvfb no está disponible en el sistema. Instala con 'sudo apt install xvfb'."
        )
    except Exception as exc:
        escribir_log(f"❌ Error al iniciar Xvfb: {exc}")

    return None


def resolver_chrome_binario():
    """Devuelve la ruta al binario de Chromium/Chrome disponible."""
    for candidato in Config.CHROME_BIN_CANDIDATES:
        if not candidato:
            continue
        ruta = shutil.which(candidato) if not os.path.isabs(candidato) else candidato
        if ruta and os.path.exists(ruta):
            return ruta
    return None


def resolver_chromedriver():
    """Devuelve la ruta al ejecutable de chromedriver disponible."""
    for candidato in Config.CHROMEDRIVER_CANDIDATES:
        if not candidato:
            continue
        ruta = shutil.which(candidato) if not os.path.isabs(candidato) else candidato
        if ruta and os.path.exists(ruta):
            return ruta
    ruta = shutil.which("chromedriver")
    if ruta and os.path.exists(ruta):
        return ruta
    return None


class ControladorCamaraVirtual:
    """Controlador para manejar v4l2loopback (reemplazo de OBS)"""

    def __init__(self, dispositivo="/dev/video10"):
        self.dispositivo = dispositivo
        self.proceso_actual = None
        self.conectado = False
        self.verificar_dispositivo()

    def verificar_dispositivo(self):
        """Verifica que el dispositivo de cámara virtual existe"""
        if not os.path.exists(self.dispositivo):
            escribir_log(f"❌ Dispositivo {self.dispositivo} no existe")
            escribir_log("💡 Ejecuta: sudo modprobe v4l2loopback devices=1 video_nr=10")
            self.conectado = False
            return False
        escribir_log(f"✅ Dispositivo de cámara virtual {self.dispositivo} encontrado")
        self.conectado = True
        return True

    def mostrar_video(self, ruta_video, loop=True):
        """
        Muestra un video en la cámara virtual usando FFmpeg

        Args:
            ruta_video: Ruta al archivo Y4M
            loop: Si es True, reproduce en loop infinito
        """
        if not Path(ruta_video).exists():
            escribir_log(f"❌ Archivo de video no encontrado: {ruta_video}")
            return False

        # Detener video anterior si existe
        if self.proceso_actual:
            try:
                self.proceso_actual.terminate()
                self.proceso_actual.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proceso_actual.kill()
                self.proceso_actual.wait()

        # Preparar comando FFmpeg
        cmd = ["ffmpeg", "-re"]

        if loop:
            cmd.extend(["-stream_loop", "-1"])  # Loop infinito

        cmd.extend(["-i", ruta_video, "-f", "v4l2", self.dispositivo])

        # Iniciar proceso FFmpeg en background
        escribir_log(f"📹 Reproduciendo: {Path(ruta_video).name}")
        self.proceso_actual = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        time.sleep(1)  # Esperar a que FFmpeg inicialice

        # Verificar que el proceso sigue corriendo
        if self.proceso_actual.poll() is not None:
            escribir_log("❌ FFmpeg falló al iniciar")
            return False

        return True

    def detener(self):
        """Detiene la reproducción actual"""
        if self.proceso_actual:
            try:
                self.proceso_actual.terminate()
                self.proceso_actual.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proceso_actual.kill()
                self.proceso_actual.wait()
            escribir_log("🛑 Video detenido")


def cambiar_video_camara(cam_controller, nombre_video):
    """
    Cambia el video en la cámara virtual

    Args:
        cam_controller: Instancia de ControladorCamaraVirtual
        nombre_video: 'idle', 'left', 'right', 'front', 'back'

    Returns:
        bool: True si el cambio fue exitoso
    """
    mapeo_videos = {
        "idle": Config.VIDEO_IDLE,
        "left": Config.VIDEO_LEFT,
        "right": Config.VIDEO_RIGHT,
        "front": Config.VIDEO_FRONT,
        "back": Config.VIDEO_BACK,
    }

    ruta = mapeo_videos.get(nombre_video)
    if not ruta:
        escribir_log(f"❌ Video desconocido: {nombre_video}")
        return False

    return cam_controller.mostrar_video(ruta, loop=True)


def cargar_links_pendientes():
    """Carga los links pendientes de activación del archivo."""
    try:
        with open(Config.LINKS_FILE, "r", encoding="utf-8") as f:
            lineas = f.readlines()

        links_data = []
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            if not linea:
                continue

            partes = linea.split("=", 2)
            if len(partes) == 3:
                links_data.append(
                    {
                        "numero": partes[0],
                        "iccid": partes[1],
                        "link": partes[2],
                        "indice": i + 1,
                    }
                )
            else:
                escribir_log(f"⚠️ Línea ignorada (formato incorrecto): {linea[:70]}...")

        escribir_log(f"Cargados {len(links_data)} links para activación")
        return links_data

    except FileNotFoundError:
        escribir_log(f"❌ Archivo {Config.LINKS_FILE} no encontrado")
        return []
    except Exception as e:
        escribir_log(f"❌ Error al cargar links: {e}")
        return []


def crear_driver_chrome():
    """Crea una instancia de Chrome WebDriver con emulación móvil."""

    chromedriver_log = None

    try:
        asegurar_xdg_runtime_dir()
        display = asegurar_entorno_grafico()
        if not display:
            escribir_log(
                "❌ No se pudo preparar un entorno gráfico para Chromium. Abortando creación del driver."
            )
            return None

        chrome_binario = resolver_chrome_binario()
        if not chrome_binario:
            escribir_log(
                "❌ No se encontró el binario de Chromium/Chrome. Instala 'chromium-browser' o define CHROME_BINARY."
            )
            return None

        chromedriver_path = resolver_chromedriver()
        if not chromedriver_path:
            escribir_log(
                "❌ No se encontró el ejecutable de chromedriver. Instala 'chromedriver' o define CHROMEDRIVER_PATH."
            )
            return None

        mobile_emulation = {"deviceName": "iPhone XR"}

        chrome_options = Options()
        chrome_options.binary_location = chrome_binario

        debug_port = _reservar_puerto_libre()
        chrome_options.add_argument(f"--remote-debugging-port={debug_port}")
        chrome_options.add_argument(
            "--disable-features=Translate,BackForwardCache,AutomationControlled"
        )
        chrome_options.add_argument("--force-device-scale-factor=1")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--password-store=basic")
        chrome_options.add_argument("--use-mock-keychain")

        print(f"🔧 Debug port: {debug_port}")
        escribir_log(f"🔧 Debug port asignado: {debug_port}")

        for option in Config.CHROME_BASE_OPTIONS:
            chrome_options.add_argument(option)

        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=375,812")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        )
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--auto-accept-camera-and-microphone-capture")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

        prefs = {
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.notifications": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        chromedriver_log = Path(tempfile.gettempdir()) / f"chromedriver_{uuid.uuid4().hex}.log"
        service = Service(chromedriver_path, log_path=str(chromedriver_log))
        escribir_log(f"📝 Log de ChromeDriver: {chromedriver_log}")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        setattr(driver, "_activador_chromedriver_log", str(chromedriver_log))

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        driver.set_page_load_timeout(Config.TIMEOUT_PAGINA)
        driver.implicitly_wait(10)

        return driver

    except Exception as e:
        escribir_log(f"❌ Error al crear driver Chrome: {e}")

        if chromedriver_log and os.path.exists(chromedriver_log):
            with contextlib.suppress(OSError):
                os.remove(chromedriver_log)

        return None


def scroll_y_click_forzado(driver, wait, locator, intentos=3):
    """Hace clic en un elemento con scroll previo y fallback a JavaScript"""
    for i in range(intentos):
        try:
            # Esperar a que el elemento esté presente
            elemento = wait.until(EC.presence_of_element_located(locator))

            # Scroll al elemento
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                elemento,
            )
            time.sleep(1)

            # Intentar hacer visible si está oculto
            driver.execute_script(
                "arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';",
                elemento,
            )

            # Intentar clic normal primero
            try:
                elemento.click()
                print(f"✅ Clic exitoso en: {locator[1]}")
                return True
            except:
                # Si falla, usar JavaScript
                print(
                    f"🖱️ Forzando clic con JS en -> {elemento.text or elemento.get_attribute('id') or locator[1]}"
                )
                driver.execute_script("arguments[0].click();", elemento)
                return True

        except StaleElementReferenceException:
            print(
                f"⚠️ Error de 'stale element' en intento {i + 1}/{intentos}. Reintentando..."
            )
            time.sleep(2)
        except TimeoutException:
            print(f"⏰ Timeout esperando elemento en intento {i + 1}/{intentos}")
            if i == intentos - 1:
                # En el último intento, guardar screenshot
                try:
                    driver.save_screenshot(
                        f"/tmp/screenshot_error_{locator[1][:20]}.png"
                    )
                    print(f"📸 Screenshot guardado para debugging")
                except:
                    pass
                return False
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error en intento {i+1}/{intentos}: {e}")
            if i == intentos - 1:
                return False
            time.sleep(2)
    return False


def ejecutar_flujo_pre_biometria(driver, wait, cam_controller):
    """Ejecuta el flujo de pre-verificación con documentos"""
    try:
        print("▶️ Ejecutando flujo de pre-verificación...")
        print("... Aceptando términos y condiciones.")

        # Intentar múltiples estrategias para el checkbox
        checkbox_exitoso = False

        # Estrategia 1: Locator normal con JavaScript
        print("🔎 Estrategia 1: Locator ID='checkTyc'")
        if scroll_y_click_forzado(driver, wait, Locators.TERMS_CHECKBOX):
            checkbox_exitoso = True

        # Estrategia 2: Si falla, buscar por otros atributos
        if not checkbox_exitoso:
            print("🔎 Estrategia 2: Buscando checkbox por tipo 'checkbox'")
            try:
                checkboxes = driver.find_elements(
                    By.CSS_SELECTOR, "input[type='checkbox']"
                )
                print(f"   Encontrados {len(checkboxes)} checkboxes")
                for idx, cb in enumerate(checkboxes):
                    try:
                        cb_id = cb.get_attribute("id")
                        cb_class = cb.get_attribute("class")
                        print(f"   Checkbox {idx}: id='{cb_id}', class='{cb_class}'")
                        if not cb.is_selected():
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});", cb
                            )
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", cb)
                            print(f"   ✅ Checkbox {idx} clickeado")
                            checkbox_exitoso = True
                            break
                    except Exception as e:
                        print(f"   ⚠️ Error con checkbox {idx}: {e}")
            except Exception as e:
                print(f"   ❌ Error buscando checkboxes: {e}")

        # Estrategia 3: Si aún no funciona, buscar cualquier label o span relacionado
        if not checkbox_exitoso:
            print("🔎 Estrategia 3: Buscando labels relacionados con términos")
            try:
                labels = driver.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    texto = label.text.lower()
                    if "término" in texto or "condicion" in texto or "tyc" in texto:
                        print(f"   Encontrado label: '{label.text[:50]}'")
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", label
                        )
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", label)
                        checkbox_exitoso = True
                        print("   ✅ Label clickeado")
                        break
            except Exception as e:
                print(f"   ❌ Error con labels: {e}")

        if not checkbox_exitoso:
            driver.save_screenshot("/tmp/screenshot_checkbox_error.png")
            print("❌ No se pudo marcar el checkbox de términos con ninguna estrategia")
            return False

        time.sleep(1)
        print("✅ Checkbox de términos marcado exitosamente")

        if not scroll_y_click_forzado(driver, wait, Locators.INICIAR_BTN):
            return False

        print("... Iniciando fase de verificación de documentos con v4l2loopback.")
        if not scroll_y_click_forzado(driver, wait, Locators.EMPEZAR_VERIFICACION_BTN):
            return False
        if not scroll_y_click_forzado(driver, wait, Locators.LISTO_BTN):
            return False

        # CRÍTICO: Forzar inicio del stream de cámara con JavaScript
        print("📹 Forzando inicio del stream de cámara...")
        try:
            camera_start_script = """
            (async function() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            width: { ideal: 1280 },
                            height: { ideal: 720 },
                            facingMode: "user"
                        } 
                    });
                    console.log("✅ Stream de cámara iniciado:", stream.id);
                    
                    // Buscar video element y asignar stream
                    const videoElements = document.querySelectorAll('video');
                    if (videoElements.length > 0) {
                        videoElements[0].srcObject = stream;
                        videoElements[0].play();
                        console.log("✅ Video element found and stream assigned");
                    }
                    
                    return { success: true, streamId: stream.id };
                } catch(e) {
                    console.error("❌ Error iniciando cámara:", e);
                    return { success: false, error: e.message };
                }
            })();
            """
            result = driver.execute_async_script(
                camera_start_script + " arguments[arguments.length - 1](arguments[0]);"
            )
            print(f"   Resultado: {result}")
        except Exception as e:
            print(f"   ⚠️ Error ejecutando script de cámara: {e}")

        time.sleep(3)  # Dar tiempo a que la cámara se inicie

        # Capturar logs de consola antes de empezar
        print("📋 Logs de consola del navegador:")
        try:
            logs = driver.get_log("browser")
            for log in logs[-10:]:  # Últimos 10 logs
                print(f"   [{log['level']}] {log['message']}")
        except Exception as e:
            print(f"   ⚠️ No se pudieron obtener logs: {e}")

        # Screenshot antes de mostrar documentos
        try:
            driver.save_screenshot("/tmp/screenshot_antes_documentos.png")
            print("📸 Screenshot guardado: /tmp/screenshot_antes_documentos.png")
        except:
            pass

        # Mostrar documento frontal
        print("📸 Mostrando CI (Anverso)...")
        if not cambiar_video_camara(cam_controller, "front"):
            return False
        time.sleep(8)

        # Screenshot con documento frontal
        try:
            driver.save_screenshot("/tmp/screenshot_doc_frontal.png")
            print("📸 Screenshot con doc frontal: /tmp/screenshot_doc_frontal.png")
        except:
            pass

        # Mostrar documento reverso
        print("📸 Mostrando CI (Reverso)...")
        if not cambiar_video_camara(cam_controller, "back"):
            return False
        time.sleep(8)

        # Screenshot con documento reverso
        try:
            driver.save_screenshot("/tmp/screenshot_doc_reverso.png")
            print("📸 Screenshot con doc reverso: /tmp/screenshot_doc_reverso.png")
        except:
            pass

        # Volver a idle
        cambiar_video_camara(cam_controller, "idle")

        # Capturar logs de consola después de mostrar documentos
        print("📋 Logs de consola después de documentos:")
        try:
            logs = driver.get_log("browser")
            for log in logs[-10:]:  # Últimos 10 logs
                print(f"   [{log['level']}] {log['message']}")
        except Exception as e:
            print(f"   ⚠️ No se pudieron obtener logs: {e}")

        print("... Esperando resultado de la verificación de documentos.")
        print("🔍 Buscando en HTML: 'Documento validado'")

        # Buscar con más información
        try:
            # Buscar texto específico en el body
            body_text = driver.find_element(*Locators.BODY_TAG).text.lower()
            print(f"📄 Texto del body (primeros 500 chars): {body_text[:500]}")

            # Buscar mensajes de error o validación
            if "error" in body_text:
                print("⚠️ Se encontró 'error' en el HTML")
            if "validado" in body_text or "validación" in body_text:
                print("✅ Se encontró texto de validación en el HTML")
            if "documento" in body_text:
                print("📋 Se encontró 'documento' en el HTML")

            # Capturar screenshot antes de esperar
            driver.save_screenshot("/tmp/screenshot_esperando_validacion.png")
            print(
                "📸 Screenshot esperando validación: /tmp/screenshot_esperando_validacion.png"
            )

            wait.until(
                EC.text_to_be_present_in_element(
                    Locators.BODY_TAG, "Documento validado"
                )
            )
            print("🎉 ¡ÉXITO! Documento verificado correctamente.")
        except TimeoutException:
            print("❌ Timeout esperando 'Documento validado'")
            # Capturar estado final
            driver.save_screenshot("/tmp/screenshot_timeout_validacion.png")
            print("📸 Screenshot timeout: /tmp/screenshot_timeout_validacion.png")

            # Logs finales
            print("📋 Logs de consola en timeout:")
            try:
                logs = driver.get_log("browser")
                for log in logs[-15:]:
                    print(f"   [{log['level']}] {log['message']}")
            except:
                pass

            # HTML parcial
            try:
                html_snippet = driver.page_source[:2000]
                print(f"📄 HTML parcial (primeros 2000 chars):\n{html_snippet}")
            except:
                pass

            raise

        time.sleep(2)

        wait.until(EC.visibility_of_element_located(Locators.TEXTO_CAPTURA_ROSTRO))
        if not scroll_y_click_forzado(driver, wait, Locators.CONTINUAR_ROSTRO_BTN):
            return False
        if not scroll_y_click_forzado(driver, wait, Locators.LISTO_BTN):
            return False

        print("✅ Flujo de pre-verificación completado con éxito.")
        return True
    except Exception as e:
        print(f"❌ Error durante el flujo de pre-verificación: {e}")
        return False


def activar_tarjeta_completa(numero_telefono, iccid, link, cam_controller):
    """Realiza el proceso completo de activación para un link."""
    print(f"\n--- 💎 PROCESANDO: ICCID {iccid} ---")

    driver = None

    try:
        driver = crear_driver_chrome()
        if not driver:
            return False

        wait = WebDriverWait(driver, 20)

        print(f"🔗 Abriendo link...")
        driver.get(link)
        time.sleep(3)  # Dar tiempo extra para que la página cargue

        # Guardar screenshot para debugging
        try:
            driver.save_screenshot(f"/tmp/screenshot_rut_{iccid[:10]}.png")
            escribir_log(
                f"📸 Screenshot guardado: /tmp/screenshot_rut_{iccid[:10]}.png"
            )
        except:
            pass

        # Intentar encontrar el input de RUT con más tiempo
        print("🔎 Buscando campo RUT...")
        try:
            rut_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(Locators.RUT_INPUT)
            )
            rut_input.clear()
            rut_input.send_keys(Config.RUT_PROVISIONAL)
            print("📄 RUT ingresado.")
        except TimeoutException:
            escribir_log(
                f"❌ Timeout esperando campo RUT. URL actual: {driver.current_url}"
            )
            escribir_log(f"📄 Título de página: {driver.title}")
            driver.save_screenshot(f"/tmp/screenshot_error_{iccid[:10]}.png")
            return False

        driver.find_element(*Locators.BODY_TAG).click()

        print("🔎 Verificando si aparece el botón de bypass (5 segundos)...")
        try:
            wait_bypass = WebDriverWait(driver, 5)
            wait_bypass.until(
                EC.presence_of_element_located(Locators.CONTINUAR_BYPASS_BTN)
            )
            print("⚠️ Botón de bypass encontrado. Intentando clic forzado...")
            if scroll_y_click_forzado(
                driver, wait_bypass, Locators.CONTINUAR_BYPASS_BTN
            ):
                print("... Bypass activado. Esperando...")
                time.sleep(8)
        except TimeoutException:
            print(
                "... Botón de bypass no apareció. Asumiendo flujo normal o auto-redirect."
            )

        if not ejecutar_flujo_pre_biometria(driver, wait, cam_controller):
            return False

        print("\n--- 🤖 Iniciando ciclo de verificación biométrica ---")

        # Screenshot antes de biometría
        try:
            driver.save_screenshot("/tmp/screenshot_antes_biometria.png")
            print(
                "📸 Screenshot antes de biometría: /tmp/screenshot_antes_biometria.png"
            )
        except:
            pass

        # Logs de consola antes de biometría
        print("📋 Logs de consola antes de biometría:")
        try:
            logs = driver.get_log("browser")
            for log in logs[-10:]:
                print(f"   [{log['level']}] {log['message']}")
        except Exception as e:
            print(f"   ⚠️ No se pudieron obtener logs: {e}")

        time.sleep(2)

        # Mostrar idle al inicio
        cambiar_video_camara(cam_controller, "idle")

        biometria_exitosa = False
        tiempo_maximo_biometria = Config.TIEMPO_ESPERA_BIOMETRIA
        tiempo_inicio = time.time()
        iteracion = 0

        while time.time() - tiempo_inicio < tiempo_maximo_biometria:
            iteracion += 1
            tiempo_transcurrido = int(time.time() - tiempo_inicio)

            if iteracion % 10 == 0:  # Cada 10 iteraciones (~5 segundos)
                print(
                    f"⏱️ Biometría en progreso... {tiempo_transcurrido}s / {tiempo_maximo_biometria}s"
                )

            html_actual = driver.page_source.lower()

            if "validación exitosa" in html_actual:
                print("🎉 ¡ÉXITO! Validación exitosa detectada en el HTML.")
                biometria_exitosa = True
                break

            elif "el proceso de autenticación ha fallado" in html_actual:
                print("🚨 Fallo de autenticación detectado. Iniciando recuperación...")
                try:
                    if not scroll_y_click_forzado(
                        driver, wait, Locators.VOLVER_A_INTENTAR_LINK
                    ):
                        return False

                    time.sleep(2)
                    driver.switch_to.window(driver.window_handles[-1])
                    print("✅ Foco cambiado a la última pestaña.")

                    wait.until(
                        EC.presence_of_element_located(Locators.TEXTO_FIRMA_SIMPLE)
                    )

                    if not scroll_y_click_forzado(
                        driver, wait, Locators.VERIFICAR_Y_FIRMAR_BTN
                    ):
                        print(
                            "❌ No se pudo hacer clic en 'Verificar y Firmar'. Abortando."
                        )
                        return False

                    if not ejecutar_flujo_pre_biometria(driver, wait, cam_controller):
                        return False

                    print(
                        "✅ Secuencia completa reiniciada. Retomando ciclo de detección biométrica."
                    )
                    continue

                except Exception as e:
                    print(f"❌ Error CRÍTICO durante la recuperación: {e}")
                    return False

            elif (
                "tiempo de espera excedido" in html_actual
                or "error de calidad" in html_actual
            ):
                mensaje = (
                    "Tiempo de espera excedido"
                    if "tiempo de espera excedido" in html_actual
                    else "Error de calidad"
                )
                print(f"⚠️ {mensaje} detectado. Intentando reintentar...")
                if scroll_y_click_forzado(driver, wait, Locators.REINTENTAR_BTN):
                    print("... Clic en Reintentar. Reiniciando chequeo.")
                    time.sleep(3)
                else:
                    print("❌ No se encontró el botón de reintentar. Abortando.")
                    return False
                continue

            elif "verificando" in html_actual:
                print("⏳ Spinner 'verificando' detectado. Esperando...")
                time.sleep(1)
                continue

            else:
                # Buscar instrucciones de dirección en el HTML
                if any(
                    k in html_actual
                    for k in ["gira a la izquierda", "izquierda", "turn left"]
                ):
                    print("👈 Instrucción detectada: Girar a la IZQUIERDA")

                    # Screenshot antes del movimiento
                    try:
                        driver.save_screenshot(
                            f"/tmp/screenshot_antes_izquierda_{tiempo_transcurrido}s.png"
                        )
                        print(f"📸 Screenshot antes de girar izquierda")
                    except:
                        pass

                    cambiar_video_camara(cam_controller, "left")
                    time.sleep(5)
                    cambiar_video_camara(cam_controller, "idle")
                    time.sleep(2)

                elif any(
                    k in html_actual
                    for k in ["gira a la derecha", "derecha", "turn right"]
                ):
                    print("👉 Instrucción detectada: Girar a la DERECHA")

                    # Screenshot antes del movimiento
                    try:
                        driver.save_screenshot(
                            f"/tmp/screenshot_antes_derecha_{tiempo_transcurrido}s.png"
                        )
                        print(f"📸 Screenshot antes de girar derecha")
                    except:
                        pass

                    cambiar_video_camara(cam_controller, "right")
                    time.sleep(5)
                    cambiar_video_camara(cam_controller, "idle")
                    time.sleep(2)

                else:
                    # Si no hay instrucciones, mantener idle
                    time.sleep(1)

        if biometria_exitosa:
            print("\n✅✅✅ PROCESO COMPLETO FINALIZADO CON ÉXITO ✅✅✅")
            print("... Esperando 15 segundos finales.")
            time.sleep(15)
            return True
        else:
            print("❌ Se alcanzó el tiempo máximo para la biometría. Proceso fallido.")

            # Capturar estado final
            try:
                driver.save_screenshot("/tmp/screenshot_timeout_biometria.png")
                print(
                    "📸 Screenshot timeout biometría: /tmp/screenshot_timeout_biometria.png"
                )
            except:
                pass

            # Logs finales
            print("📋 Logs de consola en timeout biometría:")
            try:
                logs = driver.get_log("browser")
                for log in logs[-20:]:
                    print(f"   [{log['level']}] {log['message']}")
            except:
                pass

            # HTML parcial final
            try:
                body_text = driver.find_element(*Locators.BODY_TAG).text.lower()
                print(
                    f"📄 Texto del body al finalizar (primeros 800 chars):\n{body_text[:800]}"
                )
            except:
                pass

            return False

    except Exception as e:
        print(f"❌ Ocurrió un error inesperado durante la activación: {e}")
        import traceback

        traceback.print_exc()

        # Capturar estado en excepción
        if driver:
            try:
                driver.save_screenshot("/tmp/screenshot_exception.png")
                print("📸 Screenshot en excepción: /tmp/screenshot_exception.png")
            except:
                pass

            try:
                print("📋 Logs de consola en excepción:")
                logs = driver.get_log("browser")
                for log in logs[-20:]:
                    print(f"   [{log['level']}] {log['message']}")
            except:
                pass

        return False
    finally:
        print("🧹 Limpiando y finalizando proceso...")
        if driver:
            try:
                driver.quit()
            finally:
                try:
                    log_path = getattr(driver, "_activador_chromedriver_log", None)
                    if log_path and os.path.exists(log_path):
                        os.remove(log_path)
                except Exception:
                    pass


def activar_masivo_con_v4l2(links_data):
    """Orquesta la activación secuencial de múltiples tarjetas."""
    escribir_log(
        f"🚀 INICIANDO PROCESO DE ACTIVACIÓN SECUENCIAL DE {len(links_data)} TARJETAS (v4l2loopback v{VERSION})"
    )

    # Crear controlador de cámara virtual
    cam_controller = ControladorCamaraVirtual()
    if not cam_controller.conectado:
        escribir_log("❌ ERROR: No se pudo inicializar la cámara virtual. Abortando.")
        return 0, len(links_data)

    exitosos, fallidos = 0, 0
    try:
        for i, data in enumerate(links_data):
            escribir_log(f"📊 Procesando {i+1}/{len(links_data)}: {data['numero']}")
            try:
                resultado = activar_tarjeta_completa(
                    data["numero"], data["iccid"], data["link"], cam_controller
                )
                if resultado:
                    exitosos += 1
                else:
                    fallidos += 1
                escribir_log(
                    f"📊 Progreso: {i+1}/{len(links_data)} | ✅ Éxitos: {exitosos} | ❌ Fallos: {fallidos}"
                )

                if i < len(links_data) - 1:
                    escribir_log(
                        f"⏳ Pausa de {Config.PAUSA_ENTRE_ACTIVACIONES} segundos..."
                    )
                    time.sleep(Config.PAUSA_ENTRE_ACTIVACIONES)
            except Exception as e:
                fallidos += 1
                escribir_log(f"❌ Error irrecuperable para {data['numero']}: {e}")
    finally:
        # Detener cámara virtual
        cam_controller.detener()

    return exitosos, fallidos


def main():
    """Punto de entrada principal del script."""
    print("=" * 50)
    print(f">>> ACTIVADOR MASIVO MOVISTAR v{VERSION} - v4l2loopback <<<")
    print(">>> SIN OBS - Usando Cámara Virtual de Linux <<<")
    print("=" * 50 + "\n")

    # Verificar si se está ejecutando en modo automático
    modo_automatico = "--auto" in sys.argv
    if modo_automatico:
        print("🤖 MODO AUTOMÁTICO ACTIVADO - Sin confirmaciones")

    links_data = cargar_links_pendientes()
    if not links_data:
        print("❌ No se encontraron links con formato válido para activar.")
        return

    print(f"📋 Links cargados: {len(links_data)}")
    print(f"📹 MODO v4l2loopback: Activación con cámara virtual de Linux.")

    print(f"\n📄 Ejemplo de los primeros 3 links:")
    for i, data in enumerate(links_data[:3]):
        print(f"  {i+1}. {data['numero']} = {data['iccid']} = {data['link'][:40]}...")
    if len(links_data) > 3:
        print(f"  ... y {len(links_data) - 3} más.")

    # Solo pedir confirmación si no está en modo automático
    if not modo_automatico:
        try:
            confirmar = (
                input(
                    f"\n¿Proceder con la activación de {len(links_data)} tarjetas? (S/n): "
                )
                .strip()
                .lower()
            )
            if confirmar and confirmar not in ["s", "si", "y", "yes", ""]:
                print("❌ Operación cancelada por el usuario.")
                return
        except KeyboardInterrupt:
            print("\n❌ Operación cancelada por el usuario.")
            return
    else:
        print(
            f"🤖 Modo automático: procediendo con la activación de {len(links_data)} tarjetas"
        )

    escribir_log(
        "=" * 60
        + f"\nINICIANDO PROCESO DE ACTIVACIÓN MASIVA (v4l2loopback v{VERSION})\n"
        + "=" * 60
    )
    inicio = time.time()
    exitosos, fallidos = activar_masivo_con_v4l2(links_data)
    tiempo_total = time.time() - inicio

    resumen = (
        f"\n{'='*40}\n📊 RESUMEN DE LA OPERACIÓN:\n"
        f"   ⏱️  Tiempo total: {tiempo_total:.1f} segundos\n"
        f"   📱 Tarjetas procesadas: {len(links_data)}\n"
        f"   ✅ Activaciones exitosas: {exitosos}\n"
        f"   ❌ Activaciones fallidas: {fallidos}\n"
    )
    if len(links_data) > 0:
        resumen += (
            f"   📊 Tasa de éxito: {exitosos/len(links_data)*100:.1f}%\n"
            f"   ⚡ Tiempo promedio por tarjeta: {tiempo_total/len(links_data):.1f}s\n"
        )
    resumen += "=" * 40
    print(resumen)

    escribir_log(
        "=" * 60
        + f"\nPROCESO COMPLETADO - ✅{exitosos} ❌{fallidos} en {tiempo_total:.1f}s\n"
        + "=" * 60
    )

    if fallidos > 0:
        print(f"\n⚠️  Algunas activaciones fallaron. Revisa el log: {Config.LOG_FILE}")
    if exitosos > 0:
        print(f"\n🎉 PROCESO FINALIZADO. {exitosos} tarjeta(s) activada(s) con éxito.")


if __name__ == "__main__":
    main()
