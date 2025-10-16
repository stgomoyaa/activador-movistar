#!/usr/bin/env python3
"""
Test Suite para Sistema de Auto-Actualización
==============================================

Script de pruebas para validar el funcionamiento del módulo auto_update.py

Ejecutar:
    python test_auto_update.py
    python test_auto_update.py --verbose
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(message, status="INFO"):
    """Imprime mensaje de test formateado."""
    colors = {
        "PASS": Colors.GREEN,
        "FAIL": Colors.RED,
        "WARN": Colors.YELLOW,
        "INFO": Colors.BLUE,
    }
    color = colors.get(status, "")
    print(f"{color}[{status}]{Colors.RESET} {message}")


def run_command(cmd, capture=True, cwd=None):
    """Ejecuta comando y retorna resultado."""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, cwd=cwd, timeout=10)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)


class AutoUpdateTester:
    """Suite de pruebas para auto_update.py"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def test_import(self):
        """Test 1: Verificar que auto_update.py puede importarse."""
        print_test("Test 1: Importando módulo auto_update...", "INFO")
        try:
            import auto_update
            print_test("✓ Módulo importado correctamente", "PASS")
            self.passed += 1
            return True
        except ImportError as e:
            print_test(f"✗ No se pudo importar: {e}", "FAIL")
            self.failed += 1
            return False
    
    def test_config(self):
        """Test 2: Verificar configuración con variables de entorno."""
        print_test("Test 2: Probando configuración por ENV...", "INFO")
        
        # Guardar ENV original
        original_enabled = os.getenv("AUTO_UPDATE")
        original_branch = os.getenv("AUTO_UPDATE_BRANCH")
        
        try:
            # Probar configuración
            os.environ["AUTO_UPDATE"] = "False"
            os.environ["AUTO_UPDATE_BRANCH"] = "test-branch"
            
            # Re-importar para aplicar cambios
            import importlib
            import auto_update
            importlib.reload(auto_update)
            
            if auto_update.AutoUpdateConfig.ENABLED == False:
                print_test("✓ AUTO_UPDATE=False detectado correctamente", "PASS")
                self.passed += 1
            else:
                print_test("✗ AUTO_UPDATE no se aplicó correctamente", "FAIL")
                self.failed += 1
            
            if auto_update.AutoUpdateConfig.TARGET_BRANCH == "test-branch":
                print_test("✓ AUTO_UPDATE_BRANCH configurado correctamente", "PASS")
                self.passed += 1
            else:
                print_test("✗ AUTO_UPDATE_BRANCH no se aplicó", "FAIL")
                self.failed += 1
            
        finally:
            # Restaurar ENV
            if original_enabled:
                os.environ["AUTO_UPDATE"] = original_enabled
            else:
                os.environ.pop("AUTO_UPDATE", None)
            
            if original_branch:
                os.environ["AUTO_UPDATE_BRANCH"] = original_branch
            else:
                os.environ.pop("AUTO_UPDATE_BRANCH", None)
    
    def test_git_detection(self):
        """Test 3: Detectar si Git está instalado."""
        print_test("Test 3: Verificando instalación de Git...", "INFO")
        
        success, stdout, stderr = run_command(["git", "--version"])
        
        if success:
            version = stdout.strip()
            print_test(f"✓ Git instalado: {version}", "PASS")
            self.passed += 1
            return True
        else:
            print_test("✗ Git no está instalado o no está en PATH", "FAIL")
            self.failed += 1
            return False
    
    def test_git_repo_detection(self):
        """Test 4: Verificar detección de repositorio Git."""
        print_test("Test 4: Probando detección de repositorio Git...", "INFO")
        
        try:
            from auto_update import is_git_repository
            
            # Verificar directorio actual
            is_repo = is_git_repository()
            
            if is_repo:
                print_test("✓ Directorio actual es repositorio Git", "PASS")
                self.passed += 1
            else:
                print_test("⚠ Directorio actual NO es repositorio Git", "WARN")
                print_test("  (Esto es normal si no ejecutas desde un repo)", "INFO")
                self.warnings += 1
            
            # Crear directorio temporal (NO es repo)
            with tempfile.TemporaryDirectory() as tmpdir:
                is_temp_repo = is_git_repository(tmpdir)
                if not is_temp_repo:
                    print_test("✓ Detecta correctamente directorio NO-git", "PASS")
                    self.passed += 1
                else:
                    print_test("✗ Falso positivo en directorio temporal", "FAIL")
                    self.failed += 1
        
        except Exception as e:
            print_test(f"✗ Error en test: {e}", "FAIL")
            self.failed += 1
    
    def test_lock_system(self):
        """Test 5: Verificar sistema de locks."""
        print_test("Test 5: Probando sistema de locks anti-loop...", "INFO")
        
        try:
            from auto_update import UpdateLock
            
            lock_file = ".test_auto_update.lock"
            
            # Test 1: Adquirir lock
            lock1 = UpdateLock(lock_file)
            if lock1.acquire():
                print_test("✓ Lock adquirido correctamente", "PASS")
                self.passed += 1
            else:
                print_test("✗ No se pudo adquirir lock", "FAIL")
                self.failed += 1
                return
            
            # Test 2: Intentar adquirir lock duplicado (debe fallar)
            lock2 = UpdateLock(lock_file)
            if not lock2.acquire():
                print_test("✓ Prevención de lock duplicado funciona", "PASS")
                self.passed += 1
            else:
                print_test("✗ Lock duplicado permitido (ERROR)", "FAIL")
                self.failed += 1
            
            # Test 3: Liberar lock
            lock1.release()
            if not Path(lock_file).exists():
                print_test("✓ Lock liberado correctamente", "PASS")
                self.passed += 1
            else:
                print_test("✗ Lock no se liberó", "FAIL")
                self.failed += 1
            
            # Cleanup
            if Path(lock_file).exists():
                Path(lock_file).unlink()
        
        except Exception as e:
            print_test(f"✗ Error en test de locks: {e}", "FAIL")
            self.failed += 1
    
    def test_branch_detection(self):
        """Test 6: Detectar rama actual (si estamos en repo)."""
        print_test("Test 6: Probando detección de rama Git...", "INFO")
        
        try:
            from auto_update import get_current_branch, is_git_repository
            
            if not is_git_repository():
                print_test("⚠ No es repo Git - test omitido", "WARN")
                self.warnings += 1
                return
            
            branch = get_current_branch()
            
            if branch:
                print_test(f"✓ Rama detectada: '{branch}'", "PASS")
                self.passed += 1
            else:
                print_test("✗ No se pudo detectar rama", "FAIL")
                self.failed += 1
        
        except Exception as e:
            print_test(f"✗ Error en test: {e}", "FAIL")
            self.failed += 1
    
    def test_local_changes_detection(self):
        """Test 7: Detectar cambios locales."""
        print_test("Test 7: Probando detección de cambios locales...", "INFO")
        
        try:
            from auto_update import has_local_changes, is_git_repository
            
            if not is_git_repository():
                print_test("⚠ No es repo Git - test omitido", "WARN")
                self.warnings += 1
                return
            
            changes = has_local_changes()
            
            if changes:
                print_test("⚠ Hay cambios locales detectados", "WARN")
                print_test("  (Esto puede ser normal durante desarrollo)", "INFO")
                self.warnings += 1
            else:
                print_test("✓ No hay cambios locales", "PASS")
                self.passed += 1
        
        except Exception as e:
            print_test(f"✗ Error en test: {e}", "FAIL")
            self.failed += 1
    
    def test_logger(self):
        """Test 8: Verificar sistema de logging."""
        print_test("Test 8: Probando sistema de logging...", "INFO")
        
        try:
            from auto_update import setup_logger
            import logging
            
            logger = setup_logger()
            
            if isinstance(logger, logging.Logger):
                print_test("✓ Logger creado correctamente", "PASS")
                self.passed += 1
            else:
                print_test("✗ Logger inválido", "FAIL")
                self.failed += 1
            
            # Verificar que puede escribir
            try:
                logger.info("Test message")
                print_test("✓ Logger puede escribir mensajes", "PASS")
                self.passed += 1
            except Exception as e:
                print_test(f"✗ Error escribiendo log: {e}", "FAIL")
                self.failed += 1
        
        except Exception as e:
            print_test(f"✗ Error en test de logger: {e}", "FAIL")
            self.failed += 1
    
    def test_diagnose_function(self):
        """Test 9: Ejecutar función de diagnóstico."""
        print_test("Test 9: Probando función diagnose()...", "INFO")
        
        try:
            from auto_update import diagnose
            
            # Capturar output
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                diagnose()
            
            output = f.getvalue()
            
            if "DIAGNÓSTICO DE AUTO-ACTUALIZACIÓN" in output:
                print_test("✓ Función diagnose() ejecutada correctamente", "PASS")
                self.passed += 1
            else:
                print_test("✗ Output de diagnose() inesperado", "FAIL")
                self.failed += 1
            
            if self.verbose:
                print("\n--- Output de diagnose() ---")
                print(output)
                print("--- Fin de output ---\n")
        
        except Exception as e:
            print_test(f"✗ Error ejecutando diagnose(): {e}", "FAIL")
            self.failed += 1
    
    def test_python_interpreter_detection(self):
        """Test 10: Verificar detección del intérprete Python."""
        print_test("Test 10: Probando detección de intérprete Python...", "INFO")
        
        try:
            python_exe = sys.executable
            
            if python_exe and Path(python_exe).exists():
                print_test(f"✓ Intérprete detectado: {python_exe}", "PASS")
                self.passed += 1
            else:
                print_test("✗ No se pudo detectar intérprete válido", "FAIL")
                self.failed += 1
        
        except Exception as e:
            print_test(f"✗ Error en test: {e}", "FAIL")
            self.failed += 1
    
    def run_all_tests(self):
        """Ejecuta todos los tests."""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}🧪 TEST SUITE - SISTEMA DE AUTO-ACTUALIZACIÓN{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        tests = [
            self.test_import,
            self.test_config,
            self.test_git_detection,
            self.test_git_repo_detection,
            self.test_lock_system,
            self.test_branch_detection,
            self.test_local_changes_detection,
            self.test_logger,
            self.test_diagnose_function,
            self.test_python_interpreter_detection,
        ]
        
        for i, test in enumerate(tests, 1):
            print(f"\n{Colors.BOLD}--- Test {i}/{len(tests)} ---{Colors.RESET}")
            try:
                test()
            except Exception as e:
                print_test(f"✗ Test falló con excepción: {e}", "FAIL")
                self.failed += 1
        
        # Resumen
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 RESUMEN DE TESTS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        
        total = self.passed + self.failed + self.warnings
        print(f"{Colors.GREEN}✓ Pasados:{Colors.RESET}    {self.passed}/{total}")
        print(f"{Colors.RED}✗ Fallados:{Colors.RESET}   {self.failed}/{total}")
        print(f"{Colors.YELLOW}⚠ Warnings:{Colors.RESET}   {self.warnings}/{total}")
        
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{Colors.BOLD}Tasa de éxito:{Colors.RESET} {success_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS LOS TESTS PASARON{Colors.RESET}")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ALGUNOS TESTS FALLARON{Colors.RESET}")
            return False


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Suite para auto_update.py"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mostrar output detallado"
    )
    
    args = parser.parse_args()
    
    tester = AutoUpdateTester(verbose=args.verbose)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
