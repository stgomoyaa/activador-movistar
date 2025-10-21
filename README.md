# Arquitectura Dockerizada para Activador Movistar

Este repositorio incluye un entorno listo para ejecutar múltiples instancias de OBS Studio en Linux Server mediante contenedores Docker. Cada instancia expone una cámara virtual, mantiene escenas configuradas y habilita el plugin OBS WebSocket para que el script de automatización controle la escena y sincronice la biometría con Selenium/Chrome.

## Estructura del proyecto

```
├── docker-compose.yml
├── docker
│   └── obs
│       ├── Dockerfile
│       └── entrypoint.sh
├── obs_config/
│   └── .gitkeep
├── ActivadorMasivoMovistar_v4l2.py
└── requirements.txt
```

- `docker/obs/Dockerfile`: Imagen base para OBS con cámara virtual (`v4l2loopback`), servidor gráfico headless (Xvfb) y plugin OBS WebSocket v5.
- `docker/obs/entrypoint.sh`: Inicia PulseAudio, Xvfb y OBS con la cámara virtual habilitada y parámetros personalizables mediante variables de entorno.
- `obs_config/`: Directorio que debe contener los perfiles y escenas de OBS que se replicarán en cada contenedor. Se incluye un `.gitkeep` para mantener la carpeta en el repositorio.
- `docker-compose.yml`: Orquesta múltiples instancias de OBS; el ejemplo expone dos (`obs1`, `obs2`) usando puertos WebSocket 4455 y 4456.

## Requisitos previos en el host

1. **Kernel module v4l2loopback**: Debe estar cargado en el host para que los contenedores puedan exponer cámaras virtuales.

   ```bash
   sudo modprobe v4l2loopback video_nr=0,1 exclusive_caps=1 card_label="obs0","obs1"
   ```

   Verifica los dispositivos disponibles:

   ```bash
   v4l2-ctl --list-devices
   ```

   Ajusta `video_nr` y `card_label` según la cantidad de contenedores que planeas usar.

2. **Docker y Docker Compose**: Asegúrate de tener ambos instalados en tu servidor Ubuntu.

3. **Perfiles de OBS**: Copia tus escenas personalizadas dentro de `obs_config/`. Puedes exportarlas desde una instalación existente de OBS (`~/.config/obs-studio`) y pegarlas aquí. Cada contenedor montará esta carpeta en `/root/.config/obs-studio`.

## Construcción e inicio de contenedores

1. Construye las imágenes y levanta los contenedores definidos en `docker-compose.yml`:

   ```bash
   docker compose up -d --build
   ```

2. Confirma que los contenedores están en ejecución:

   ```bash
   docker compose ps
   ```

3. Cada contenedor publica su propio puerto WebSocket:
   - `obs1` → puerto 4455
   - `obs2` → puerto 4456

   Puedes ajustar puertos y dispositivos modificando `docker-compose.yml`.

## Integración con el script Python

1. Instala las dependencias del proyecto (incluye `obsws-python` para controlar OBS mediante WebSocket):

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Configura tu archivo de configuración (por ejemplo `config.json`) para apuntar a la instancia deseada:

   ```json
   {
     "obs": {
       "host": "obs1",
       "port": 4455,
       "password": "secret"
     }
   }
   ```

   Si ejecutas el script fuera de Docker en el mismo host, puedes usar `localhost` y mapear los puertos publicados (`4455`, `4456`, ...).

3. El script `ActivadorMasivoMovistar_v4l2.py` continúa orquestando Chrome en modo emulación móvil y manipulando la cámara virtual. Para garantizar sesiones aisladas, asegúrate de que Chrome utilice un `--user-data-dir` temporal distinto en cada ejecución.

## Personalización

- Cambia la escena inicial ajustando `OBS_SCENE` en `docker-compose.yml` o al iniciar el contenedor (`OBS_SCENE=OtraEscena`).
- Puedes escalar a más instancias duplicando servicios en `docker-compose.yml` o usando `docker compose up --scale obs=3` con un archivo adicional que parametrice los puertos y dispositivos.
- Para depurar visualmente, puedes conectar `x11vnc` al contenedor y mapear un puerto VNC adicional.

## Apagado y limpieza

Para detener todas las instancias y liberar las cámaras virtuales:

```bash
docker compose down
```

Recuerda descargar los módulos de `v4l2loopback` si ya no los necesitas:

```bash
sudo modprobe -r v4l2loopback
```

## Seguridad

- Cambia `OBS_WEBSOCKET_PASSWORD` en `docker-compose.yml` antes de exponer los puertos fuera de tu red interna.
- Limita el acceso de la red a los puertos WebSocket mediante firewall o redes internas de Docker.

Con esta arquitectura, cada instancia OBS opera en su propio contenedor, controlada mediante WebSocket y conectada a la automatización Selenium sin interferencias entre cámaras virtuales.
