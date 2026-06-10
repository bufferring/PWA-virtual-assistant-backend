# 🤖 PWA Virtual Assistant Backend

Backend en **FastAPI** que actúa como proxy inteligente para `llama-server` (llama.cpp), exponiendo una API compatible con OpenAI para un asistente virtual en PWA.

Diseñado para **producción** con streaming SSE, arquitectura desacoplada y despliegue con Podman + systemd + Caddy.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Características

- 🔌 **API compatible con OpenAI**: Endpoints estándar `/v1/chat/completions` y `/v1/models`
- ⚡ **Streaming SSE nativo**: Respuestas en tiempo real desde el LLM
- 🐳 **Desacoplado por capas**: LLM en el host (systemd), API en contenedor (Podman)
- 🚀 **Máximo rendimiento**: Binario nativo con acceso directo a GPU
- 🔒 **Seguro**: Usuario no-root en contenedor, secrets fuera de la imagen
- 📦 **Moderno**: Gestión de paquetes con `uv`, Python 3.12, tipado estricto
- 🛡️ **HTTPS automático**: Caddy como proxy inverso con Let's Encrypt

## 🏗️ Arquitectura

```
┌────────────────────────────────────────────────────────┐
│                      TU SERVIDOR                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐        ┌─────────────────────┐      │
│  │    CADDY     │───────▶│ FastAPI (Podman)    │      │
│  │  :80 / :443  │ :8000  │ puerto 8000         │      │
│  │  (systemd)   │        │ usuario: appuser    │      │
│  └──────────────┘        └──────────┬──────────┘      │
│                                      │                 │
│                                      │ HTTP            │
│                                      │ host.containers │
│                                      │ .internal:8080  │
│                                      ▼                 │
│  ┌──────────────────────────────────────────────┐     │
│  │ llama-server (systemd - binario nativo)      │     │
│  │ puerto 8080 │ GPU acceso directo             │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**¿Por qué esta arquitectura?**

- **llama-server en systemd**: Máximo rendimiento con acceso directo a GPU/CPU sin overhead de contenedor
- **FastAPI en Podman**: Aislamiento del código Python, fácil despliegue y reproducibilidad
- **Caddy como proxy inverso**: HTTPS automático, HTTP/3, y manejo de conexiones persistentes para streaming

## 📋 Requisitos previos

### En el servidor host

- **Linux** (probado en Debian/Ubuntu, Fedora)
- **Podman** >= 4.0 (no Docker, para `host.containers.internal`)
- **Caddy** >= 2.7
- **Python** 3.12+ (solo para desarrollo local)
- **uv** >= 0.4 (gestor de paquetes)
- **llama.cpp** compilado o binario oficial descargado
- **GPU con drivers** (NVIDIA CUDA, AMD ROCm, o Vulkan) - opcional pero recomendado

### Instalar dependencias del sistema

```bash
# Fedora/RHEL
sudo dnf install podman caddy

# Debian/Ubuntu
sudo apt install podman caddy

# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 📁 Estructura del proyecto

```
PWA-virtual-assistant-backend/
├── app/
│   ├── api/
│   │   └── endpoints.py      # Rutas FastAPI (chat, models, health)
│   ├── core/
│   │   ├── config.py         # Configuración con pydantic-settings
│   │   └── schemas.py        # Modelos Pydantic (compatibles OpenAI)
│   ├── services/
│   │   └── llm_service.py    # Cliente HTTP hacia llama-server
│   └── main.py               # App FastAPI + middlewares
├── Containerfile             # Imagen Podman optimizada con uv
├── pyproject.toml            # Dependencias del proyecto
├── uv.lock                   # Lockfile reproducible
├── .python-version           # 3.12
└── README.md
```

## ⚙️ Configuración

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (ya está en `.gitignore`):

```env
# URL del llama-server en el host
LLAMA_SERVER_URL=http://host.containers.internal:8080

# Timeout para respuestas del LLM (segundos)
LLAMA_TIMEOUT=300

# API Key opcional para proteger el endpoint
API_KEY=tu-super-secreto-aqui

# CORS - dominios permitidos (cambia en producción)
CORS_ORIGINS=["https://tu-dominio.com"]
```

> 💡 **Nota**: `host.containers.internal` es el hostname especial de Podman que resuelve al host desde dentro del contenedor.

## 💻 Desarrollo local

### 1. Clonar e instalar

```bash
git clone https://github.com/BufferRing/PWA-virtual-assistant-backend.git
cd PWA-virtual-assistant-backend
uv sync
```

### 2. Iniciar llama-server (en otra terminal)

```bash
./llama-server \
    --model /ruta/a/tu/modelo.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    --ctx-size 4096 \
    --n-gpu-layers 99
```

### 3. Ejecutar FastAPI

