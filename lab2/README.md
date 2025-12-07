# Лабораторная №2 — docker-compose стек

## Сервисы

| Service   | Назначение |
|-----------|------------|
| `db`      | PostgreSQL 16 для хранения пользователей и истории сообщений |
| `init-db` | Одноразовый контейнер, применяет Alembic-миграцию и создаёт схему |
| `llm`     | FastAPI + LangChain/Mistral сервис, генерирует рекомендации по транспорту |
| `gateway` | FastAPI-шлюз, общается с Telegram-ботом, хранит историю, вызывает LLM |
| `tg-bot`  | aiogram-бот, общается с пользователем в Telegram |

Общие модели (`shared/`) переиспользуются всеми сервисами. Все Python-зависимости управляются через [uv](https://github.com/astral-sh/uv).

## Подготовка

1. Скопируйте `.env.example` → `.env` и заполните значения, минимум:
   ```bash
   cp lab2/.env.example lab2/.env
   # отредактируйте токен бота и, при необходимости, ключ Mistral
   ```
2. (Опционально) Установите `uv`, чтобы запускать сервисы локально без Docker.

## Запуск

```bash
cd lab2
docker compose up --build
```

Команда поднимет БД, выполнит миграции, запустит LLM, gateway и бота. Переменные `GATEWAY_PORT` и `LLM_PORT` управляют проброшенными портами.

### Тестирование API без Telegram

```bash
curl -X POST http://localhost:${GATEWAY_PORT:-8080}/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
        "telegram_user_id": "local",
        "text": "нужен городской электромобиль до 4 млн",
        "username": "test"
      }'
```

## Ответы на вопросы из задания

1. **Можно ли ограничивать ресурсы в docker-compose.yml (в том числе GPU/CUDA)?**  
   Да. Для CPU/памяти используйте `deploy.resources` (Compose V3+ в Swarm) или `mem_limit`/`cpus` в V2. Пример V3:
   ```yaml
   services:
     gateway:
       deploy:
         resources:
           limits:
             cpus: "0.50"
             memory: 512M
   ```
   Для GPU в Docker Engine 19.03+ можно указать доступ к CUDA-устройствам:
   ```yaml
   services:
     llm:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 capabilities: [gpu]
                 device_ids: ["0"]  # номер нужного GPU
   ```
   Или в режиме standalone:
   ```yaml
   services:
     llm:
       runtime: nvidia
       environment:
         - NVIDIA_VISIBLE_DEVICES=all
         - NVIDIA_DRIVER_CAPABILITIES=compute,utility
   ```
   Главное — чтобы на хосте был установлен NVIDIA Container Toolkit; тогда контейнер сможет использовать CUDA.

2. **Как запустить только один сервис?**  
   Используйте `docker compose up <service>` или `docker compose run --no-deps <service>`. Например, `docker compose up gateway` поднимет только gateway и его зависимости, а `docker compose run --no-deps llm` стартует только LLM (без остальных контейнеров).

## Структура

```
lab2/
├── docker-compose.yml
├── shared/               # Общие Pydantic и SQLAlchemy модели
├── services/
│   ├── gateway/          # FastAPI шлюз + Dockerfile
│   ├── llm/              # LLM сервис на LangChain/Mistral
│   ├── tg-bot/           # aiogram бот
│   └── init-db/          # Alembic миграции
└── README.md
```

## Полезные команды

- `docker compose logs -f gateway` — смотреть логи шлюза
- `docker compose run --rm init-db uv run alembic history` — проверить состояние миграций