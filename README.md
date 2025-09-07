
# PlayIT auth backend

## Использованные технологии
```
- Python
- FastAPI
- FastAPI Users
- Sqlalchemy
- PostgreSQL
- Docker
- GitHub Actions
```

## Как запустить проект с помощью Docker

### 1. Создайте файл `.env`:
- Скопируйте содержимое файла `example.env` в новый файл с именем `.env`:
  ```bash
  cp example.env .env
  ```
- Измените значения переменных на те, которые вам нужны. **Обязательно смените пароль** в файлах `.env` и `docker-compose.yml`!

### 2. Поднимите сеть `skynet`:
Проект использует внешнюю Docker-сеть `skynet`, чтобы обеспечить взаимодействие между сервисами. Если она ещё не создана, выполните:
```bash
docker network create skynet
```

### 3. Запустите Docker Compose:
```bash
docker-compose up --build
```

### 4. Проверьте доступность приложения:
- Приложение будет доступно по адресу: [http://localhost:8000](http://localhost:8000).
- Документация API: [http://localhost:8000/docs](http://localhost:8000/docs).
