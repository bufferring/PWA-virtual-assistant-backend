FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Crear usuario no-root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Habilitar bytecode compilation y otras optimizaciones de uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copiar archivos de configuración PRIMERO (para cacheo óptimo)
COPY pyproject.toml uv.lock ./

# Instalar dependencias (cacheado por capas)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copiar el código fuente
COPY app/ ./app/
COPY main.py ./

# Instalar el proyecto completo
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Cambiar propietario
RUN chown -R appuser:appuser /app
USER appuser

# Poner los binarios del venv en el PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx, sys; httpx.get('http://localhost:8000/health').raise_for_status() or sys.exit(0)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop", "--http", "httptools"]
