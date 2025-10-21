#!/bin/bash
set -euo pipefail

# Allow overriding display geometry via environment variables
SCREEN_GEOMETRY="${OBS_DISPLAY_WIDTH:-1920}x${OBS_DISPLAY_HEIGHT:-1080}x${OBS_DISPLAY_DEPTH:-24}"

# Ensure PulseAudio daemon is running for OBS even when headless
pulseaudio --start --exit-idle-time=-1 --log-level=error || true

# Export DISPLAY for xvfb-run runtime
export DISPLAY="${DISPLAY:-:99}"

# Launch OBS with virtual camera and websocket support under Xvfb
exec xvfb-run --auto-servernum --server-args="-screen 0 ${SCREEN_GEOMETRY}" \
    obs --startvirtualcam --minimize-to-tray \
        --profile "${OBS_PROFILE}" \
        --scene "${OBS_SCENE}" \
        --websocket_port "${OBS_WEBSOCKET_PORT}" \
        --websocket_password "${OBS_WEBSOCKET_PASSWORD}"
