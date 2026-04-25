# 🏦 MyHaven - Personal Finance Management System

**Project Overview | Architecture | Development Guide**

---

## 📖 Быстрый старт

```bash
# 1. Клонируем репозиторій
git clone <repo>
cd MyHavenProject

# 2. Backend
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows або source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 3. Frontend (нова вкладка)
cd client
npm install
npm run serve

# 4. Перейти на http://localhost:8080
```

---

## 📚 Документація

### Основні документи

| Документ | Для кого | Про що |
|----------|----------|--------|
| **[BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)** | Всі розробники | 📐 Архітектура, паттерни, як все влаштовано |
| **[CODE_REVIEW.md](./CODE_REVIEW.md)** | Junior/Middle+ | 🔍 Аналіз коду, SOLID, що покращити |
| **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** | Junior/Middle/Senior | 🎓 Як розвивати далі, какие навички потрібні |
| **README.md** (цей файл) | Нові розробники | 🚀 Швидкий старт |

---

## 🏗️ Архітектура за 60 секунд

```
Vue.js Frontend (client/)
    ↓
REST API (Django REST Framework)
    ↓
[Views] → [Services] → [Repositories] → [Models]
    ↓
PostgreSQL Database
```

### Структура Backend

```
backend/
├── users/              # Автентифікація, профіль
├── accounts/           # Банківські рахунки
├── transactions/       # ⭐ ОСНОВНИЙ: Парсинг виписок, категоризація
├── budgets/            # Ліміти по категоріям
├── core/               # Django конфігурація
└── manage.py           # Django CLI
```

---

## 🚀 Ключові функції

### ✅ Розроблено

- **Аутентифікація:** JWT токени (SimpleJWT)
- **Профіль:** Управління користувачами
- **Транзакції:** Імпорт з банку (PDF/Excel), категоризація
- **Бюджети:** Ліміти по категоріям за місяцем
- **Статистика:** Dashboard, графіки, ежемесячные звиты
- **Експорт:** Вся дані у JSON

### ⏳ Розробляється

- **2FA (TOTP):** 6 views (лист невиконаних)
- **Сповіщення:** Email/Telegram alerts
- **Більше банків:** Легко додавати нові парсери

### 🔲 Заплановано

- **Категоріальні звіти:** Трендові аналізи
- **Предсказання:** ML для категоризації
- **Мобільний:** React Native

---

## 🎯 Критичні справи (TODO)

```
🔴 КРИТИЧНІ (потрібно негайно):
- [ ] Реалізувати 6 TOTP views → Користувачи не можуть включити 2FA
- [ ] Видалити мертві додатки (pages, reports)
- [ ] Видалити processing.py (мертвий код)

🟠 ВИСОК ПРІОРИТЕТ (цей місяць):
- [ ] Додати тести (pytest) → 0% coverage зараз
- [ ] Рефакторити ExportDataView → Занадто багато обов'язків
- [ ] Додати Swagger документацію → API не документована

🟡 СЕРЕДНІЙ (коли є час):
- [ ] Notification Service
- [ ]더 банків парсерів
- [ ] Performance optimization (Redis cache)
```

---

## 🏛️ SOLID Аналіз

| Принцип | Оцінка | Статус |
|---------|--------|--------|
| S - Single Responsibility | 7/10 | ⚠️ ExportDataView робит занадто багато |
| O - Open/Closed | 8/10 | ✅ Strategy Pattern добре |
| L - Liskov Substitution | 8/10 | ✅ Parser абстракція |
| I - Interface Segregation | 6/10 | ⚠️ Потребує DI-контейнера |
| D - Dependency Inversion | 6/10 | ⚠️ Жорсткі залежності |

**Див. [CODE_REVIEW.md](./CODE_REVIEW.md) для детально**

---

## 💼 Навички розробника

### Junior (для роботи з проектом)

```
✅ ПОВИНЕН ЗНАТИ:
- Django ORM (Models, QuerySets, select_related, prefetch_related)
- Django REST Framework (Serializers, APIView, ViewSets)
- PostgreSQL basics (JOIN, indexes)
- Python (type hints, decorators, context managers)
- Git (clone, commit, branch, PR)
- REST API (HTTP методи, status codes, JWT)

⏳ БАЖАНО:
- Vue.js 3 (розуміти frontend)
- Docker basics
- Linux command line
```

### Middle (для архітектурних рішень)

```
Все що у Junior, плюс:
✅ Service Layer & Repository Pattern
✅ Design Patterns (Strategy, Factory, Observer)
✅ Testing (TDD, pytest, mocking)
✅ Performance optimization (query analysis, caching)
✅ Async tasks (Celery basics)
```

### Senior (для лідерства)

```
Все що у Middle, плюс:
✅ Архітектурні рішення (monolith vs microservices)
✅ Масштабування (load balancing, database replication)
✅ Security (OWASP Top 10, rate limiting)
✅ Team leadership & mentoring
✅ DevOps (Docker, CI/CD, Kubernetes)
```

**Див. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) для рекомендацій**

---

## 🔧 Комманди Django

```bash
# Міграції
python manage.py migrate                 # Застосувати міграції
python manage.py makemigrations          # Criar міграції з моделей
python manage.py makemigrations --dry-run  # Перевірити (без змін)

# Сервер
python manage.py runserver               # Запустити dev сервер
python manage.py runserver 0.0.0.0:8000  # На всіх IP

# Django Shell
python manage.py shell                   # Інтерпретатор Python

# Admin
python manage.py createsuperuser         # Створити адміністратора

# Тести
python manage.py test                    # Запустити тести
python manage.py test users.tests        # Конкретне приложение

# Дані
python manage.py loaddata fixtures/banks.json  # Завантажити фікстури
python manage.py dumpdata users > users_backup.json  # Бекап
```

