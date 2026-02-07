# Предпроф олимпиада "Платформа для подготовки к олимпиадам"
Команда IT1409. Предпроф олимпиада по Информационным технологиям. Кейс "Платформа для подготовки к олимпиадам". Участники команды: Болгаренко Матвей, Гонопольский Максим, Погиба Иван, Якупов Амир

Скопировать

Olymp Platform — платформа для подготовки к олимпиадам

Видео-демо проекта: https://rutube.ru/video/private/876e78430d4050cc1d49b0e60af094c6/?p=hT5FdQmjtPEEFVQzrNtrmA

---

О проекте

Olymp Platform — веб-платформа для подготовки к олимпиадам: банк задач, тренировочный режим, аналитика прогресса, PvP-матчи в реальном времени и генерация новых задач на основе шаблонов и локальной LLM.

---

Функциональность

Банк задач
- Фильтрация по предмету, теме и сложности
- Решение задач онлайн
- Подсказки к задачам
- Автопроверка ответа

Тренировка
- Сохранение попыток решения (верно/неверно)
- Учет времени решения
- История попыток

Аналитика
- Количество решений, точность, среднее время
- Отчетность по темам
- График прогресса по дням

PvP
- Матчмейкинг
- WebSocket-синхронизация состояния матча
- Таймер, счёт, статусы ответов
- Elo-рейтинг и история матчей

Генерация задач
- Шаблоны задач (ProblemTemplate)
- Генерация новых задач и сохранение в общий банк

Админ-панель
- Управление задачами, шаблонами, матчами, попытками
- Импорт/экспорт данных (CSV/JSON)

---

Технологический стек

Backend
- Python
- Django
- Django REST Framework
- Django Channels (ASGI/Daphne)

Инфраструктура
- PostgreSQL
- Redis
- Docker (для Redis)

Frontend
- Django Templates
- HTML/CSS
- JavaScript

LLM (локально)
- Ollama

---

Запуск проекта

1) Установка зависимостей

python -m venv .venv
Windows: .venv\Scripts\activate
Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

2) PostgreSQL

Настройки подключения задаются в olymp_platform/settings.py (DATABASES).  
Пример параметров:
- NAME: olymp_db
- USER: postgres
- PASSWORD: пароль
- HOST: localhost
- PORT: 5432

3) Redis (Docker)

docker run --name redis -p 6379:6379 -d redis

4) Миграции и запуск

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

Адреса:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/admin

---

API

Получить токен
POST /api/auth/token/
Поля: username, password

Пример:
curl -X POST http://127.0.0.1:8000/api/auth/token/ -d "username=USER&password=PASS"

Список задач
GET /api/problems/
Заголовок: Authorization: Token YOUR_TOKEN

Пример:
curl http://127.0.0.1:8000/api/problems/?subject=math -H "Authorization: Token YOUR_TOKEN"

Конкретная задача
GET /api/problems/<id>/
Пример:
curl http://127.0.0.1:8000/api/problems/12/ -H "Authorization: Token YOUR_TOKEN"

Отправка решения
POST /api/problems/<id>/submit/
Пример:
curl -X POST http://127.0.0.1:8000/api/problems/12/submit/ -H "Authorization: Token YOUR_TOKEN" -H "Content-Type: application/json" -d "{\"answer\":\"5\",\"time_spent\":12.7}"

---

Авторы

Команда: Болгаренко Матвей, Гонопольский Максим, Погиба Иван, Якупов Амир. 

---
