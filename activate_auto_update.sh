#!/bin/bash
# Script para cargar configuración de .env

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Variables de entorno cargadas desde .env"
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi
