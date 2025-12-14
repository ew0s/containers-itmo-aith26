# Лабораторная №4 — More Kubernetes

В этой работе мы переносим сервисы из `lab2` (gateway + LLM + миграции + PostgreSQL) в кластер Kubernetes.  
Архитектура развёртывания:

| Требование ЛР4 | Реализация |
| --- | --- |
| ≥2 Deployment'ов | `postgres`, `llm`, `gateway`, `tg-bot` |
| Кастомный образ | `lab4/gateway`, `lab4/llm`, `lab4/init-db` (собираются из Dockerfile'ов `lab2`) |
| InitContainer внутри Deployment | `gateway` запускает `lab4/init-db` для Alembic миграций и ждёт готовности зависимостей |
| Volume в Deployment | `postgres` монтирует PVC `postgres-data` |
| ConfigMap / Secret | см. `01-configmaps.yaml`, `02-secrets.yaml` |
| Service | `postgres-service`, `llm-service`, `gateway-service` |
| Liveness/Readiness | HTTP-пробы для `llm` и `gateway`, `pg_isready` для `postgres` |
| Пользовательские лейблы | `lab`, `tier`, `component` во всех ресурсах |

## Подготовка образов

Собираем образы из исходников `lab2` (каждый содержит собственный Dockerfile).  
Пример сборки и загрузки в Minikube:

```bash
cd lab2
docker build -t lab4/gateway:latest -f services/gateway/Dockerfile .
docker build -t lab4/llm:latest -f services/llm/Dockerfile .
docker build -t lab4/init-db:latest -f services/init-db/Dockerfile .
docker build -t lab4/tg-bot:latest -f services/tg-bot/Dockerfile .

# чтобы кластер Minikube видел образы:
minikube image load lab4/gateway:latest -p lab4
minikube image load lab4/llm:latest -p lab4
minikube image load lab4/init-db:latest -p lab4
minikube image load lab4/tg-bot:latest -p lab4
```

> Если используется другой профиль/драйвер, замените `-p lab4` на свой.

### Сборка прямо внутри Minikube

Чтобы не пушить образы во внешние реестры, можно собрать их сразу в профиле Minikube:

```bash
# 1. Обновляем lock-файлы (uv создаёт формат TOML, который понимают Dockerfile'ы)
cd lab2/services/gateway && uv lock
cd ../llm && uv lock
cd ../init-db && uv lock
cd ../tg-bot && uv lock

# 2. Стартуем профиль (пример — qemu2, 4 CPU/4 ГБ RAM)
minikube start -p lab4 --cpus=4 --memory=4g --disk-size=30g --driver=qemu

# 3. Сборка внутри VM; контекст — весь каталог lab2
cd /Users/byebye/Documents/AITH_master/containers_2026/containers-itmo-aith26
minikube image build -p lab4 -t lab4/gateway:latest -f services/gateway/Dockerfile lab2
minikube image build -p lab4 -t lab4/llm:latest     -f services/llm/Dockerfile     lab2
minikube image build -p lab4 -t lab4/init-db:latest -f services/init-db/Dockerfile lab2
minikube image build -p lab4 -t lab4/tg-bot:latest  -f services/tg-bot/Dockerfile  lab2
```

После этого Kubernetes-поды в профиле `lab4` смогут использовать теги `lab4/*:latest` без дополнительных `image load`.

## Настройка секретов и конфигов

1. Отредактируйте `lab4/manifests/02-secrets.yaml` (пароли БД, API-ключ Mistral, `BOT_TOKEN` Telegram-бота).  
   > Если оставить значение по умолчанию, контейнер `tg-bot` не будет запускать polling и останется в ожидании (см. логи).
2. При необходимости измените значения в `lab4/manifests/01-configmaps.yaml`  
   (имя БД, `LLM_SERVICE_URL`, логирование и т.п.).

## Развёртывание

```bash
kubectl apply -f lab4/manifests/00-namespace.yaml
kubectl apply -f lab4/manifests/01-configmaps.yaml
kubectl apply -f lab4/manifests/02-secrets.yaml
kubectl apply -f lab4/manifests/10-postgres.yaml
kubectl apply -f lab4/manifests/20-llm.yaml
kubectl apply -f lab4/manifests/30-gateway.yaml
kubectl apply -f lab4/manifests/40-tg-bot.yaml

kubectl get pods -n lab4
```

Инициализация происходит автоматически:

- `postgres` получает PVC и стартует с liveness-пробой `pg_isready`;
- `gateway` прогоняет Alembic миграции через init-контейнер `lab4/init-db`,
  ждёт готовности Postgres и LLM, затем запускает FastAPI;
- `llm` выставляет REST API на `9000` и отдает `/healthz`.

## Тестирование

```bash
# Проверяем внутренний доступ к статусу
kubectl -n lab4 run curl --rm -it --image=curlimages/curl \
  -- curl -s http://gateway-service.lab4.svc.cluster.local:8080/healthz

# Для локального доступа без ingress (в драйвере qemu2 service-туннель недоступен):
kubectl -n lab4 port-forward svc/gateway-service 8080:8080
curl -X POST http://127.0.0.1:8080/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id":"local","username":"demo","text":"нужен электромобиль"}'

# Логи Telegram-бота
kubectl logs -n lab4 deployment/tg-bot -f
```

## Очистка

```bash
kubectl delete -f lab4/manifests --ignore-not-found
kubectl delete namespace lab4 --ignore-not-found
```

## Скриншоты

**Билд контейнеров внутри minikube**

<img width="971" height="935" alt="image" src="https://github.com/user-attachments/assets/1bae6d89-c8b1-45cd-92d9-41787ab8cd17" />

**Манифесты**

<img width="1002" height="117" alt="image" src="https://github.com/user-attachments/assets/dbf40fd3-cf43-4855-adfc-860e5e3ba99f" />

**Статус Подов**

<img width="831" height="102" alt="image" src="https://github.com/user-attachments/assets/690818ca-c1e4-4cc4-8ed0-09161efb6183" />
<img width="820" height="100" alt="image" src="https://github.com/user-attachments/assets/224f1682-1343-4b94-aeba-41419adfedae" />

**Лог гейтвея**

<img width="923" height="118" alt="image" src="https://github.com/user-attachments/assets/7ee6d146-1602-4f0d-afd5-f2fe3b79bbb9" />

**Лог ТГ Бота**

<img width="1010" height="115" alt="image" src="https://github.com/user-attachments/assets/5a83d1ef-ea7f-4708-9fe3-fec126f73180" />

**Удаление и очистка**

<img width="1015" height="254" alt="image" src="https://github.com/user-attachments/assets/64f33186-bc15-4fb0-a171-8a654c095bb5" />

**Локальынй вызов**
<img width="1081" height="149" alt="image" src="https://github.com/user-attachments/assets/00774cd5-07cb-4417-8304-0d5328449401" /> 
<img width="1710" height="87" alt="image" src="https://github.com/user-attachments/assets/e52be608-9fa6-4453-abdb-1d8a1c674592" />