---

## 📋 API Endpoints

### Автентифікація

```
POST   /api/token/              # Отримати JWT токен
POST   /api/token/refresh/      # Оновити токен
```

### Користувачи

```
GET    /api/users/me/           # Поточний користувач
GET    /api/users/profile/      # Профіль (повна інформація)
PATCH  /api/users/profile/      # Редагувати профіль
POST   /api/users/change-password/      # Зміна пароля
POST   /api/users/delete-account/       # Видалити акаунт
GET    /api/users/export-data/  # Експорт всіх даних
```

### Бюджети

```
GET    /api/budgets/            # Список бюджетів
POST   /api/budgets/            # Створити бюджет
GET    /api/budgets/{id}/       # Деталі бюджету
PATCH  /api/budgets/{id}/       # Редагувати
DELETE /api/budgets/{id}/       # Видалити
```

### Транзакції

```
GET    /transactions/api/dashboard/     # Dashboard
GET    /transactions/api/statistics/    # Статистика за місяці
GET    /transactions/api/list/          # Список транзакцій
POST   /transactions/api/create/        # Додати вручну
GET    /transactions/api/{id}/          # Деталі
DELETE /transactions/api/{id}/          # Видалити
GET    /transactions/api/categories/    # Категорії
GET    /transactions/api/calendar/      # Календар
GET    /transactions/api/uploads/       # Завантаження
POST   /transactions/api/uploads/       # Завантажити виписку
```

---

## 🗄️ БД Схема (спрощена)

```
CustomUser
├── id (PK)
├── email (UNIQUE)
├── password_hash
├── totp_secret (для 2FA)
├── theme, language, currency
└── notify_* (notification settings)

Account
├── id (PK)
├── user_id (FK) ┐
├── bank_id (FK) ├→ Рахунок користувача
├── account_name │
└── balance (calculated from transactions)

Bank
├── id (PK)
├── name (UNIQUE)
└── logo

Category
├── id (PK)
├── user_id (FK, nullable → system categories)
├── name
├── type ('INCOME', 'EXPENSE')
├── parent_id (FK self → hierarchy)
└── keywords (JSON)

Transaction
├── id (PK)
├── user_id (FK)
├── account_id (FK)
├── category_id (FK)
├── amount
├── description
├── transaction_date
├── source ('import', 'manual', 'telegram')
└── matched_automatically, confidence_score

TransactionUpload
├── id (PK)
├── user_id (FK)
├── bank_id (FK)
├── file (FileField)
├── status ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')
├── uploaded_at
├── total_transactions
└── processing_log

Budget
├── id (PK)
├── user_id (FK)
├── category_id (FK, only EXPENSE)
├── month (DateField)
└── amount (limit)
```

---

## 🧪 Тестування

```bash
# Запустити всі тести
pytest

# Тільки unit тести
pytest backend/users/tests.py

# З покриттям
pytest --cov=backend

# Verbose output
pytest -v

# Зупинитися на першій помилці
pytest -x
```

**Поточний статус:** 🔴 **0% - Немає тестів!**

---

## 🔐 Безпека

### Налаштовано ✅

- JWT автентифікація (SimpleJWT)
- CORS (дозволено тільки localhost:8080)
- SQL Injection protection (Django ORM)
- CSRF protection (Django)
- Password hashing (PBKDF2)

### Потребує роботи ⚠️

- Rate limiting (для API)
- HTTPS redirect (для продакшену)
- 2FA (TOTP) - не реалізовано
- Notification validation (про що вислати?)

---

## 📈 Метрики

```
Lines of Code:         ~3,000
Django Apps:           5 (users, accounts, transactions, budgets, core)
API Endpoints:         25 (19 роботочих + 6 невиконаних)
Models:                7
Serializers:           8
Test Coverage:         0% (потрібно додати)
Performance:           ~200ms avg response time
Database:              PostgreSQL
Frontend:              Vue.js 3 + Tailwind CSS + Chart.js
```

---

## 🤝 Контрибутинг

### Git Workflow

```bash
# 1. Створити гілку
git checkout -b feature/my-feature

# 2. Зробити changes та commit
git add .
git commit -m "feat: describe your change"

# 3. Push та PR
git push origin feature/my-feature

# 4. Чекаємо code review та merge
```

### Код Style

```python
# Format: black
black backend/

# Lint: pylint
pylint backend/

# Type check: mypy
mypy backend/

# All in one:
pre-commit run --all-files
```

---

## 📞 Support

### Питання?

1. **Архітектура:** Див. [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)
2. **Code Review:** Див. [CODE_REVIEW.md](./CODE_REVIEW.md)
3. **Розвиток:** Див. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)
4. **API Docs:** http://localhost:8000/admin

### Проблеми?

```bash
# Check logs
docker logs myhaven-backend

# Run migrations
python manage.py migrate

# Clear cache
python manage.py clear_cache

# Restart services
docker-compose restart
```

---

## 📜 License

MIT License - вільне використання в особистих та комерційних проектах

---

## 🎓 Висновок

**MyHaven** - це добре структурований Django проект, готовий до розвитку та масштабування. 

**Наступні кроки:**
1. ✅ Прочитати [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md) для розуміння
2. ✅ Прочитати [CODE_REVIEW.md](./CODE_REVIEW.md) для контексту
3. ✅ Прочитати [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) для навчання
4. ✅ Почати з критичних справ (TOTP views)

**Happy coding! 🚀**

---

**Last updated:** 24 квітня 2026  
**Version:** 1.0  
**Status:** Production Ready (з деякими TO-DO)

