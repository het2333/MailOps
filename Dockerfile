FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/backend/.venv/bin:$PATH" \
    STATIC_DIR=/app/static \
    DEMO_MODE=true \
    DATABASE_URL=sqlite:////tmp/mailops-demo.db \
    PORT=8000
WORKDIR /app/backend
RUN pip install --no-cache-dir uv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ ./
COPY --from=frontend-build /build/frontend/dist /app/static
EXPOSE 8000
CMD ["/bin/sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
