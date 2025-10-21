FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    OBS_PROFILE=default \
    OBS_SCENE=Escena \
    OBS_WEBSOCKET_PORT=4455 \
    OBS_WEBSOCKET_PASSWORD=secret \
    OBS_DISPLAY_WIDTH=1920 \
    OBS_DISPLAY_HEIGHT=1080 \
    OBS_DISPLAY_DEPTH=24

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        obs-studio \
        v4l2loopback-dkms \
        linux-headers-generic \
        x11vnc xvfb pulseaudio \
        libgl1-mesa-glx libxcb-randr0 libxcb-xinerama0 \
        python3 python3-pip wget unzip curl \
    && rm -rf /var/lib/apt/lists/*

# Install OBS WebSocket plugin compatible with obsws-python (v5.x)
RUN wget -q https://github.com/obsproject/obs-websocket/releases/download/5.3.0/obs-websocket-5.3.0-Ubuntu.zip \
    && unzip -q obs-websocket-5.3.0-Ubuntu.zip -d /tmp/obsws \
    && /tmp/obsws/install.sh \
    && rm -rf /tmp/obsws obs-websocket-5.3.0-Ubuntu.zip

# Copy pre-configured OBS profiles and scenes (mounted at runtime too)
COPY obs_config/ /root/.config/obs-studio/

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 4455

CMD ["/usr/local/bin/entrypoint.sh"]
