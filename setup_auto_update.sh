#!/bin/bash
# ============================================================================
# Script de Configuración - Auto-Actualización Git (Linux/macOS)
# ============================================================================
# Este script facilita la configuración del sistema de auto-actualización
# en entornos Linux y macOS.
#
# USO:
#   ./setup_auto_update.sh                    # Configuración interactiva
#   ./setup_auto_update.sh --quick            # Usar defaults
#   ./setup_auto_update.sh --disable          # Desactivar auto-update
#   ./setup_auto_update.sh --diagnose         # Ejecutar diagnóstico
#   ./setup_auto_update.sh --test             # Ejecutar tests
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funciones de output
success() { echo -e "${GREEN}$1${NC}"; }
error() { echo -e "${RED}$1${NC}"; }
warning() { echo -e "${YELLOW}$1${NC}"; }
info() { echo -e "${CYAN}$1${NC}"; }

# Banner
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}🔄 CONFIGURACIÓN DE AUTO-ACTUALIZACIÓN GIT${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Parsear argumentos
QUICK=false
DISABLE=false
DIAGNOSE=false
TEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK=true
            shift
            ;;
        --disable)
            DISABLE=true
            shift
            ;;
        --diagnose)
            DIAGNOSE=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        *)
            error "Argumento desconocido: $1"
            exit 1
            ;;
    esac
done

# Verificar Git
info "🔍 Verificando instalación de Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    success "✅ Git instalado: $GIT_VERSION"
else
    error "❌ Git no está instalado"
    warning "💡 Instala Git:"
    echo "   Ubuntu/Debian: sudo apt install git"
    echo "   RHEL/CentOS:   sudo yum install git"
    echo "   macOS:         brew install git"
    exit 1
fi

# Verificar Python
info "🔍 Verificando instalación de Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "✅ Python instalado: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    success "✅ Python instalado: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    error "❌ Python no está instalado"
    exit 1
fi

# Verificar auto_update.py
info "🔍 Verificando módulo auto_update.py..."
if [ -f "auto_update.py" ]; then
    success "✅ auto_update.py encontrado"
else
    error "❌ auto_update.py no encontrado en el directorio actual"
    warning "💡 Asegúrate de ejecutar este script desde el directorio del proyecto"
    exit 1
fi

# MODO: Diagnóstico
if [ "$DIAGNOSE" = true ]; then
    info "\n🔍 Ejecutando diagnóstico del sistema..."
    echo ""
    $PYTHON_CMD auto_update.py --diagnose
    exit 0
fi

# MODO: Tests
if [ "$TEST" = true ]; then
    info "\n🧪 Ejecutando suite de tests..."
    echo ""
    
    if [ -f "test_auto_update.py" ]; then
        $PYTHON_CMD test_auto_update.py --verbose
    else
        error "❌ test_auto_update.py no encontrado"
        exit 1
    fi
    exit 0
fi

# MODO: Desactivar
if [ "$DISABLE" = true ]; then
    warning "\n⚠️ Desactivando auto-actualización..."
    export AUTO_UPDATE="False"
    success "✅ AUTO_UPDATE=False configurado para esta sesión"
    info "💡 Para desactivar permanentemente, agrega a tu ~/.bashrc o ~/.zshrc:"
    info '    export AUTO_UPDATE="False"'
    echo ""
    exit 0
fi

