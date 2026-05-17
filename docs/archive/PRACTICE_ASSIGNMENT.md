# ЗАВДАННЯ ПРОГРАМИ ПЕРЕДДИПЛОМНОЇ ПРАКТИКИ
## MyHaven — Система управління особистими фінансами

**Дата:** травень 2026 | **Версія:** 1.0 | **Статус:** Активний

---

## 📋 ЗМІСТ
1. [Ознайомлення з діяльністю підприємства](#1-ознайомлення-з-діяльністю-підприємства)
2. [Ознайомлення з програмними засобами](#2-ознайомлення-з-програмними-засобами)
3. [Опис та аналіз компонентів середовища розробки](#3-опис-та-аналіз-компонентів-середовища-розробки)
4. [Створення специфікації та документації](#4-створення-специфікації-та-документації)
5. [Створення технічної документації функціоналу](#5-створення-технічної-документації-функціоналу)
6. [Перелік інструментів та технологій](#додаток-перелік-інструментів-та-технологій)

---

# 1. ОЗНАЙОМЛЕННЯ З ДІЯЛЬНІСТЮ ПІДПРИЄМСТВА

## 1.1. Природа та мета проекту

**MyHaven** — це інноваційна система управління особистими фінансами, розроблена для допомоги користувачам у:
- Імпорту та аналізу банківських виписок з різних форматів (PDF, Excel)
- Автоматичної категоризації фінансових транзакцій
- Отримання аналітичних звітів та KPI (Key Performance Indicators)
- Управління бюджетами та контролю видатків
- Інтеграції з популярними месенджерами (Telegram Bot API)

## 1.2. Установчі документи та структура управління

### Архітектурні принципи проекту

Проект розроблений на основі таких ключових принципів:

**1. Service Layer Pattern** — вся бізнес-логіка зосереджена в сервісних класах, відділена від логіки представлення та доступу до даних.

**2. Repository Pattern** — доступ до бази даних здійснюється через спеціалізовані репозиторії, що забезпечує централізовану обробку ORM-запитів.

**3. SOLID Принципи** — код дотримується принципів:
- **S**ingle Responsibility — кожен клас має одну відповідальність
- **O**pen/Closed — код відкритий до розширення, але закритий для модифікації
- **L**iskov Substitution — коректна підстановка типів
- **I**nterface Segregation — залежність від інтерфейсів, не імплементацій
- **D**ependency Inversion — залежності від абстракцій

**4. Test-Driven Development (TDD)** — розробка функціоналу починається з написання тестів (Red → Green → Refactor).

### Структура проекту

```
MyHavenProject/
├── backend/                        # Django REST API
│   ├── core/                       # Django конфігурація
│   ├── users/                      # Управління користувачами та автентифікацією
│   ├── accounts/                   # Банківські рахунки та організації-банки
│   ├── transactions/               # Основна бізнес-логіка (парсинг, категоризація, KPI)
│   ├── budgets/                    # Управління бюджетами
│   ├── telegram_api/               # API для Telegram Bot
│   ├── tests/                      # Інтеграційні тести
│   └── requirements.txt            # Python залежності
│
└── client/                         # Vue.js фронтенд
    ├── src/
    │   ├── components/             # Переиспользуемые компоненти
    │   ├── views/                  # Сторінки (Pages)
    │   ├── stores/                 # State management (Pinia)
    │   └── router/                 # Маршрутизація
    └── public/                     # Статичні активи
```

## 1.3. Основні напрямки діяльності

### Ключові функціональні можливості

| Функціональність | Статус | Описання |
|-----------------|--------|---------|
| **Автентифікація користувачів** | ✅ Реалізовано | JWT токени, підтримка 2FA (TOTP) |
| **Імпорт банківських виписок** | ✅ Реалізовано | Обробка PDF, Excel форматів |
| **Автоматична категоризація** | ✅ Реалізовано | Розумне відповідання по ключовим словам |
| **Управління рахунками** | ✅ Реалізовано | Додавання кількох банківських рахунків |
| **Контроль бюджетів** | ✅ Реалізовано | Встановлення лімітів по категоріям |
| **Аналітичні звіти** | ✅ Реалізовано | KPI, статистика видатків |
| **Telegram Bot API** | ✅ Реалізовано | Інтеграція з Telegram мессенджером |
| **Користувацькі налаштування** | ✅ Реалізовано | Тема, мова, валюта, сповіщення |

---

# 2. ОЗНАЙОМЛЕННЯ З ПРОГРАМНИМИ ЗАСОБАМИ

## 2.1. Інфраструктура розробки та операційні системи

### Backend інфраструктура

**Django 5.2** — веб-фреймворк для розробки серверної частини:
- Django REST Framework (DRF) — для створення REST API
- SimpleJWT — для управління JWT автентифікацією
- drf-spectacular — для генерації OpenAPI/Swagger документації

**PostgreSQL** — реляційна база даних для збереження:
- Даних користувачів та облікових записів
- Фінансових транзакцій
- Категорій та бюджетів
- Налаштувань користувачів

**Python 3.x** — мова програмування з:
- Type hints для статичної типізації
- Dependency Injection для управління залежностями
- Декораторами для функціональної розширюваності

### Frontend інфраструктура

**Vue.js 3** — прогресивний JavaScript фреймворк для розробки:
- SPA (Single Page Application) з маршрутизацією
- Компонентної архітектури
- Реактивності даних

**Tailwind CSS** — утилітарна бібліотека для стилізації:
- Сучасного, адаптивного дизайну
- Швидкої розробки інтерфейсів без написання CSS

**Pinia** — проста система управління станом:
- Глобального стану додатку
- Перехідних даних між сторінками

## 2.2. Управління версіями та контроль якості коду

### Git та GitHub

- **Git** — система контролю версій для відстеження всіх змін в коді
- **GitHub** — платформа для хостингу репозиторію та спільної розробки
- **Гілки** — розділення розробки (main, develop, feature/*, bugfix/*)

### Інструменти контролю якості

**Black** — автоматичний форматер коду:
- Забезпечує однаковий стиль форматування
- Дотримання PEP 8 стандартів

**Ruff** — швидкий linter для Python:
- Перевірка лінтингових помилок
- Виявлення неви́користаних імпортів
- Вилучення несправних конструкцій

**pytest** — фреймворк для автоматизованого тестування:
- Unit тести для окремих функцій
- Інтеграційні тести для взаємодії модулів
- Регресійне тестування перед комітом

## 2.3. Телекомунікаційні та комунікаційні програми

### Telegram Bot API

Система містить вбудовану інтеграцію з Telegram для:
- Отримання звітів про видатки
- Сповіщень про перевищення бюджету
- Швидкого доступу до KPI

**Endpoints:**
- `GET /api/telegram/health/` — перевірка стану API
- `GET /api/telegram/dashboard/` — дашборд користувача
- `GET /api/telegram/categories/` — список категорій
- `GET /api/telegram/budgets/` — статус бюджетів

### REST API та документація

**OpenAPI/Swagger UI** — інтерактивна документація API:
- Доступна на `http://localhost:8000/api/docs/`
- Дозволяє тестувати endpoints прямо з браузера
- Автоматично генерується з коду

## 2.4. Системи моніторингу та аналітики

### Аналіз даних та звітність

**Dashboard KPI** — система показників ефективності:

```
GET /api/transactions/dashboard/
{
    "total_income": 5000.00,          # Загальний прибуток
    "total_expenses": 3200.50,        # Загальні видатки
    "net_balance": 1799.50,           # Чистий баланс
    "categories_breakdown": {...},    # Розподіл по категоріям
    "monthly_trend": {...},           # Тренд за місяцями
    "budget_status": {...}            # Статус бюджетів
}
```

**Категоризація транзакцій** — розумне розподілення видатків:
- Автоматичне відповідання по ключовим словам
- Налаштування категорій користувачем
- Можливість ручного перевизначення

### Безпека та зберігання даних

**JWT токени** — для безпечної автентифікації:
- Access токен з коротким TTL
- Refresh токен для оновлення
- Захист CSRF атак

**2FA (TOTP)** — двофакторна автентифікація:
- Інтеграція з Google Authenticator
- QR-коди для налаштування
- Backup коди при втраті пристрою

**Шифрування паролів** — захист облікових записів:
- Хешування з PBKDF2
- Сіль для запобігання rainbow table атак

---

# 3. ОПИС ТА АНАЛІЗ КОМПОНЕНТІВ СЕРЕДОВИЩА РОЗРОБКИ

## 3.1. Введення

Під час проходження переддипломної практики було ознайомлено з сучасними інструментами розробки програмного забезпечення, які були використані у процесі реалізації дипломного проєкту **"MyHaven — Система управління особистими фінансами"**.

Проект демонструє комплексне застосування Agile методик, Test-Driven Development, та сучасної багатошарової архітектури у розробці масштабованого фінансового додатку.

## 3.2. Компоненти візуального середовища розробки

### 3.2.1 IDE та редактори коду

#### Visual Studio Code (VSCode)

**Призначення:** Основний редактор для розробки фронтенду (Vue.js, JavaScript) та конфігураційних файлів.

**Ключові можливості:**
- Інтегрована підтримка Git та GitHub
- Розширення для Vue.js розробки (Vetur, Vue Language Features)
- Live Server для тестування змін в режимі реального часу
- Встроєний терміналл для запуску команд
- IntelliSense для автозаповнення коду

**Налаштування проекту:**
```json
// .vscode/settings.json
{
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "[vue]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    }
}
```

#### PyCharm (або VSCode + Pylance)

**Призначення:** Розробка серверної частини на Python (Django).

**Ключові можливості:**
- Глибокий аналіз Python коду з типізацією
- Вбудований debugger для налагодження
- Інтеграція з Django ORM та миграціями
- Підтримка виртуальних середовищ (venv, virtualenv)
- Рефакторинг коду з автоматичним оновленням посилань

**Налаштування проекту:**
```bash
# Вибір Python інтерпретера у PyCharm
# Settings → Project → Python Interpreter → backend/.venv/Scripts/python.exe
```

### 3.2.2 Система управління проєктами та версіями

#### Git та GitHub

**Git** — розподілена система контролю версій:

```bash
# Базові команди
git clone https://github.com/user/MyHavenProject.git
git checkout -b feature/new-feature
git add backend/transactions/services.py
git commit -m "feat(transactions): add budget analysis service"
git push origin feature/new-feature
git pull origin main  # Синхронізація з основною гілкою
```

**GitHub** — платформа для спільної розробки:
- Pull Request Reviews для перевірки коду
- Issues для відстеження завдань
- Actions для CI/CD автоматизації
- Wiki для документації

#### Структура гілок

```
main                    # Продакшн версія
├── develop            # Розробка версія
│   ├── feature/auth   # Нова функція
│   ├── feature/budget # Нова функція
│   └── bugfix/issue-1 # Виправлення помилки
└── hotfix/urgent-fix  # Критична виправка
```

### 3.2.3 Бази даних та управління даними

#### PostgreSQL

**Призначення:** Основне сховище даних для серверної частини.

**Архітектура бази:**

```sql
-- Основні таблиці
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    totp_secret VARCHAR(32),
    totp_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bank_name VARCHAR(100),
    account_number VARCHAR(34),
    balance DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'UAH',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2),
    category_id INTEGER REFERENCES categories(id),
    transaction_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    type VARCHAR(10),  -- 'INCOME' або 'EXPENSE'
    is_system BOOLEAN DEFAULT FALSE,
    keywords TEXT[]  -- PostgreSQL array для пошуку
);
```

**Інструменти управління:**
- **pgAdmin** — графічний інтерфейс для адміністрування
- **DBeaver** — універсальний інструмент управління БД

### 3.2.4 Контейнеризація та DevOps

#### Docker (планується)

```dockerfile
# Dockerfile для backend
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

#### Docker Compose (планується)

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myhaven
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./client
    ports:
      - "3000:3000"
```

### 3.2.5 Тестування та контроль якості

#### Фреймворк для тестування (pytest)

**Призначення:** Автоматизована перевірка коректності коду.

```python
# backend/transactions/tests.py
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from transactions.models import Transaction, Category
from transactions.services import TransactionService

class TestTransactionService:
    
    @pytest.fixture
    def test_user(self):
        """Фікстура для створення тестового користувача."""
        User = get_user_model()
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Pass1234!'
        )
    
    def test_calculate_monthly_expenses(self, test_user):
        """Тест для функції обчислення видатків за місяць."""
        # Arrange (підготовка)
        service = TransactionService()
        category = Category.objects.create(
            user=test_user,
            name='Food',
            type='EXPENSE'
        )
        
        # Act (виконання)
        result = service.calculate_monthly_expenses(
            user=test_user,
            month=5,
            year=2026
        )
        
        # Assert (перевірка)
        assert isinstance(result, Decimal)
        assert result >= 0
```

**Типи тестів:**
- **Unit тести** — перевірка окремих функцій
- **Інтеграційні тести** — взаємодія кількох модулів
- **API тести** — перевірка REST endpoints
- **Регресійні тести** — перевірка, що старий функціонал не сломався

## 3.3. Архітектурні паттерни та їх реалізація

### 3.3.1 Service Layer Pattern

**Назначение:** Відокремлення бізнес-логіки від представлення та доступу до даних.

```python
# backend/transactions/services.py
class TransactionService:
    """Сервіс для роботи з транзакціями."""
    
    def __init__(self, repository=None):
        self.repository = repository or TransactionRepository()
    
    def import_bank_statement(self, file, user):
        """
        Імпорт банківської виписки з файлу.
        
        Крок 1: Парсинг файлу
        Крок 2: Валідація даних
        Крок 3: Збереження в БД
        Крок 4: Автоматична категоризація
        """
        parser = BankStatementParser()
        transactions_data = parser.parse(file)
        
        # Валідація
        for trans in transactions_data:
            if not self._validate_transaction(trans):
                raise ValidationError(f"Invalid transaction: {trans}")
        
        # Збереження
        transactions = []
        for trans_data in transactions_data:
            trans = self.repository.create_transaction(trans_data)
            transactions.append(trans)
        
        # Категоризація
        categorizer = TransactionCategorizer()
        for trans in transactions:
            category = categorizer.categorize(trans)
            trans.category = category
            self.repository.update(trans)
        
        return transactions
    
    def calculate_monthly_expenses(self, user, month, year):
        """Обчислення видатків за місяць."""
        return self.repository.sum_expenses_by_month(user, month, year)
```

### 3.3.2 Repository Pattern

**Назначение:** Централізований доступ до даних через ORM.

```python
# backend/transactions/repositories.py
from django.db.models import Q, Sum
from decimal import Decimal

class TransactionRepository:
    """Репозиторій для доступу до транзакцій."""
    
    def get_filtered_transactions(self, user, filters=None):
        """
        Отримати фільтровані транзакції.
        
        Параметри:
        - user: користувач
        - filters: {'category_id': 1, 'start_date': '2026-01-01', ...}
        """
        queryset = Transaction.objects.filter(
            account__user=user
        ).select_related('category', 'account')
        
        if filters:
            if 'category_id' in filters:
                queryset = queryset.filter(category_id=filters['category_id'])
            
            if 'start_date' in filters:
                queryset = queryset.filter(
                    transaction_date__gte=filters['start_date']
                )
            
            if 'end_date' in filters:
                queryset = queryset.filter(
                    transaction_date__lte=filters['end_date']
                )
        
        return queryset.order_by('-transaction_date')
    
    def sum_expenses_by_month(self, user, month, year):
        """Сума видатків за місяць."""
        return Transaction.objects.filter(
            account__user=user,
            transaction_date__month=month,
            transaction_date__year=year,
            category__type='EXPENSE'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
    
    def create_transaction(self, data):
        """Створити нову транзакцію."""
        return Transaction.objects.create(**data)
```

### 3.3.3 Strategy Pattern для парсерів

**Назначение:** Різні реалізації парсинга для різних форматів.

```python
# backend/transactions/parsers.py
from abc import ABC, abstractmethod

class BankStatementParser(ABC):
    """Абстрактний парсер банківської виписки."""
    
    @abstractmethod
    def parse(self, file):
        """Парсинг файлу і повернення списку транзакцій."""
        pass

class PDFParser(BankStatementParser):
    """Парсер для PDF файлів."""
    
    def parse(self, file):
        # Реалізація парсинга PDF
        import pdfplumber
        
        transactions = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                for row in table:
                    trans = self._extract_transaction(row)
                    transactions.append(trans)
        
        return transactions
    
    def _extract_transaction(self, row):
        return {
            'date': row[0],
            'description': row[1],
            'amount': float(row[2])
        }

class ExcelParser(BankStatementParser):
    """Парсер для Excel файлів."""
    
    def parse(self, file):
        import pandas as pd
        
        df = pd.read_excel(file)
        transactions = []
        
        for _, row in df.iterrows():
            trans = {
                'date': row['Дата'],
                'description': row['Опис'],
                'amount': float(row['Сума'])
            }
            transactions.append(trans)
        
        return transactions

# Використання
parser = PDFParser()  # або ExcelParser()
transactions = parser.parse('statement.pdf')
```

## 3.4. Технологічні компоненти та їх властивості

| Компонент | Тип | Функція | Властивості |
|-----------|-----|---------|-----------|
| **Django** | Framework | Серверна логіка | REST API, ORM, Admin panel |
| **PostgreSQL** | БД | Збереження даних | Реляційна, масштабована, ACID |
| **Vue.js** | Frontend | Інтерфейс користувача | Реактивність, компонентність, SPA |
| **Docker** | Container | Ізоляція середовища | Портативність, консистентність |
| **pytest** | Тестування | Перевірка коду | Фікстури, параметризація, мокування |
| **Git/GitHub** | VC | Управління версіями | Спільна розробка,历ория, CI/CD |
| **Black** | Formatter | Форматування коду | PEP 8, консистентність |
| **Ruff** | Linter | Аналіз коду | Швидкість, інтеграція, fixable |

---

# 4. СТВОРЕННЯ СПЕЦИФІКАЦІЇ ТА ДОКУМЕНТАЦІЇ

## 4.1. Цілі та завдання

Під час проходження переддипломної практики було ознайомлено з етапами створення специфікації та документації програмного продукту **"MyHaven"**, системи управління особистими фінансами, яка розробляється в межах дипломного проєкту.

**Основна мета:** Розробка комплексної вебдодатку та мобільного рішення, яке забезпечує:
- Безпечний імпорт та аналіз банківських виписок
- Автоматичну категоризацію фінансових операцій
- Управління бюджетами та отримання аналітичних звітів
- Інтеграцію з сучасними мобільними платформами та мессенджерами

## 4.2. Вимоги до системи

### Функціональні вимоги

**1. Управління користувачами:**
- Реєстрація та автентифікація через email
- 2FA (TOTP) для підвищеної безпеки
- Управління профілем та налаштуваннями (тема, мова, валюта)
- Видалення акаунта з видаленням всіх даних

**2. Управління рахунками:**
- Додавання кількох банківських рахунків
- Вибір типу рахунку (BANK, CARD, SAVINGS)
- Вибір валюти рахунку

**3. Імпорт та обробка транзакцій:**
- Завантаження виписок у форматах PDF та Excel
- Автоматичний парсинг даних
- Валідація та очищення даних
- Відстеження статусу завантаження

**4. Категоризація:**
- Автоматичне розподілення по категоріям
- Можливість ручного перевизначення
- Керування користувацькими категоріями
- Системні категорії за замовчуванням

**5. Управління бюджетами:**
- Встановлення лімітів по категоріям
- Отримання сповіщень при перевищенні
- Перегляд статусу бюджету

**6. Аналітика та звітність:**
- Дашборд з ключовими KPI
- Таблиці та графіки видатків
- Експорт звітів (планується)

**7. Інтеграція з Telegram:**
- Bot API для отримання звітів
- Сповіщення про бюджети
- Статистика видатків

### Нефункціональні вимоги

**Безпека:**
- JWT автентифікація з токен-рефреш механізмом
- HTTPS для всіх комунікацій
- Хешування паролів з солю
- Захист від CSRF атак

**Продуктивність:**
- Обробка 100+ операцій без затримок
- Час відповіді сервера < 200 мс
- Оптимізація запитів до БД (select_related, prefetch_related)

**Масштабованість:**
- Підтримка до 10,000+ користувачів
- Готовність до міграції на мікросервіси
- Можливість використання Celery для фонових завдань

**Надійність:**
- 99.5% uptime
- Регулярні резервні копії БД
- Обробка помилок та логування

## 4.3. Виміри та типи даних

### Основні типи даних

```python
# User
{
    id: int,
    username: str (max 150),
    email: str (unique),
    password_hash: str,
    totp_secret: str (optional),
    totp_enabled: bool,
    theme: 'light' | 'dark' | 'auto',
    language: 'uk' | 'en',
    currency: 'UAH' | 'USD' | 'EUR',
    created_at: datetime,
    updated_at: datetime
}

# Account
{
    id: int,
    user_id: int,
    bank_name: str,
    account_number: str,
    account_type: 'BANK' | 'CARD' | 'SAVINGS',
    balance: Decimal,
    currency: 'UAH' | 'USD' | 'EUR',
    is_active: bool,
    created_at: datetime
}

# Transaction
{
    id: int,
    account_id: int,
    amount: Decimal,
    category_id: int,
    transaction_date: date,
    description: str,
    is_income: bool,
    created_at: datetime
}

# Category
{
    id: int,
    user_id: int,
    name: str,
    type: 'INCOME' | 'EXPENSE',
    is_system: bool,
    keywords: str[],  # PostgreSQL array
    created_at: datetime
}

# Budget
{
    id: int,
    user_id: int,
    category_id: int,
    limit_amount: Decimal,
    month: int,
    year: int,
    alert_threshold: int,  # % від ліміту
    created_at: datetime
}
```

## 4.4. Інструменти для документації

| Інструмент | Призначення |
|-----------|-----------|
| **Markdown** | Технічна документація, README, гайди |
| **OpenAPI/Swagger** | Автоматична генерація API документації |
| **Draw.io** | UML діаграми, ER діаграми |
| **Figma** | Макети інтерфейсу (планується) |
| **GitHub Wiki** | Спільна документація |

---

# 5. СТВОРЕННЯ ТЕХНІЧНОЇ ДОКУМЕНТАЦІЇ ФУНКЦІОНАЛУ

## 5.1. Архітектура системи

### Загальна архітектура (3-tier)

```
┌─────────────────────────────────────────────────────────────┐
│ PRESENTATION TIER                                           │
│ Vue.js Frontend (SPA) + Telegram Bot                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/HTTPS REST API
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ APPLICATION TIER                                            │
│ Django + DRF                                                │
│                                                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │ Views/       │ │ Services     │ │ Repositories │        │
│ │ Serializers  │ │ (Business    │ │ (Data        │        │
│ │              │ │ Logic)       │ │ Access)      │        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQL Queries
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ DATA TIER                                                   │
│ PostgreSQL Database                                         │
│ (Users, Accounts, Transactions, Categories, Budgets)       │
└─────────────────────────────────────────────────────────────┘
```

### Послідовність операцій: Імпорт банківської виписки

```
1. Користувач завантажує файл виписки (PDF/Excel)
   ↓
2. Django приймає файл та створює TransactionUpload запис
   ↓
3. TransactionService викликає відповідний Parser (PDFParser, ExcelParser)
   ↓
4. Parser читає дані з файлу
   ↓
5. TransactionService валідує кожну операцію
   ↓
6. TransactionService передає до Repository для збереження в БД
   ↓
7. Repository створює Transaction записи (bulk_create для оптимізації)
   ↓
8. TransactionService викликає TransactionCategorizer для кожної операції
   ↓
9. Categorizer визначає категорію по ключовим словам (Matcher Strategy)
   ↓
10. Transaction оновлюється з визначеною категорією
   ↓
11. Користувачу повертається статус успіху та список імпортованих операцій
```

## 5.2. Ключові функціональні модулі

### 5.2.1 AuthModule (Управління автентифікацією)

```python
# backend/users/services.py

class AuthService:
    """Сервіс для автентифікації та управління сеансами."""
    
    def register(self, username, email, password):
        """
        Реєстрація нового користувача.
        
        Кроки:
        1. Валідація email та паролю
        2. Перевірка унікальності username та email
        3. Хешування паролю з солю
        4. Створення користувача в БД
        5. Повернення JWT токенів
        
        Вимоги до паролю:
        - Мінімум 8 символів
        - Містить велику та малу літери
        - Містить цифру та спецсимвол
        """
        pass
    
    def login(self, email, password):
        """
        Вхід користувача в систему.
        
        Повертає:
        - access_token (15 хвилин)
        - refresh_token (7 днів)
        - user_data
        """
        pass
    
    def setup_totp(self, user):
        """
        Налаштування 2FA.
        
        Повертає:
        - totp_secret
        - qr_code_url (для Google Authenticator)
        """
        pass
    
    def verify_totp(self, user, token):
        """Перевірка коду 2FA при вході."""
        pass
```

### 5.2.2 TransactionModule (Обробка транзакцій)

```python
# backend/transactions/services.py

class TransactionService:
    """Основна бізнес-логіка для обробки транзакцій."""
    
    def import_statements(self, file, user, account):
        """
        Імпорт банківської виписки.
        
        1. Визначення формату файлу (PDF/Excel)
        2. Парсинг даних
        3. Валідація операцій
        4. Збереження в БД
        5. Категоризація
        
        Повертає: список успішно імпортованих операцій
        """
        pass
    
    def categorize_transaction(self, transaction):
        """
        Автоматична категоризація операції.
        
        Алгоритм:
        1. Витяг ключових слів з опису операції
        2. Пошук збігу в категоріях користувача
        3. Якщо знайдено — присвоєння категорії
        4. Якщо не знайдено — призначення категорії "Інше"
        """
        pass
    
    def get_dashboard(self, user):
        """
        Отримання KPI дашборду.
        
        Повертає:
        - total_income (всього прибутків)
        - total_expenses (всього видатків)
        - net_balance (чистий баланс)
        - categories_breakdown (розподіл по категоріям)
        - monthly_trend (тренд за 6 місяців)
        """
        pass

class TransactionCategorizer:
    """Стратегія категоризації операцій."""
    
    def categorize(self, transaction, user_categories):
        """
        Визначення категорії для операції.
        
        Механізм:
        1. Отримати опис операції
        2. Перетворити в нижній регістр
        3. Для кожної категорії користувача перевірити ключові слова
        4. Повернути першу категорію з збігом
        5. Якщо немає збігу — повернути категорію "Інше"
        """
        pass
```

### 5.2.3 BudgetModule (Управління бюджетами)

```python
# backend/budgets/services.py

class BudgetService:
    """Сервіс для управління бюджетами."""
    
    def create_budget(self, user, category, limit_amount, alert_threshold=80):
        """
        Створення бюджетного ліміту по категорії.
        
        Параметри:
        - user: користувач
        - category: категорія видатків
        - limit_amount: ліміт (грн./USD)
        - alert_threshold: поріг для сповіщення (%, за замовч. 80%)
        """
        pass
    
    def get_budget_status(self, user):
        """
        Отримання статусу всіх бюджетів користувача.
        
        Повертає для кожного бюджету:
        - category_name
        - limit_amount
        - spent_amount
        - percentage_used
        - is_exceeded
        """
        pass
    
    def check_budget_alerts(self, user):
        """
        Перевірка перевищених бюджетів.
        
        Повертає список категорій, які перевищили поріг alert_threshold.
        """
        pass
```

## 5.3. API Endpoints та приклади запитів

### Authentication

```
POST /api/auth/register/
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
}

Відповідь 201:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
    }
}
```

```
POST /api/auth/login/
{
    "email": "john@example.com",
    "password": "SecurePass123!"
}

Відповідь 200: (як у register)
```

### Transactions

```
GET /api/transactions/dashboard/

Відповідь 200:
{
    "total_income": 5000.00,
    "total_expenses": 3200.50,
    "net_balance": 1799.50,
    "categories_breakdown": {
        "Food": 800.50,
        "Transport": 450.00,
        "Entertainment": 200.00
    },
    "monthly_trend": [
        {"month": "2026-01", "income": 5000, "expenses": 3000},
        {"month": "2026-02", "income": 5000, "expenses": 3200},
        ...
    ]
}
```

```
POST /api/transactions/upload/
Content-Type: multipart/form-data

bank_statement: [file.pdf]
account_id: 1

Відповідь 201:
{
    "upload_id": "uuid-xxx",
    "status": "processing",
    "transactions_count": 45,
    "created_at": "2026-05-07T10:30:00Z"
}
```

### Budgets

```
GET /api/budgets/

Відповідь 200:
[
    {
        "id": 1,
        "category": "Food",
        "limit_amount": 1000.00,
        "spent_amount": 650.50,
        "percentage_used": 65,
        "is_exceeded": false
    },
    {
        "id": 2,
        "category": "Transport",
        "limit_amount": 500.00,
        "spent_amount": 520.00,
        "percentage_used": 104,
        "is_exceeded": true
    }
]
```

## 5.4. Алгоритми та логіка

### Алгоритм категоризації

```
ФУНКЦІЯ categorize(transaction, categories):
    description = transaction.description.lower()
    keywords = extract_keywords(description)
    
    ДЛЯ КОЖНОЇ категорії В categories:
        ДЛЯ КОЖНОГО ключового_слова В category.keywords:
            ЯКЩО ключове_слово В keywords:
                ПОВЕРНУТИ категорію
    
    ПОВЕРНУТИ default_category("Інше")
```

### Алгоритм парсинга PDF

```
ФУНКЦІЯ parse_pdf(file):
    transactions = []
    
    ВІДКРИТИ file як pdf:
        ДЛЯ КОЖНОЇ сторінки:
            table = extract_table(сторінка)
            
            ДЛЯ КОЖНОГО ряду В table:
                trans = {
                    'date': parse_date(ряд[0]),
                    'description': ряд[1],
                    'amount': parse_amount(ряд[2]),
                    'currency': 'UAH'  # або з файлу
                }
                transactions.append(trans)
    
    ПОВЕРНУТИ transactions
```

## 5.5. Тестування

### Unit-тести для сервісів

```python
# backend/transactions/tests.py

class TestTransactionService(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(...)
        self.category = Category.objects.create(...)
    
    def test_categorize_food_expense(self):
        """Тест категоризації видатку на їжу."""
        transaction = Transaction(
            description="Zakupki.com - Hrechka",
            amount=150.00
        )
        
        category = TransactionCategorizer().categorize(transaction)
        
        self.assertEqual(category.name, "Food")
    
    def test_import_valid_excel_file(self):
        """Тест імпорту валідного Excel файлу."""
        file = SimpleUploadedFile("statement.xlsx", b"...")
        
        result = TransactionService().import_statements(
            file=file,
            user=self.user,
            account=self.account
        )
        
        self.assertEqual(len(result), 10)  # Очікуємо 10 операцій
        self.assertTrue(all(t.category_id is not None for t in result))
```

### API-тести

```python
def test_get_dashboard_api(self):
    """Тест GET /api/transactions/dashboard/"""
    response = self.client.get(
        '/api/transactions/dashboard/',
        HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
    )
    
    self.assertEqual(response.status_code, 200)
    data = response.json()
    
    self.assertIn('total_income', data)
    self.assertIn('total_expenses', data)
    self.assertIn('categories_breakdown', data)
```

---

# ДОДАТОК: ПЕРЕЛІК ІНСТРУМЕНТІВ ТА ТЕХНОЛОГІЙ

## Таблиця технологічного стеку

| Категорія | Інструмент | Версія | Призначення |
|-----------|-----------|--------|-----------|
| **Backend Framework** | Django | 5.2 | Веб-фреймворк |
| | Django REST Framework | 3.16 | REST API |
| **Database** | PostgreSQL | 15+ | Реляційна БД |
| **Authentication** | SimpleJWT | Latest | JWT токени |
| | pyotp | Latest | 2FA (TOTP) |
| **Frontend** | Vue.js | 3.x | SPA фреймворк |
| | Tailwind CSS | Latest | CSS фреймворк |
| | Pinia | Latest | State management |
| **File Processing** | pdfplumber | Latest | Парсинг PDF |
| | openpyxl | Latest | Парсинг Excel |
| **Testing** | pytest | 8+ | Тестування |
| | pytest-django | Latest | Django інтеграція |
| | factory-boy | Latest | Фікстури |
| **Code Quality** | Black | Latest | Форматування |
| | Ruff | Latest | Linting |
| **Version Control** | Git | Latest | Контроль версій |
| | GitHub | Cloud | Repository host |
| **API Documentation** | drf-spectacular | Latest | OpenAPI/Swagger |
| **Other** | Celery | 5+ | Task queue (планується) |
| | Redis | Latest | Cache (планується) |

## IDE та редактори

| IDE | Призначення | Платформи |
|----|-----------|----------|
| **VSCode** | Frontend, конфіг файли | Windows, Mac, Linux |
| **PyCharm** | Backend розробка | Windows, Mac, Linux |
| **DBeaver** | Управління БД | Windows, Mac, Linux |

## Команди для розробки

```bash
# Встановлення залежностей
cd backend
pip install -r requirements.txt

# Міграції БД
python manage.py migrate

# Запуск сервера
python manage.py runserver

# Запуск тестів
pytest -v

# Форматування коду
black backend/

# Перевірка лінтингу
ruff check backend/ --fix

# Генерація OpenAPI схеми
python manage.py spectacular --file schema.yml
```

## Посилання на документацію

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Vue.js Guide](https://vuejs.org/guide/)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Docs](https://docs.github.com/)

---

**Документ підготовлено:** травень 2026  
**Автор:** Розробник (переддипломна практика)  
**Статус:** Актуальна версія  

