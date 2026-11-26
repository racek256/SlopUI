FROM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates jq \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install MCPs
## Lightpanda
RUN curl -fsSL https://pkg.lightpanda.io/install.sh | bash
RUN cp /root/.local/bin/lightpanda /usr/local/bin/lightpanda

COPY backend/ ./
COPY --from=frontend /app/dist ./static
EXPOSE 8000
CMD ["python3", "main.py"]
