# Local deployment candidate only. Pin reviewed base-image digests before release.
FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FREIGHTGUARD_MODEL_PATH=/models/pipeline.joblib FREIGHTGUARD_CORS_ORIGINS=""
WORKDIR /app
COPY requirements/runtime.txt /app/requirements/runtime.txt
RUN pip install --no-cache-dir -r requirements/runtime.txt
COPY pyproject.toml README.md /app/
COPY src/freightguard /app/src/freightguard
RUN pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "uvicorn", "freightguard.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-server-header", "--no-proxy-headers"]

FROM node:24-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY docs/ /app/docs/
ARG VITE_API_BASE_URL=http://127.0.0.1:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:stable-alpine AS frontend
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/frontend/dist/ /usr/share/nginx/html/
EXPOSE 8080
