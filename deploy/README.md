# Развертывание на Ubuntu 24.04

1) Подключиться к серверу  
```bash
ssh root@89.104.74.234
apt update && apt install -y git
git clone <ссылка-на-репозиторий> app && cd app
```

2) Подготовить переменные окружения  
```bash
cp .env.production.example .env.production
nano .env.production  # заполнить
```
Нужно указать:
- `POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB` — учётка БД.
- `SECRET_KEY` — длинная случайная строка.
- `CORS_ORIGINS` — список разрешённых origin (например, `http://your-domain`).
- `OPENROUTER_API_KEY` (и дополнительные `OPENROUTER_API_KEY_2` при необходимости).
- `MODEL` и `MODEL_ANALYSIS` — ID моделей в OpenRouter.
- `VITE_API_URL` и `VITE_API_BASE_URL` — по умолчанию `/api` (фронт ходит через nginx к бэкенду).

3) Установить Docker и compose-плагин  
```bash
chmod +x deploy/install_docker.sh
sudo ./deploy/install_docker.sh
```

4) Собрать и запустить стек  
```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```
Результат:  
- фронт: http://89.104.74.234/  
- API (проксируется через nginx): http://89.104.74.234/api  
- Swagger: http://89.104.74.234/api/docs

5) Проверка и логи  
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

6) DNS  
Добавьте A-запись вашего домена на IP `89.104.74.234` в панели DNS (ns5.hosting.reg.ru, ns6.hosting.reg.ru). После делегирования сайт будет доступен по доменному имени.

7) Перезапуск/обновление  
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml down  # остановить при необходимости
```

Данные БД и Redis хранятся в docker volume (`postgres_data`, `redis_data`), они сохранятся между перезапусками контейнеров.
