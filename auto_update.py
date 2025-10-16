#!/usr/bin/env python3
"""
Módulo de Auto-Actualización mediante Git
==========================================

Sistema self-contained para actualizar automáticamente un script Python
desde su repositorio Git antes de cada ejecución.

Características:
- Actualización automática vía git pull
- Detección de cambios y reinicio inteligente
- Manejo robusto de errores con logs detallados
- Compatible con Linux y Windows
- Configurable mediante variables de entorno
- Protección anti-bucles infinitos
- Verificación de rama y conflictos
- Detección del intérprete Python actual

Autor: DevOps Engineering Team
Fecha: 2025-10-16
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

class AutoUpdateConfig:
    """Configuración centralizada del sistema de auto-actualización."""
    
    # Activar/desactivar auto-update (configurable por ENV)
    ENABLED = os.getenv("AUTO_UPDATE", "True").lower() in ("true", "1", "yes", "on")
    
    # Rama a monitorear (por defecto: main)
    TARGET_BRANCH = os.getenv("AUTO_UPDATE_BRANCH", "main")
    
    # Timeout para operaciones git (segundos)
    GIT_TIMEOUT = int(os.getenv("AUTO_UPDATE_TIMEOUT", "30"))
    
    # Archivo lock para prevenir bucles infinitos
    LOCK_FILE = ".auto_update.lock"
    
    # Tiempo máximo de vida del lock (segundos) - previene locks huérfanos
    LOCK_MAX_AGE = 300  # 5 minutos
    
    # Nivel de logging
    LOG_LEVEL = os.getenv("AUTO_UPDATE_LOG_LEVEL", "INFO").upper()
    
    # Archivo de log (None = solo consola)
    LOG_FILE = os.getenv("AUTO_UPDATE_LOG_FILE", None)
    
    # Máximo número de reintentos en caso de error temporal
    MAX_RETRIES = int(os.getenv("AUTO_UPDATE_MAX_RETRIES", "3"))
    
    # Forzar actualización aunque haya cambios locales (PELIGROSO)
    FORCE_UPDATE = os.getenv("AUTO_UPDATE_FORCE", "False").lower() in ("true", "1")


# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

def setup_logger() -> logging.Logger:
    """
    Configura el sistema de logging con formato profesional.
    
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger("AutoUpdate")
    logger.setLevel(getattr(logging, AutoUpdateConfig.LOG_LEVEL, logging.INFO))
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato detallado con timestamp
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (opcional)
    if AutoUpdateConfig.LOG_FILE:
        try:
            file_handler = logging.FileHandler(
                AutoUpdateConfig.LOG_FILE, 
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"No se pudo crear log file: {e}")
    
    return logger


logger = setup_logger()


# ============================================================================
# UTILIDADES DE GIT
# ============================================================================

def run_git_command(
    args: list, 
    timeout: Optional[int] = None,
    cwd: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Ejecuta un comando git de forma segura.
    
    Args:
        args: Lista de argumentos para git (ej: ['status', '--porcelain'])
        timeout: Timeout en segundos (None = usar config default)
        cwd: Directorio de trabajo (None = directorio actual)
    
    Returns:
        Tuple[bool, str, str]: (éxito, stdout, stderr)
    """
    timeout = timeout or AutoUpdateConfig.GIT_TIMEOUT
    cmd = ["git"] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace"
        )
        
        success = result.returncode == 0
        return success, result.stdout.strip(), result.stderr.strip()
        
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Timeout ejecutando: git {' '.join(args)}")
        return False, "", f"Timeout after {timeout}s"
    
    except FileNotFoundError:
        logger.error("❌ Git no está instalado o no está en el PATH")
        return False, "", "Git command not found"
    
    except Exception as e:
        logger.error(f"❌ Error ejecutando git: {e}")
        return False, "", str(e)


def is_git_repository(path: Optional[str] = None) -> bool:
    """
    Verifica si el directorio es un repositorio git válido.
    
    Args:
        path: Ruta a verificar (None = directorio actual)
    
    Returns:
        bool: True si es un repositorio git
    """
    success, stdout, stderr = run_git_command(["rev-parse", "--git-dir"], cwd=path)
    return success


def get_current_branch() -> Optional[str]:
    """
    Obtiene el nombre de la rama actual.
    
    Returns:
        Optional[str]: Nombre de la rama o None si hay error
    """
    success, branch, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    return branch if success else None


def has_local_changes() -> bool:
    """
    Verifica si hay cambios locales sin commitear.
    
    Returns:
        bool: True si hay cambios locales
    """
    success, stdout, _ = run_git_command(["status", "--porcelain"])
    return bool(stdout) if success else False


def get_remote_url() -> Optional[str]:
    """
    Obtiene la URL del repositorio remoto.
    
    Returns:
        Optional[str]: URL del remote o None
    """
    success, url, _ = run_git_command(["config", "--get", "remote.origin.url"])
    return url if success else None


def fetch_updates() -> bool:
    """
    Descarga actualizaciones del remoto sin aplicarlas.
    
    Returns:
        bool: True si el fetch fue exitoso
    """
    logger.info("📡 Consultando repositorio remoto...")
    success, _, stderr = run_git_command(["fetch", "origin"])
    
    if not success:
        logger.warning(f"⚠️ Fetch falló: {stderr}")
    
    return success


def check_updates_available() -> bool:
    """
    Verifica si hay commits nuevos en el remoto.
    
    Returns:
        bool: True si hay actualizaciones disponibles
    """
    branch = get_current_branch()
    if not branch:
        return False
    
    # Comparar HEAD local vs remoto
    success, local_hash, _ = run_git_command(["rev-parse", "HEAD"])
    if not success:
        return False
    
    success, remote_hash, _ = run_git_command(["rev-parse", f"origin/{branch}"])
    if not success:
        return False
    
    return local_hash != remote_hash


# ============================================================================
# SISTEMA DE LOCKS (Anti-Loop)
# ============================================================================

class UpdateLock:
    """Gestiona el archivo lock para prevenir bucles de actualización."""
    
    def __init__(self, lock_file: str = AutoUpdateConfig.LOCK_FILE):
        self.lock_file = Path(lock_file)
        self.created = False
    
    def acquire(self) -> bool:
        """
        Intenta adquirir el lock.
        
        Returns:
            bool: True si se adquirió exitosamente
        """
        # Verificar si existe un lock antiguo y limpiarlo
        if self.lock_file.exists():
            try:
                age = time.time() - self.lock_file.stat().st_mtime
                if age > AutoUpdateConfig.LOCK_MAX_AGE:
                    logger.warning(f"🧹 Limpiando lock huérfano (edad: {age:.0f}s)")
                    self.lock_file.unlink()
                else:
                    logger.warning("🔒 Lock activo - actualizacion en progreso o reciente")
                    return False
            except Exception as e:
                logger.error(f"Error verificando lock: {e}")
                return False
        
        # Crear lock
        try:
            self.lock_file.write_text(
                f"Locked at {datetime.now().isoformat()}\nPID: {os.getpid()}\n",
                encoding="utf-8"
            )
            self.created = True
            logger.debug(f"🔒 Lock adquirido: {self.lock_file}")
            return True
        except Exception as e:
            logger.error(f"Error creando lock: {e}")
            return False
    
    def release(self):
        """Libera el lock si fue creado por esta instancia."""
        if self.created and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                logger.debug(f"🔓 Lock liberado: {self.lock_file}")
            except Exception as e:
                logger.error(f"Error liberando lock: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError("No se pudo adquirir el lock de actualización")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


# ============================================================================
# FUNCIÓN PRINCIPAL DE AUTO-ACTUALIZACIÓN
# ============================================================================

def auto_update(script_path: Optional[str] = None) -> bool:
    """
    Sistema principal de auto-actualización.
    
    Verifica actualizaciones en Git, descarga cambios si existen,
    y reinicia el script con la nueva versión.
    
    Args:
        script_path: Ruta del script a reiniciar (None = __main__.__file__)
    
    Returns:
        bool: True si NO hubo actualización (continuar normalmente)
              False si hubo actualización y se reinició (no debería retornar)
    
    Raises:
        RuntimeError: Si hay errores críticos irrecuperables
    """
    # Verificar si está activado
    if not AutoUpdateConfig.ENABLED:
        logger.info("ℹ️ Auto-actualización desactivada (AUTO_UPDATE=False)")
        return True
    
    logger.info("=" * 70)
    logger.info("🔄 INICIANDO SISTEMA DE AUTO-ACTUALIZACIÓN")
    logger.info("=" * 70)
    
    # Obtener ruta del script principal
    if script_path is None:
        try:
            script_path = os.path.abspath(sys.argv[0])
        except Exception:
            script_path = os.path.abspath(__file__)
    
    script_dir = os.path.dirname(script_path)
    
    # Verificar que estamos en un repositorio git
    if not is_git_repository(script_dir):
        logger.warning("⚠️ El directorio no es un repositorio Git")
        logger.info("💡 Continuando sin auto-actualización")
        return True
    
    try:
        # Adquirir lock para prevenir ejecuciones concurrentes
        with UpdateLock():
            
            # Información del repositorio
            branch = get_current_branch()
            remote_url = get_remote_url()
            
            logger.info(f"📂 Directorio: {script_dir}")
            logger.info(f"🌿 Rama actual: {branch}")
            logger.info(f"🔗 Remoto: {remote_url or 'No configurado'}")
            
            # Verificar rama objetivo
            if branch != AutoUpdateConfig.TARGET_BRANCH:
                logger.warning(
                    f"⚠️ Rama actual '{branch}' difiere de la objetivo "
                    f"'{AutoUpdateConfig.TARGET_BRANCH}'"
                )
                logger.info("💡 Continuando sin actualizar")
                return True
            
            # Verificar cambios locales
            if has_local_changes():
                if AutoUpdateConfig.FORCE_UPDATE:
                    logger.warning("⚠️ Hay cambios locales - forzando actualización (FORCE_UPDATE=True)")
                    # Intentar hacer stash
                    success, _, stderr = run_git_command(["stash", "push", "-u", "-m", "Auto-update stash"])
                    if not success:
                        logger.error(f"❌ No se pudo hacer stash: {stderr}")
                        logger.info("💡 Continuando sin actualizar")
                        return True
                else:
                    logger.warning("⚠️ Hay cambios locales sin commitear")
                    logger.info("💡 Continuando sin actualizar (usa AUTO_UPDATE_FORCE=True para forzar)")
                    return True
            
            # Fetch actualizaciones
            if not fetch_updates():
                logger.warning("⚠️ No se pudo consultar el repositorio remoto")
                logger.info("💡 Continuando sin actualizar (posible problema de conexión)")
                return True
            
            # Verificar si hay actualizaciones
            if not check_updates_available():
                logger.info("✅ El script ya está actualizado")
                return True
            
            # HAY ACTUALIZACIONES DISPONIBLES
            logger.info("📦 Se encontraron actualizaciones nuevas")
            logger.info("⬇️ Descargando cambios...")
            
            # Git pull
            success, stdout, stderr = run_git_command(["pull", "origin", branch])
            
            if not success:
                logger.error(f"❌ Error en git pull: {stderr}")
                logger.info("💡 Continuando con versión actual")
                return True
            
            logger.info("✅ Actualización descargada correctamente")
            logger.info(f"📋 Cambios:\n{stdout}")
            
            # REINICIAR EL SCRIPT CON LA NUEVA VERSIÓN
            logger.info("=" * 70)
            logger.info("🔄 REINICIANDO CON NUEVA VERSIÓN...")
            logger.info("=" * 70)
            
            restart_script(script_path)
            
            # Si restart_script retorna, algo falló
            logger.error("❌ No se pudo reiniciar el script")
            return True
    
    except RuntimeError as e:
        # Lock no disponible u otro error controlado
        logger.warning(f"⚠️ {e}")
        logger.info("💡 Continuando sin actualizar")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error inesperado durante auto-actualización: {e}")
        logger.info("💡 Continuando con versión actual")
        import traceback
        logger.debug(traceback.format_exc())
        return True


def restart_script(script_path: str):
    """
    Reinicia el script Python actual preservando argumentos.
    
    Args:
        script_path: Ruta absoluta del script a reiniciar
    
    Note:
        Esta función NO retorna si tiene éxito (reemplaza el proceso actual)
    """
    # Detectar el intérprete Python actual
    python_executable = sys.executable
    
    # Preservar argumentos originales
    args = sys.argv.copy()
    args[0] = script_path
    
    logger.info(f"🐍 Intérprete: {python_executable}")
    logger.info(f"📜 Script: {script_path}")
    logger.info(f"⚙️ Argumentos: {args}")
    
    try:
        # En Windows, usar os.execv directamente
        if sys.platform == "win32":
            os.execv(python_executable, [python_executable] + args)
        else:
            # En Unix, usar os.execv con el intérprete
            os.execv(python_executable, [python_executable] + args)
    
    except Exception as e:
        logger.error(f"❌ Error en execv: {e}")
        
        # Fallback: intentar con subprocess
        try:
            logger.warning("⚠️ Intentando reinicio alternativo con subprocess...")
            subprocess.Popen([python_executable] + args)
            sys.exit(0)
        except Exception as e2:
            logger.error(f"❌ Reinicio alternativo falló: {e2}")
            raise


# ============================================================================
# FUNCIÓN DE CONVENIENCIA PARA INTEGRACIÓN SIMPLE
# ============================================================================

def check_and_update():
    """
    Función simple de integración - llama a auto_update() y maneja el retorno.
    
    Usage:
        if __name__ == "__main__":
            from auto_update import check_and_update
            check_and_update()
            
            # Tu código principal aquí...
    
    Returns:
        None (continúa ejecución si no hay actualización, 
              o reinicia proceso si hay actualización)
    """
    try:
        should_continue = auto_update()
        if not should_continue:
            # Si retorna False, hubo actualización y reinicio
            # (aunque normalmente no debería llegar aquí)
            logger.info("🔄 Actualización completada - reiniciando...")
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error en auto-actualización: {e}")
        logger.info("💡 Continuando con versión actual")


# ============================================================================
# DIAGNÓSTICO Y TESTING
# ============================================================================

def diagnose():
    """
    Ejecuta un diagnóstico completo del sistema de auto-actualización.
    Útil para debugging y verificación de configuración.
    """
    print("\n" + "=" * 70)
    print("🔍 DIAGNÓSTICO DE AUTO-ACTUALIZACIÓN")
    print("=" * 70)
    
    # Configuración
    print("\n📋 CONFIGURACIÓN:")
    print(f"  • Auto-update activado: {AutoUpdateConfig.ENABLED}")
    print(f"  • Rama objetivo: {AutoUpdateConfig.TARGET_BRANCH}")
    print(f"  • Timeout Git: {AutoUpdateConfig.GIT_TIMEOUT}s")
    print(f"  • Forzar actualización: {AutoUpdateConfig.FORCE_UPDATE}")
    print(f"  • Max reintentos: {AutoUpdateConfig.MAX_RETRIES}")
    print(f"  • Log level: {AutoUpdateConfig.LOG_LEVEL}")
    
    # Estado del repositorio
    print("\n📂 ESTADO DEL REPOSITORIO:")
    
    if is_git_repository():
        print("  ✅ Directorio es un repositorio Git")
        
        branch = get_current_branch()
        print(f"  • Rama actual: {branch}")
        
        remote = get_remote_url()
        print(f"  • Remote URL: {remote or 'No configurado'}")
        
        if has_local_changes():
            print("  ⚠️ Hay cambios locales sin commitear")
        else:
            print("  ✅ No hay cambios locales")
        
        # Intentar fetch
        if fetch_updates():
            print("  ✅ Conexión con remoto exitosa")
            
            if check_updates_available():
                print("  📦 HAY ACTUALIZACIONES DISPONIBLES")
            else:
                print("  ✅ Repositorio actualizado")
        else:
            print("  ❌ No se pudo conectar con el remoto")
    else:
        print("  ❌ El directorio NO es un repositorio Git")
    
    # Python
    print("\n🐍 ENTORNO PYTHON:")
    print(f"  • Ejecutable: {sys.executable}")
    print(f"  • Versión: {sys.version}")
    print(f"  • Plataforma: {sys.platform}")
    
    # Lock
    print("\n🔒 SISTEMA DE LOCKS:")
    lock_file = Path(AutoUpdateConfig.LOCK_FILE)
    if lock_file.exists():
        age = time.time() - lock_file.stat().st_mtime
        print(f"  ⚠️ Lock existe (edad: {age:.1f}s)")
        if age > AutoUpdateConfig.LOCK_MAX_AGE:
            print(f"  💡 Lock huérfano - será limpiado")
    else:
        print("  ✅ No hay lock activo")
    
    print("\n" + "=" * 70)


# ============================================================================
# CLI (si se ejecuta directamente)
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sistema de Auto-Actualización mediante Git",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Ejecutar diagnóstico del sistema"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Probar actualización (sin reiniciar)"
    )
    
    parser.add_argument(
        "--clear-lock",
        action="store_true",
        help="Limpiar archivo lock manualmente"
    )
    
    args = parser.parse_args()
    
    if args.diagnose:
        diagnose()
    
    elif args.clear_lock:
        lock_file = Path(AutoUpdateConfig.LOCK_FILE)
        if lock_file.exists():
            lock_file.unlink()
            print(f"✅ Lock eliminado: {lock_file}")
        else:
            print("ℹ️ No existe archivo lock")
    
    elif args.test:
        print("🧪 Modo de prueba - verificando actualizaciones sin reiniciar...\n")
        auto_update()
    
    else:
        parser.print_help()
