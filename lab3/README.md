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

1. Пробросить сервис: `kubectl port-forward svc/nextcloud-service 8080:80`. Перейти по адресу `http://127.0.0.1:8080/login`
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
   При масштабировании до 0 удаляются все поды Postgres, соединение рвётся, Nextcloud переходит в состояние ошибок БД. После возврата реплик к 1 создаётся новый под, и Nextcloud сможет переподключиться к БД. Однако **данные будут потеряны**, так как в текущей конфигурации не используется постоянное хранилище (PV/PVC) — данные хранились внутри контейнера и были удалены вместе с подом. Nextcloud потребует повторной инициализации. В продуктиве необходимо использовать PersistentVolume для сохранения данных между перезапусками.

## Скриншоты логов

Запуск
![telegram-cloud-photo-size-2-5307933310292004172-y](https://github.com/user-attachments/assets/42d5394d-ae77-465c-b455-62c1b40b894d)

Проверка подов
<img width="1580" height="146" alt="telegram-cloud-document-2-5307933309832038450" src="https://github.com/user-attachments/assets/0c27d0b2-70dd-4695-9a4c-2e50dcd4daff" />

Проброс порта
![telegram-cloud-photo-size-2-5307933310292004173-y](https://github.com/user-attachments/assets/3ffcf846-b581-418a-a765-a9152695708d)

Скриншот из самого клауда
![telegram-cloud-photo-size-2-5307933310292004164-y](https://github.com/user-attachments/assets/87ba70bf-f0d6-409f-8c63-d899d58017e3)

Другие скриншоты и команды
<img width="754" height="87" alt="image" src="https://github.com/user-attachments/assets/8df2b26e-1792-4896-b6d5-af7ec64610ca" />

<img width="792" height="895" alt="image" src="https://github.com/user-attachments/assets/9ab7a028-4991-4c10-9e6b-0ec8affc8a3d" />

<img width="973" height="283" alt="image" src="https://github.com/user-attachments/assets/2cc7a443-85f3-4f3a-b49d-758448eabe0f" />
