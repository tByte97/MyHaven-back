# MyHaven Backend - Архітектурний Гайд

**Мова:** Украї́нська | **Фреймворк:** Django 5.2 + DRF | **БД:** PostgreSQL | **Автентифікація:** JWT (SimpleJWT)

---

## 📋 ЗМІСТ

1. [Архітектура проекту](#архітектура-проекту)
2. [Структура додатків](#структура-додатків)
3. [Паттерни проектування](#паттерни-проектування)
4. [SOLID Аналіз](#solid-аналіз)
5. [Как запустити](#как-запустити)
6. [Рекомендації по розробці](#рекомендації-по-розробці)
7. [Навички для розробників](#необхідні-навички)

---

## Архітектура проекту

### 🏗️ Загальна структура

```
backend/
├── core/                      # Django проект-конфігурація
│   ├── settings.py           # Налаштування (БД, CORS, JWT, etc)
│   ├── urls.py               # Головні URL-маршути
│   ├── wsgi.py               # WSGI для продакшену
│   └── asgi.py               # ASGI для async
│
├── users/                     # Додаток: користувачі & автентифікація
│   ├── models.py             # CustomUser з 2FA, налаштуваннями
│   ├── views.py              #混合: template-views + REST API views
│   ├── views_api.py          # ❌ Не використовується
│   ├── urls.py               # Template views (login, register)
│   ├── urls_api.py           # REST API endpoints
│   ├── serializers.py        # DRF serializers для API
│   ├── forms.py              # Django forms для templates
│   └── tests.py
│
├── accounts/                  # Додаток: банківські рахунки
│   ├── models.py             # Bank, Account (без API views)
│   ├── admin.py              # Django admin інтерфейс
│   └── migrations/
│
├── transactions/              # Додаток: транзакції (🎯 Найскладніший)
│   ├── models.py             # Transaction, Category, TransactionUpload
│   ├── views.py              # Тонкі API views (делегують у services)
│   ├── services.py           # 📍 БІЗНЕС-ЛОГІКА: парсинг, категоризація
│   ├── repositories.py       # 📍 ДОСТУП ДО ДАНИХ: ORM-запити, Query Builder
│   ├── serializers.py        # DRF serializers
│   ├── parsers.py            # Парсери банківських виписок (PDF, Excel)
│   ├── categorization.py     # Матчинг категорій по ключовим словам
│   ├── urls.py               # API endpoints
│   ├── forms.py              # Django forms (для template views)
│   └── tests.py
│
├── budgets/                   # Додаток: бюджети
│   ├── models.py             # Budget (ліміти по категоріям)
│   ├── views.py              # ViewSet для CRUD
│   ├── serializers.py        # BudgetSerializer
│   ├── urls.py               # API endpoints
│   └── migrations/
│
├── pages/                     # ❌ МЕРТВИЙ ДОДАТОК (можна видалити)
├── reports/                   # ❌ МЕРТВИЙ ДОДАТОК (можна видалити)
│
└── manage.py                  # Django CLI
```

---

## Структура додатків

### 1. **USERS** - Управління користувачами

#### Моделі
```python
class CustomUser(AbstractUser):
    # Ядро
    email                    # Унікальна електронна пошта
    
    # 2FA (TOTP)
    totp_secret             # QR-секрет для Google Authenticator
    totp_enabled            # Статус 2FA
    
    # Налаштування UI
    theme: 'light' | 'dark' | 'auto'
    language: 'uk' | 'en'
    currency: 'UAH' | 'USD' | 'EUR'
    
    # Сповіщення (⚠️ Не реалізовані на backend)
    email_notifications
    telegram_notifications
    notify_large_expense
    notify_budget_exceeded
    notify_daily_summary
    
    # Telegram Integration (⚠️ Не реалізовано)
    telegram_user_id
    telegram_username
```

#### Endpoints (REST API)

| Метод | Endpoint | Статус | Примітка |
|-------|----------|--------|----------|
| POST | `/api/users/register/` | ✅ | Реєстрація (не активно використовується - template form) |
| GET | `/api/users/me/` | ✅ | Поточний користувач |
| GET/PATCH | `/api/users/profile/` | ✅ | Профіль користувача |
| POST | `/api/users/change-password/` | ✅ | Зміна пароля |
| POST | `/api/users/delete-account/` | ✅ | Видалення акаунта |
| GET | `/api/users/export-data/` | ✅ | Експорт всіх даних у JSON |
| GET | `/api/users/totp/setup/` | ❌ | ВІДСУТНІЙ - генерація QR коду |
| POST | `/api/users/totp/enable/` | ❌ | ВІДСУТНІЙ - активація 2FA |
| POST | `/api/users/totp/disable/` | ❌ | ВІДСУТНІЙ - деактивація 2FA |
| POST | `/api/users/totp/verify/` | ❌ | ВІДСУТНІЙ - верифікація коду |
| PATCH | `/api/users/preferences/` | ❌ | ВІДСУТНІЙ - зберегти тему/мову/валюту |
| PATCH | `/api/users/notifications/` | ❌ | ВІДСУТНІЙ - зберегти налаштування сповіщень |

#### Архітектура

```
views.py
├── Template Views (Django Sessions)
│   ├── home_view()         → userhome.html
│   ├── register()          → register.html (RegisterForm)
│   ├── login_view()        → login.html (AuthenticationForm)
│   └── logout_view()
│
└── REST API Views (JWT)
    ├── RegisterView            → DRF CreateAPIView
    ├── CurrentUserView         → APIView (get)
    ├── ProfileView             → APIView (get, patch)
    ├── ChangePasswordView      → APIView (post)
    ├── DeleteAccountView       → APIView (post)
    └── ExportDataView          → APIView (get) - рекурсивно збирає всі дані
```

---

### 2. **TRANSACTIONS** - Транзакції (🎯 ОСНОВНИЙ ДОДАТОК)

#### Моделі

```python
class Category(models.Model):
    """Категорія видатків/доходів"""
    user                # null=True → системні категорії для всіх
    name, type          # 'INCOME' | 'EXPENSE'
    parent              # ForeignKey('self') → ієрархія
    keywords            # JSON: ['супер', 'маркет'] для auto-matching
    is_system           # True → не видаляти

class Transaction(models.Model):
    """Одна операція банку"""
    user, account       # ForeignKeys
    category            # auto-matched або manual
    amount              # Decimal: >0 = дохід, <0 = видатки
    description         # Текст від банку або user-entered
    transaction_date    # Коли була операція
    source              # 'import' | 'manual' | 'telegram'
    raw_description     # Оригінальна від банку
    bank_category       # Категорія від банку
    matched_automatically # Чи автоматично підібрана категорія?
    confidence_score    # % впевненості в match'е (0-1)
    source_upload       # Посилання на завантажену виписку

class TransactionUpload(models.Model):
    """Завантажена банківська виписка"""
    user, bank          # ForeignKeys
    file                # FileField → media/bank_statements/
    status              # 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
    uploaded_at         # Часова мітка
    total_transactions  # Скільки було у виписці
    processed_transactions # Скільки успішно імпортовано
    processing_log      # Лог помилок/попереджень
```

#### Архітектура (Service Layer Pattern)

```
API Request
    ↓
views.py (тонкий шар - тільки HTTP)
    ├── DashboardStatsAPI
    ├── StatisticsAPI
    ├── TransactionListAPI
    ├── TransactionCreateAPI
    ├── TransactionDetailAPI
    └── UploadListAPI
    ↓
services.py (БІЗНЕС-ЛОГІКА)
    ├── process_upload()
    │   ├── Вибрати parser (PrivatBank, OSCHADBANK, etc)
    │   ├── Розпарсити файл
    │   ├── _create_transactions() → get_or_create (уникнення дублів)
    │   └── CategoryMatcher.match() → auto-assign категорія
    └── get_or_create_account()
    ↓
repositories.py (ДОСТУП ДО ДАНИХ - Query Builder)
    ├── get_dashboard_kpi()
    ├── get_monthly_statistics()
    ├── get_category_stats()
    ├── get_bank_stats()
    ├── get_calendar()
    └── ...15+ методів для різних запитів
    ↓
models.py (ORM → PostgreSQL)
```

#### Endpoints

| Метод | Endpoint | Функція |
|-------|----------|---------|
| GET | `/transactions/api/dashboard/` | KPI за 30 днів |
| GET | `/transactions/api/statistics/?months=6` | Статистика |
| GET | `/transactions/api/list/?category=...&type=...&date_from=...` | Список з фільтрацією |
| POST | `/transactions/api/create/` | Додати вручну |
| GET/PATCH/DELETE | `/transactions/api/{id}/` | Редагувати транзакцію |
| GET | `/transactions/api/categories/` | Список категорій |
| GET | `/transactions/api/calendar/` | Календар операцій |
| GET | `/transactions/api/calendar/{year}/{month}/{day}/` | День детально |
| GET/POST | `/transactions/api/uploads/` | Завантаження виписок |
| DELETE | `/transactions/api/uploads/{id}/` | Видалити виписку |
| GET | `/transactions/api/banks/` | Список банків |

#### Парсери (Strategy Pattern)

```python
# Абстрактний базовий клас
class BankStatementParser:
    def parse(file_path) → List[Dict]  # {date, amount, description}
    
# Конкретні реалізації
class PrivatBankExcelParser(BankStatementParser)  # Excel .xlsx
class OSCHADBankPDFParser(BankStatementParser)    # PDF
class AlphaExcelParser(BankStatementParser)       # Excel .xlsx

# Фабрика
def get_parser_for_bank(bank_name) → BankStatementParser
```

#### Категоризація (Keyword Matching)

```python
class CategoryMatcher:
    def __init__(self, user):
        self.keywords_cache = {}  # Кеш для швидкості
    
    def match(description, bank_category, amount) → (Category, confidence):
        # 1. Шукаємо ключові слова у keywords JSON
        # 2. Матчимо банківські категорії
        # 3. Шукаємо регекси
        # 4. Повертаємо найкращий match з confidence score
```

---

### 3. **BUDGETS** - Бюджети

#### Модель

```python
class Budget(models.Model):
    user        # ForeignKey
    category    # ForeignKey (тільки EXPENSE)
    month       # DateField (перший день місяця)
    amount      # Decimal (ліміт)
    
    unique_together = ('user', 'category', 'month')
```

#### Endpoints

| Метод | Endpoint |
|-------|----------|
| GET/POST | `/api/budgets/` |
| GET/PATCH/DELETE | `/api/budgets/{id}/` |

#### Архітектура

```python
class BudgetViewSet(viewsets.ModelViewSet):
    # Використовує різні serializers для читання/запису
    # Автоматично фільтрує по поточному користувачу
```

---

### 4. **ACCOUNTS** - Рахунки (модельні дані, без API)

#### Моделі

```python
class Bank(models.Model):
    name        # Назва банку (унікальна)
    logo        # ImageField → media/bank_logos/

class Account(models.Model):
    user        # ForeignKey
    bank        # ForeignKey
    account_name # 'Мій рахунок'
    account_type # 'BANK', 'CARD', 'CASH'
    last_four_digits # '1234'
    currency    # 'UAH', 'USD', 'EUR'
    
    @property
    def calculated_balance:
        # Сума всіх транзакцій (ORM aggregation)
```

---

### 5. **PAGES & REPORTS** - ❌ Мертві додатки

- Створені, але пусті
- Можна безпечно видалити
- Не впливають на функціональність

---

## Паттерни проектування

### ✅ Використані

#### 1. **Service Layer Pattern** (transactions)
- Views → Services → Repositories
- Логіка відділена від HTTP-рівня
- Легко тестувати без мокування запитів

```python
# Service (бізнес-логіка)
def process_upload(upload):
    parser = get_parser_for_bank(upload.bank.name)
    data = parser.parse(upload.file.path)
    account = get_or_create_account(upload.user, upload.bank)
    _create_transactions(account, upload, data)

# Тонкий view
class UploadListAPI(APIView):
    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        service.process_upload(serializer.instance)
        return Response(...)
```

#### 2. **Repository Pattern** (transactions)
- Інкапсулює всі ORM-запити
- Централізована Query Builder
- Легко змінити БД без змін у views

```python
class TransactionRepository:
    def get_dashboard_kpi(self)
    def get_monthly_statistics(self, months=6)
    def get_category_stats(self, months=6, transaction_type='EXPENSE')
```

#### 3. **Strategy Pattern** (parsers)
- Абстрактний BankStatementParser
- Конкретні класи для кожного банку (PrivatBank, OSCHADBANK)
- Фабрична функція вибирає потрібний

```python
class BankStatementParser:  # Абстрактна
    def parse(self, file_path):
        raise NotImplementedError

class PrivatBankExcelParser(BankStatementParser):  # Конкретна
    def parse(self, file_path):
        df = pd.read_excel(file_path)
        # ...
```

#### 4. **DRY (Don't Repeat Yourself)**
- `COMMON_DATE_FORMATS` - один місце для форматів
- `DecimalEncoder` - один місце для JSON-encoding
- Базовий `CategorySerializer` в Transaction

#### 5. **Permissions & Authentication**
- JWT токени через SimpleJWT
- `permission_classes = [IsAuthenticated]` в API views
- Фільтрація по `request.user`

---

## SOLID Аналіз

### 📊 Матриця відповідності SOLID

| Принцип | Дотримання | Оцінка | Коментар |
|---------|----------|--------|---------|
| **S** - Single Responsibility | ✅ Хорошо | 8/10 | Views делегують, Services мають одну відповідальність, але є винятки |
| **O** - Open/Closed | ✅ Хорошо | 7/10 | Strategy Pattern для парсерів, але додати новий парсер потребує нового класу |
| **L** - Liskov Substitution | ✅ Хорошо | 8/10 | BankStatementParser - правильна абстракція |
| **I** - Interface Segregation | ⚠️ Середньо | 6/10 | Деякі Views мають занадто багато методів |
| **D** - Dependency Inversion | ⚠️ Середньо | 6/10 | Немає DI-контейнера, імпорти жорсткі |

---

### 🔴 ПРОБЛЕМИ

#### 1. **Views з занадто багатьма обов'язками**

**Файл:** `users/views.py`

```python
# ❌ ПРОБЛЕМА: ExportDataView робить занадто багато
class ExportDataView(APIView):
    def get(self, request):
        # 1. Запитує транзакції
        transactions = Transaction.objects.filter(...)
        # 2. Запитує бюджети
        budgets = Budget.objects.filter(...)
        # 3. Запитує завантаження
        uploads = TransactionUpload.objects.filter(...)
        # 4. Серіалізує різні моделі
        data = {'profile': ..., 'transactions': ..., ...}
        return Response(data)
```

**Рішення:**
```python
# ✅ Делегувати у сервіс
class ExportService:
    @staticmethod
    def export_all_user_data(user):
        return {
            'profile': ProfileSerializer(user).data,
            'transactions': ...,
            'budgets': ...,
            'uploads': ...,
        }

class ExportDataView(APIView):
    def get(self, request):
        data = ExportService.export_all_user_data(request.user)
        return Response(data)
```

---

#### 2. **Змішування Template Views та REST API у одному файлі**

**Файл:** `users/views.py`

```python
# ❌ ПРОБЛЕМА: Один файл містить:
# - Template views (login, register, logout)
# - REST API views (CurrentUserView, ProfileView, etc)

# Змішування парадигм:
@login_required                    # Django Sessions
def login_view(request):           # Template view
    ...

class RegisterView(generics.CreateAPIView):  # JWT/DRF
    ...
```

**Рішення:**
- Розділити на `views.py` (templates) та `api/views.py` (REST)
- Або використовувати `api_views.py` (як у budgets)
- Документувати ітентифікацію в кожному файлі

---

#### 3. **Недостатнє дотримання Interface Segregation**

**Файл:** `budgets/views.py`

```python
# ❌ ViewSet мав би мати інтерфейси
class BudgetViewSet(viewsets.ModelViewSet):
    def get_queryset(self):      # Used
    def get_serializer_class(self):  # Used
    def perform_create(self, serializer):  # Used
    def list(self, request, ...):  # Overridden (дублювання коду)
```

**Рішення:**
```python
# ✅ Делегувати логіку у сервіс
class BudgetService:
    @staticmethod
    def list_budgets(user, month=None):
        qs = Budget.objects.filter(user=user)
        if month:
            qs = qs.filter(month=month)
        return qs

class BudgetViewSet(viewsets.ModelViewSet):
    def list(self, request):
        budgets = BudgetService.list_budgets(
            request.user,
            request.query_params.get('month')
        )
        return Response(BudgetSerializer(budgets, many=True).data)
```

---

#### 4. **Жорстокі залежності (Hard Dependencies)**

**Файл:** `transactions/views.py`

```python
# ❌ Імпорти жорсткі, не можна замінити
from .repositories import TransactionRepository
from .services import process_upload
from accounts.models import Bank

# Якщо захочемо змінити реалізацію Repository,
# потрібно редагувати весь файл
```

**Рішення (DI-контейнер):**
```python
# ✅ Dependency Injection
class TransactionListAPI(ListAPIView):
    def __init__(self, repository_class=TransactionRepository, **kwargs):
        super().__init__(**kwargs)
        self.repository = repository_class(self.request.user)

# Для тестування можемо передати mock
```

---

#### 5. **Частково реалізовані функції**

**Файл:** `users/models.py`

```python
# ❌ Поля збережені, але не використовуються
email_notifications = models.BooleanField(default=True)
telegram_notifications = models.BooleanField(default=False)
notify_large_expense = models.BooleanField(default=True)
notify_budget_exceeded = models.BooleanField(default=True)
notify_daily_summary = models.BooleanField(default=False)
telegram_user_id = models.BigIntegerField(blank=True, null=True)
telegram_username = models.CharField(max_length=100, blank=True, null=True)

# Views не реалізовані
# Services не використовують
# Frontend думає, що працює, але помилки 404
```

---

## 📋 РЕКОМЕНДАЦІЇ ПО РОЗРОБЦІ

### Стилю кодування

#### 1. **Імена змінних - Українська в коментарях, англійська в коді**

```python
# ✅ Добре
def get_dashboard_kpi(self):
    """Отримати KPI за останні 30 днів: витрати, доходи, баланс."""
    month_ago = timezone.now() - timedelta(days=30)
    expenses = qs.filter(amount__lt=0).aggregate(t=Sum('amount'))['t'] or 0
    return {'total_expenses': abs(expenses), ...}

# ❌ Погано
def get_dashboard_kpi(self):
    """Отримати KPI за останні 30 днів"""
    місяць_тому = timezone.now() - timedelta(days=30)  # Кирилиця в коді!
    витрати = qs.filter(amount__lt=0).aggregate(t=Sum('amount'))['t'] or 0
```

#### 2. **Структура функцій - від загального до деталей**

```python
# ✅ Добре
def process_upload(upload: TransactionUpload) -> None:
    """Повний цикл обробки завантаженого файлу."""
    upload.status = 'PROCESSING'
    upload.save()
    
    try:
        # 1. Визначити парсер
        parser = get_parser_for_bank(upload.bank.name)
        # 2. Розпарсити файл
        data = parser.parse(upload.file.path)
        # 3. Створити рахунок
        account = get_or_create_account(upload.user, upload.bank)
        # 4. Зберегти транзакції
        created, skipped = _create_transactions(account, upload, data)
    except Exception as e:
        upload.status = 'FAILED'
        upload.processing_log = str(e)
```

#### 3. **Логування - INFO для успіху, WARNING для проблем, ERROR для критичного**

```python
# ✅ Добре
logger.info("User %s changed password", request.user.id)
logger.warning("Registration form errors: %s", form.errors)
logger.exception("Помилка оновлення фільтра")  # Автоматично includes traceback

# ❌ Погано
print("User changed password")  # Не зберігається
logger.debug("User %s changed password", request.user.id)  # Не видно в продакшені
```

#### 4. **Type Hints - обов'язково для функцій**

```python
# ✅ Добре
def match(
    self,
    description: str,
    bank_category: str,
    amount: float,
) -> Tuple[Optional[Category], float]:
    """Match transaction to category."""
    
def get_or_create_account(user: CustomUser, bank: Bank) -> Account:
    """Get or create account for user-bank pair."""

# ❌ Погано
def match(self, description, bank_category, amount):
    # Не ясно, які типи поверта́ємо
    ...
```

#### 5. **Django QuerySets - використовувати select_related, prefetch_related**

```python
# ✅ Добре (N+1 problem вирішено)
qs = Transaction.objects.filter(
    account__user=self.user,
).select_related(
    'category', 'account', 'account__bank'
).order_by('-transaction_date')

# ❌ Погано (N+1 queries!)
qs = Transaction.objects.filter(account__user=self.user)
for tx in qs:
    print(tx.category.name)  # Окремий запит для кожної!
    print(tx.account.bank.name)  # Ще один!
```

#### 6. **API Response Format - структурований, з метаінформацією**

```python
# ✅ Добре
return Response({
    'results': serializer.data,
    'count': paginator.count,
    'num_pages': paginator.num_pages,
    'current_page': page,
})

# ❌ Погано (просто список)
return Response(serializer.data)
```

---

### 🏗️ Архітектурні рекомендації

#### 1. **Service Layer для всієї бізнес-логіки**

```python
# ✅ Структура
transactions/
├── views.py          # Тонкі views (лише HTTP)
├── services.py       # БІЗНЕС-ЛОГІКА
├── repositories.py   # ДОСТУП ДО ДАНИХ
├── serializers.py    # Валідація & трансформація
└── models.py         # ORM

# Як це працює
HTTP Request → views.py → services.py → repositories.py → models.py → PostgreSQL
```

#### 2. **Розділити Template Views та REST API**

```python
# ✅ До (було)
users/
├── views.py
│   ├── login_view()              # Template view
│   ├── register()                # Template view
│   └── CurrentUserView           # REST API view
│
├── urls.py                       # Template routes
└── urls_api.py                   # API routes

# Краще розділити
users/
├── views.py                      # Template views (login, register)
├── api/
│   ├── views.py                  # REST API views
│   ├── serializers.py            # API serializers
│   └── urls.py                   # API routes
└── forms.py                      # Django forms
```

#### 3. **Додати сервіс-модуль для TOTP**

```python
# users/services/totp_service.py
import pyotp
import qrcode

class TOTPService:
    @staticmethod
    def generate_secret_and_qr(user_email: str) -> Dict[str, str]:
        """Генеруємо QR код для Google Authenticator."""
        secret = pyotp.random_base32()
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name='MyHaven'
        )
        qr_code_b64 = _generate_qr_code(uri)
        return {'secret': secret, 'qr_code': qr_code_b64}
    
    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Перевіримо 6-значний код."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    @staticmethod
    def enable_totp(user: CustomUser, secret: str) -> None:
        """Активуємо 2FA."""
        user.totp_secret = secret
        user.totp_enabled = True
        user.save(update_fields=['totp_secret', 'totp_enabled'])
```

#### 4. **Додати Notification Service** (якщо потрібна функціональність)

```python
# notifications/service.py
class NotificationService:
    @staticmethod
    def on_budget_exceeded(user: CustomUser, budget: Budget) -> None:
        """Тригер коли перевищено бюджет."""
        if not user.email_notifications:
            return
        
        # Відправити email
        send_email(
            to=user.email,
            subject=f"Бюджет '{budget.category.name}' перевищено!",
            template='budget_exceeded.html',
            context={'budget': budget}
        )
    
    @staticmethod
    def on_large_expense(user: CustomUser, transaction: Transaction, threshold=5000) -> None:
        """Тригер для великої витрати."""
        if transaction.amount > threshold and user.notify_large_expense:
            send_email(...)
```

---

## Як запустити

### Налаштування

#### 1. **Встановити залежності**

```bash
# Перейти до backend директорії
cd backend

# Створити virtual environment
python -m venv .venv

# Активувати
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Встановити пакети
pip install -r requirements.txt
```

#### 2. **Налаштувати базу даних**

```bash
# PostgreSQL має бути запущений
# Поправити backend/core/settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'MyHaven',
        'USER': 'postgres',
        'PASSWORD': 'ваш_пароль',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Запустити міграції
python manage.py migrate
```

#### 3. **Створити суперюзера**

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: ****
```

#### 4. **Запустити dev сервер**

```bash
python manage.py runserver
# Сервер на http://localhost:8000
# Admin на http://localhost:8000/admin
```

---

## Необхідні навички

### Для Junior розробника

#### Backend

- **Django:**
  - Models, QuerySets, Migrations
  - Class-Based Views (CBV) vs Function-Based Views (FBV)
  - Django Forms & Validation
  - ORM basics (select_related, prefetch_related)

- **Django REST Framework:**
  - Serializers (ModelSerializer, custom serializers)
  - APIView, generics, ViewSets
  - Permission classes (IsAuthenticated)
  - Response formatting

- **Databases:**
  - SQL basics (SELECT, JOIN, WHERE)
  - PostgreSQL основи
  - Indexes for performance

- **Python:**
  - Type hints
  - Decorators (@login_required, @property)
  - Context managers (with statement)
  - List comprehensions

#### Frontend Integration

- **REST API:**
  - HTTP методи (GET, POST, PATCH, DELETE)
  - Status codes (200, 400, 404, 500)
  - JWT tokens
  - CORS

- **Vue.js 3:**
  - Components, Props, Emits
  - Reactivity (ref, computed)
  - API calls (axios)
  - Pinia stores

---

### Для Middle розробника

#### Додатково до Junior

- **Django:**
  - Signals (post_save, pre_delete)
  - Managers & QuerySets customization
  - Middleware
  - Custom decorators
  - Management commands

- **Design Patterns:**
  - Service Layer (як у transactions/)
  - Repository Pattern (TransactionRepository)
  - Strategy Pattern (BankStatementParser)
  - Factory Pattern
  - Observer Pattern (Django signals)

- **Performance:**
  - Query optimization (N+1 problem)
  - Caching (Redis, Django cache)
  - Database indexing
  - Pagination & filtering

- **Testing:**
  - Unit tests (unittest, pytest)
  - Mocking (unittest.mock)
  - API testing (DRF test utilities)
  - Fixtures

- **DevOps/Infrastructure:**
  - Environment variables (.env)
  - Docker basics
  - Database migrations in production
  - Git workflow (branching, rebasing)

---

### Для Senior розробника

#### Додатково до Middle

- **Architecture:**
  - Scalability (horizontal, vertical)
  - Microservices patterns
  - Event-driven architecture
  - API versioning

- **Advanced Django:**
  - Custom authentication backends
  - Permissions & authorization (Django Guardian)
  - GraphQL (Graphene)
  - Async views (async/await)

- **Database:**
  - Query execution plans (EXPLAIN)
  - Transactions & locks
  - Replication & backup strategy
  - Performance tuning

- **Security:**
  - OWASP Top 10
  - SQL injection prevention
  - CSRF, CORS security
  - Password hashing (bcrypt, argon2)
  - API rate limiting

- **Team Leadership:**
  - Code review best practices
  - Architecture decisions
  - Technical documentation
  - Mentoring junior developers

---

### Технічний стек проекту

```
Backend:
├── Django 5.2          ✅ Web framework
├── Django REST Framework  ✅ API framework
├── SimpleJWT           ✅ JWT authentication
├── PostgreSQL          ✅ Database
├── Redis               ❌ (можна додати для caching)
├── Celery              ❌ (для async tasks - обробка файлів)
├── docker              ❌ (для контейнеризації)
└── pytest              ❌ (для тестування)

Frontend:
├── Vue.js 3            ✅ UI framework
├── Pinia               ✅ State management
├── axios               ✅ HTTP client
├── vue-router          ✅ Routing
├── Tailwind CSS        ✅ Styling
├── Chart.js            ✅ Charts
└── lucide-vue-next     ✅ Icons

DevOps:
├── Git                 ✅ Version control
├── PostgreSQL          ✅ Database
└── (to be added: Docker, CI/CD)
```

---

## 🎯 Висновок

Проект добре структурований з правильним використанням паттернів (Service Layer, Repository, Strategy). Основні області для покращення:

1. ✅ **Добре:** Розділення відповідальності, чіткі API endpoints, логування
2. ⚠️ **Потребує роботи:** TOTP views, Notification system, DI-контейнер
3. 🔴 **Критично:** Видалити мертві додатки, документація для нових розробників

Проект готовий до масштабування з правильною архітектурою як основою.