```bash
# Para desarrollo local, usa 127.0.0.1 en vez de host.containers.internal
LLAMA_SERVER_URL=http://127.0.0.1:8080 uv run uvicorn app.main:app --reload
```

La API estará en `http://127.0.0.1:8000` y la documentación interactiva en `http://127.0.0.1:8000/v1/openapi.json`.

### 4. Linting y tests

```bash
uv run ruff check .          # Linter
uv run ruff format .         # Formatter
uv run pytest                # Tests
```

## 🚀 Despliegue en producción

### Paso 1: Configurar llama-server como servicio systemd

Crea el archivo `/etc/systemd/system/llama-server.service`:

```ini
[Unit]
Description=LLama.cpp Server
After=network.target

[Service]
Type=simple
User=llama-user
Group=llama-user
WorkingDirectory=/opt/llama-server

ExecStart=/opt/llama-server/llama-server \
    --model /ruta/a/tu/modelo.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --ctx-size 4096 \
    --n-gpu-layers 99 \
    --threads 8

Restart=on-failure
RestartSec=5s
LimitNOFILE=65536
Environment="CUDA_VISIBLE_DEVICES=0"

[Install]
WantedBy=multi-user.target
```

> ⚠️ **Importante**: `--host 0.0.0.0` es necesario para que el contenedor de FastAPI pueda conectarse.

Activar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now llama-server
sudo systemctl status llama-server
```

### Paso 2: Construir y ejecutar el contenedor de FastAPI

```bash
# Construir imagen
podman build -t fastapi-app:latest -f Containerfile .

# Detener contenedor anterior si existe
podman stop fastapi-app 2>/dev/null || true
podman rm fastapi-app 2>/dev/null || true

# Ejecutar nuevo contenedor
podman run -d \
    --name fastapi-app \
    --env-file .env \
    --network slirp4netns:allow_host_loopback=true \
    -p 127.0.0.1:8000:8000 \
    --restart=always \
    fastapi-app:latest
```

**Flags clave explicados:**
- `--env-file .env`: Inyecta las variables sin embeberlas en la imagen
- `--network slirp4netns:allow_host_loopback=true`: Habilita `host.containers.internal`
- `-p 127.0.0.1:8000:8000`: Solo accesible desde localhost (Caddy)
- `--restart=always`: Reinicia si crashea

### Paso 3: Generar servicio systemd para el contenedor (opcional)

```bash
mkdir -p ~/.config/systemd/user/
podman generate systemd --new --name fastapi-app > ~/.config/systemd/user/fastapi-app.service

systemctl --user daemon-reload
systemctl --user enable --now fastapi-app
```

### Paso 4: Configurar Caddy

Edita `/etc/caddy/Caddyfile`:

```caddyfile
tu-dominio.com {
    reverse_proxy localhost:8000 {
        # Crítico para streaming SSE
        flush_interval -1
        
        # Timeouts largos para respuestas de LLM
        transport http {
            keepalive 300s
            keepalive_idle_conns 10
        }
    }
    
    request_body {
        max_size 10MB
    }
}
```

Recargar Caddy:

```bash
sudo systemctl reload caddy
```

## 📡 Endpoints disponibles

### `POST /v1/chat/completions`

Envía mensajes al LLM y recibe respuestas (compatible con OpenAI).

**Request:**
```json
{
  "model": "tu-modelo",
  "messages": [
    {"role": "system", "content": "Eres un asistente útil."},
    {"role": "user", "content": "Hola, ¿cómo estás?"}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": true
}
```

**Response (streaming):**
```
data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"¡Hola"}}]}

data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"!"}}]}

data: [DONE]
```

### `GET /v1/models`

Lista los modelos disponibles en llama-server.

### `GET /v1/health`

Healthcheck para Caddy. Devuelve:
```json
{"status": "healthy", "llm_server": "connected"}
```

### `GET /`

Endpoint raíz de verificación.

## 🐛 Troubleshooting

### El contenedor no puede conectar a llama-server

1. Verifica que llama-server escuche en `0.0.0.0:8080` (no `127.0.0.1`)
2. Prueba desde dentro del contenedor:
   ```bash
   podman exec -it fastapi-app curl http://host.containers.internal:8080/health
   ```
3. Revisa que el contenedor tenga el flag `--network slirp4netns:allow_host_loopback=true`

### El streaming se corta o no funciona

Asegúrate de que tu Caddyfile tenga `flush_interval -1`. Sin esto, Caddy buferiza las respuestas SSE y el cliente no recibe los chunks en tiempo real.

### El healthcheck del contenedor falla

Verifica los logs:
```bash
podman logs fastapi-app
journalctl -u llama-server -f
```

## 📄 Licencia

MIT © 2026 BufferRing. Ver [LICENSE](./LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir cambios importantes.

---

Hecho con ❤️ usando FastAPI, llama.cpp, Podman y Caddy.
