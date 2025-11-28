#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "${SCRIPT_DIR}/..")"

cd "${PROJECT_ROOT}"

ENV_FILE=".env.production"
COMPOSE_FILE="docker-compose.prod.yml"

if [ ! -f "${ENV_FILE}" ]; then
  echo "Env file ${ENV_FILE} not found. Copy .env.production.example and fill it."
  exit 1
fi

echo "Building and starting services..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build

echo "Services started. Status:"
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps
