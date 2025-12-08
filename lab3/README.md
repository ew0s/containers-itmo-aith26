# Лабораторная работа №3 — Kubernetes

Полный набор манифестов для развёртывания Nextcloud со связанной БД PostgreSQL в локальном кластере (minikube). В лабораторной задокументированы шаги установки, проверки и ответы на контрольные вопросы из методички.

## Структура каталога

```
lab3/
├─ lab3.pdf                 # методичка
└─ manifests/
   ├─ postgres/
   │  ├─ postgres-configmap.yaml
   │  ├─ postgres-secret.yaml
   │  ├─ postgres-service.yaml
   │  └─ postgres-deployment.yaml
   └─ nextcloud/
      ├─ nextcloud-configmap.yaml
      ├─ nextcloud-secret.yaml
      ├─ nextcloud-service.yaml
      └─ nextcloud-deployment.yaml
```

## Предварительные требования

- ОС с поддержкой виртуализации, установленный `kubectl`
- Minikube с драйвером Docker/VirtualBox/Hyper-V
- Docker Desktop (Windows/macOS) или Docker Engine (Linux)
- Достаточно ресурсов: ≥4 ГБ RAM, ≥2 CPU

## Подготовка к запуску

1. Запустить Docker и убедиться, что он работает (`docker ps`).
2. Запустить кластер: `minikube start --cpus=4 --memory=4g`.
3. Проверить контекст: `kubectl config view --minify`.
4. (Опционально) включить dashboard: `minikube dashboard --url`.

## Применение манифестов

1. При необходимости изменить значения в `postgres-secret.yaml` и `nextcloud-secret.yaml` (логины/пароли).  
2. Создать пространство имён или использовать `default`. В примере используется `default`.
3. Применить ресурсы Postgres:
   - `kubectl apply -f lab3/manifests/postgres/postgres-configmap.yaml`
   - `kubectl apply -f lab3/manifests/postgres/postgres-secret.yaml`
   - `kubectl apply -f lab3/manifests/postgres/postgres-deployment.yaml`
   - `kubectl apply -f lab3/manifests/postgres/postgres-service.yaml`
4. Применить ресурсы Nextcloud:
   - `kubectl apply -f lab3/manifests/nextcloud/nextcloud-configmap.yaml`
   - `kubectl apply -f lab3/manifests/nextcloud/nextcloud-secret.yaml`
   - `kubectl apply -f lab3/manifests/nextcloud/nextcloud-deployment.yaml`
   - `kubectl apply -f lab3/manifests/nextcloud/nextcloud-service.yaml`

> **Почему соблюдаем порядок?** Secrets/ConfigMaps должны существовать до деплойментов, иначе поды не смогут получить переменные окружения и перейдут в состояние `CrashLoopBackOff` до тех пор, пока объекты не появятся.

## Проверка развёртывания

- `kubectl get pods` — оба пода должны быть `Running`, у Nextcloud появятся readiness/liveness пробы.
- `kubectl describe pod postgres-...` / `kubectl describe pod nextcloud-...` — убедиться, что переменные окружения получены корректно.
- `kubectl logs deployment/nextcloud` — наблюдать автоматическую инициализацию Nextcloud.
- `kubectl get svc` — увидеть `postgres-service` и `nextcloud-service` с NodePort 30432 и 30080 соответственно.

### Доступ к веб-интерфейсу

1. Пробросить сервис: `minikube service nextcloud-service --url` (команда откроет URL или предоставит ссылку вида `http://127.0.0.1:XXXXX`).
2. Перейти в браузере по выданному адресу.  
3. Авторизоваться логином `admin` (или указанным в ConfigMap) и паролем из `nextcloud-secret.yaml`.

## Очистка ресурсов

```
kubectl delete -f lab3/manifests/nextcloud/
kubectl delete -f lab3/manifests/postgres/
minikube stop
```

## Ответы на контрольные вопросы

1. **Важен ли порядок применения манифестов?**  
   Да. Сначала должны быть созданы `ConfigMap` и `Secret`, затем `Deployment`, после чего `Service`. Деплойменты считывают конфигурацию при старте контейнера; отсутствие зависимого объекта приводит к ошибкам окружения и перезапускам подов.

2. **Что произойдёт при масштабировании Postgres в 0, затем обратно в 1 и повторной попытке войти в Nextcloud?**  
   При масштабировании до 0 удаляются все поды Postgres, соединение рвётся, Nextcloud переходит в состояние ошибок БД. После возврата реплик к 1 новый под восстановится, но при первом входе Nextcloud может потребовать время на переподключение; сессия станет доступной после того, как приложение повторно установит соединение с БД. Данные не потеряются, потому что в сценарии используется тот же Secret и конфигурация; однако при отсутствии постоянного хранилища (PV/PVC) данные БД будут потеряны, поэтому в продуктиве важно подключать персистентные тома.

## Замечания по дальнейшему развитию

- Добавить `PersistentVolumeClaim` для Postgres и Nextcloud (хранилище файлов).
- Вынести общие значения (например, домены) в отдельный `ConfigMap` и добавить шаблонизацию Helm/Kustomize.
- Настроить Ingress вместо NodePort, когда среда это позволяет.