# MODO: Configuración
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}⚙️ CONFIGURACIÓN DE VARIABLES DE ENTORNO${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Defaults
DEFAULT_ENABLED="True"
DEFAULT_BRANCH="main"
DEFAULT_TIMEOUT="30"
DEFAULT_FORCE="False"
DEFAULT_LOG_LEVEL="INFO"
DEFAULT_LOG_FILE=""

if [ "$QUICK" = true ]; then
    info "🚀 Modo Quick: Usando configuración por defecto"
    ENABLED=$DEFAULT_ENABLED
    BRANCH=$DEFAULT_BRANCH
    TIMEOUT=$DEFAULT_TIMEOUT
    FORCE=$DEFAULT_FORCE
    LOG_LEVEL=$DEFAULT_LOG_LEVEL
    LOG_FILE=$DEFAULT_LOG_FILE
else
    # Configuración Interactiva
    info "Presiona ENTER para usar el valor por defecto [entre corchetes]\n"
    
    # AUTO_UPDATE
    read -p "¿Activar auto-actualización? (True/False) [$DEFAULT_ENABLED]: " ENABLED
    ENABLED=${ENABLED:-$DEFAULT_ENABLED}
    
    # AUTO_UPDATE_BRANCH
    read -p "Rama de Git a monitorear [$DEFAULT_BRANCH]: " BRANCH
    BRANCH=${BRANCH:-$DEFAULT_BRANCH}
    
    # AUTO_UPDATE_TIMEOUT
    read -p "Timeout para Git (segundos) [$DEFAULT_TIMEOUT]: " TIMEOUT
    TIMEOUT=${TIMEOUT:-$DEFAULT_TIMEOUT}
    
    # AUTO_UPDATE_FORCE
    echo ""
    warning "⚠️ ADVERTENCIA: FORCE=True sobrescribe cambios locales"
    read -p "Forzar actualización (True/False) [$DEFAULT_FORCE]: " FORCE
    FORCE=${FORCE:-$DEFAULT_FORCE}
    
    # AUTO_UPDATE_LOG_LEVEL
    echo ""
    read -p "Nivel de log (DEBUG/INFO/WARNING/ERROR) [$DEFAULT_LOG_LEVEL]: " LOG_LEVEL
    LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
    
    # AUTO_UPDATE_LOG_FILE
    read -p "Archivo de log (dejar vacío para solo consola) [$DEFAULT_LOG_FILE]: " LOG_FILE
    LOG_FILE=${LOG_FILE:-$DEFAULT_LOG_FILE}
fi

# Aplicar configuración
echo ""
info "📝 Aplicando configuración..."
echo ""

export AUTO_UPDATE=$ENABLED
success "✅ AUTO_UPDATE=$ENABLED"

export AUTO_UPDATE_BRANCH=$BRANCH
success "✅ AUTO_UPDATE_BRANCH=$BRANCH"

export AUTO_UPDATE_TIMEOUT=$TIMEOUT
success "✅ AUTO_UPDATE_TIMEOUT=$TIMEOUT"

export AUTO_UPDATE_FORCE=$FORCE
success "✅ AUTO_UPDATE_FORCE=$FORCE"

export AUTO_UPDATE_LOG_LEVEL=$LOG_LEVEL
success "✅ AUTO_UPDATE_LOG_LEVEL=$LOG_LEVEL"

if [ -n "$LOG_FILE" ]; then
    export AUTO_UPDATE_LOG_FILE=$LOG_FILE
    success "✅ AUTO_UPDATE_LOG_FILE=$LOG_FILE"
fi

# Crear archivo .env
echo ""
info "💾 Creando archivo .env para persistencia..."

cat > .env << EOF
# Configuración de Auto-Actualización Git
# Generado: $(date '+%Y-%m-%d %H:%M:%S')

AUTO_UPDATE=$ENABLED
AUTO_UPDATE_BRANCH=$BRANCH
AUTO_UPDATE_TIMEOUT=$TIMEOUT
AUTO_UPDATE_FORCE=$FORCE
AUTO_UPDATE_LOG_LEVEL=$LOG_LEVEL
EOF

if [ -n "$LOG_FILE" ]; then
    echo "AUTO_UPDATE_LOG_FILE=$LOG_FILE" >> .env
fi

success "✅ Archivo .env creado"

# Crear script de activación
cat > activate_auto_update.sh << 'EOF'
#!/bin/bash
# Script para cargar configuración de .env

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Variables de entorno cargadas desde .env"
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi
EOF

chmod +x activate_auto_update.sh
success "✅ Script activate_auto_update.sh creado"

# Resumen
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}✅ CONFIGURACIÓN COMPLETADA${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
info "📋 Variables configuradas para esta sesión de shell"
info "💾 Configuración guardada en: .env"
echo ""
info "🚀 Para ejecutar tu script:"
echo -e "   ${YELLOW}$PYTHON_CMD ActivadorMasivoMovistar_v4l2.py${NC}"
echo ""
info "🔍 Para verificar configuración:"
echo -e "   ${YELLOW}$PYTHON_CMD auto_update.py --diagnose${NC}"
echo ""
info "📝 Para cargar .env en nuevas sesiones:"
echo -e "   ${YELLOW}source activate_auto_update.sh${NC}"
echo ""
info "   O agrega a tu ~/.bashrc:"
echo -e "   ${YELLOW}export \$(cat /ruta/a/proyecto/.env | grep -v '^#' | xargs)${NC}"
echo ""

# Preguntar si ejecutar diagnóstico
if [ "$QUICK" = false ]; then
    echo ""
    read -p "¿Ejecutar diagnóstico ahora? (S/n): " RUN_DIAGNOSE
    RUN_DIAGNOSE=${RUN_DIAGNOSE:-S}
    
    if [ "$RUN_DIAGNOSE" = "S" ] || [ "$RUN_DIAGNOSE" = "s" ]; then
        echo ""
        $PYTHON_CMD auto_update.py --diagnose
    fi
fi

success "\n✅ ¡Configuración finalizada!"
echo ""
