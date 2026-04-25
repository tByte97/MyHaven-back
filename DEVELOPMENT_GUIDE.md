# MyHaven - Гайд по Розробці

**Як розвивати проект далі? Якими навичками повинен володіти розробник?**

---

## 📚 ЧАСТИНА 1: НАВИЧКИ РОЗРОБНИКА

### Рівні

```
┌─────────────────────────────────────────────────────┐
│ SENIOR (5+ років)                                   │
│ ├─ Архітектурні рішення                             │
│ ├─ Масштабування (millions of users)                │
│ ├─ DevOps & Infrastructure                          │
│ └─ Team Leadership                                  │
├─────────────────────────────────────────────────────┤
│ MIDDLE (2-5 років)                                  │
│ ├─ Service Layer & Design Patterns                  │
│ ├─ Performance Optimization                         │
│ ├─ Testing (TDD)                                    │
│ └─ Microservices basics                             │
├─────────────────────────────────────────────────────┤
│ JUNIOR (0-2 років)                                  │
│ ├─ Django ORM & QuerySets                           │
│ ├─ DRF (Serializers, ViewSets)                      │
│ ├─ REST API basics                                  │
│ └─ PostgreSQL JOIN's & indexing                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎓 JUNIOR LEVEL (0-2 роки)

### Обов'язкові навички

#### 1. Django Orm & Models

```python
# MUST KNOW: ForeignKey, ManyToMany, OneToOne
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    # on_delete варіанти:
    # - CASCADE: видалити всі книги при видаленні автора
    # - SET_NULL: встановити NULL (потребує null=True)
    # - SET_DEFAULT: встановити default значення
    # - PROTECT: вигенерити помилку

# SELECT_RELATED - для ForeignKey (один запит)
books = Book.objects.select_related('author').all()
for book in books:
    print(book.author.name)  # 👈 БЕЗ додаткових запитів!

# PREFETCH_RELATED - для ManyToMany (оптимізація)
from django.db.models import Prefetch
authors = Author.objects.prefetch_related('book_set').all()
for author in authors:
    for book in author.book_set.all():  # 👈 Оптимізовано
        print(book.title)
```

#### 2. QuerySet Filtering

```python
# Базові фільтри
User.objects.filter(age__gt=18)           # > 18
User.objects.filter(age__gte=18)          # >= 18
User.objects.filter(age__lt=30)           # < 30
User.objects.filter(name__icontains='jo') # case-insensitive

# Q objects для OR запитів
from django.db.models import Q

User.objects.filter(
    Q(age__gt=18) | Q(is_premium=True)   # OR
)

User.objects.filter(
    Q(age__gt=18) & Q(is_active=True)    # AND
)

# Дата фільтри
Transaction.objects.filter(
    transaction_date__date__gte='2026-01-01'  # После дати
)

Transaction.objects.filter(
    transaction_date__year=2026  # По року
)
```

#### 3. DRF Serializers

```python
from rest_framework import serializers

# ModelSerializer автоматично генерує поля
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']

# Custom serializer з валідацією
class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)
    
    def validate_email(self, value):
        """Перевірити унікальність email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email вже існує")
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user
```

#### 4. APIView & ViewSets

```python
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.viewsets import ModelViewSet

# ✅ ПРОСТИЙ: APIView для контролю
class UserListView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

# ✅ ПРОСТІШЕ: ListCreateAPIView
class UserListView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# ✅ НАЙПРОСТІШЕ: ViewSet (REST автоматично!)
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Автоматично генерує:
    # GET    /users/           → list()
    # POST   /users/           → create()
    # GET    /users/{id}/      → retrieve()
    # PUT    /users/{id}/      → update()
    # DELETE /users/{id}/      → destroy()
```

#### 5. Permissions & Authentication

```python
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView

# ✅ JWT автентифікація
class MyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # request.user - поточний користувач
        print(request.user.id)
        return Response({'user': request.user.id})

# ✅ Кастомна permission
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Дозволити тільки власнику
        return obj.user == request.user

class ProfileView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    
    def patch(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        self.check_object_permissions(request, profile)
        # ... редагування
```

#### 6. PostgreSQL JOIN

```python
# N+1 проблема:
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # ← БЕЗ select_related()
    # Запит: 1 + N (де N=кількість користувачів!)

# Рішення - select_related()
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # ← 1 запит на всіх!

# Тип з'єднання:
# SELECT * FROM users JOIN profiles ON users.id = profiles.user_id
```

---

### Практичні вправи

```python
# ЗАВДАННЯ 1: Створити API endpoint для списку категорій
# - GET /api/categories/ → список всіх
# - POST /api/categories/ → створити нову
# - GET /api/categories/{id}/ → деталі
# - PATCH /api/categories/{id}/ → редагувати
# - DELETE /api/categories/{id}/ → видалити

# ЗАВДАННЯ 2: Додати фільтрацію
# GET /api/transactions/?category=5&type=expense&date_from=2026-01-01

# ЗАВДАННЯ 3: Додати пагінацію
# GET /api/transactions/?page=1&page_size=50
```

---

## 💼 MIDDLE LEVEL (2-5 років)

### Обов'язкові навички

#### 1. Service Layer Pattern

```python
# 📁 models.py
class Transaction(models.Model):
    user = models.ForeignKey(User)
    amount = models.DecimalField()
    category = models.ForeignKey(Category)

# 📁 services.py ← НОВЕ: Бізнес-логіка
class TransactionService:
    @staticmethod
    def create_transaction(user: User, data: Dict) -> Transaction:
        """Створити транзакцію з валідацією."""
        # 1. Валідація
        if data['amount'] <= 0:
            raise ValueError("Сума повинна бути > 0")
        
        # 2. Логіка
        transaction = Transaction.objects.create(**data, user=user)
        
        # 3. Side effects
        logger.info(f"Transaction {transaction.id} created")
        
        # 4. Повернути результат
        return transaction
    
    @staticmethod
    def check_budget_exceeded(transaction: Transaction) -> bool:
        """Перевірити, чи перевищено бюджет."""
        budget = Budget.objects.filter(
            user=transaction.user,
            category=transaction.category,
            month=transaction.transaction_date.date().replace(day=1),
        ).first()
        
        if not budget:
            return False
        
        total = Transaction.objects.filter(
            user=transaction.user,
            category=transaction.category,
            transaction_date__month=transaction.transaction_date.month,
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        return abs(total) > budget.amount

# 📁 views.py ← Тонкий шар
class TransactionCreateView(APIView):
    def post(self, request):
        serializer = TransactionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ✅ Делегуємо у сервіс
        transaction = TransactionService.create_transaction(
            request.user,
            serializer.validated_data
        )
        
        # Перевіримо бюджет
        if TransactionService.check_budget_exceeded(transaction):
            # Можемо відправити сповіщення
            pass
        
        return Response(TransactionSerializer(transaction).data, status=201)
```

**Переваги Service Layer:**
- ✅ Бізнес-логіка відділена від HTTP
- ✅ Легко тестувати (не потрібна БД для деяких тестів)
- ✅ Можна використати з Celery
- ✅ Легко повторно використати

#### 2. Repository Pattern

```python
# 📁 repositories.py
class TransactionRepository:
    """Єдина точка доступу до даних."""
    
    def __init__(self, user: User):
        self.user = user
    
    def get_all(self, filters: Dict = None) -> QuerySet:
        """Отримати всі транзакції з фільтрами."""
        qs = Transaction.objects.filter(
            account__user=self.user
        ).select_related('category', 'account')
        
        if filters:
            if 'category' in filters:
                qs = qs.filter(category_id=filters['category'])
            if 'date_from' in filters:
                qs = qs.filter(transaction_date__gte=filters['date_from'])
        
        return qs.order_by('-transaction_date')
    
    def get_monthly_summary(self, year: int, month: int) -> Dict:
        """Отримати підсумок за місяць."""
        qs = self.get_all().filter(
            transaction_date__year=year,
            transaction_date__month=month,
        )
        
        expenses = qs.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        incomes = qs.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        
        return {
            'expenses': abs(expenses),
            'incomes': incomes,
            'balance': incomes + expenses,
        }

# 📁 views.py
class TransactionListView(ListAPIView):
    def get_queryset(self):
        repo = TransactionRepository(self.request.user)
        return repo.get_all(self.request.query_params.dict())
    
    def get(self, request):
        repo = TransactionRepository(request.user)
        summary = repo.get_monthly_summary(2026, 4)
        # ...
```

**Переваги Repository:**
- ✅ Централізована Query Builder
- ✅ Легко змінити БД (замінити на MongoDB, etc)
- ✅ Тестування без БД (mock repository)

#### 3. Design Patterns

**Strategy Pattern:**
```python
# Вибирати поведінку в runtime
class PaymentProcessor:
    def __init__(self, strategy: 'PaymentStrategy'):
        self.strategy = strategy
    
    def pay(self, amount: float):
        return self.strategy.process(amount)

class CreditCardStrategy:
    def process(self, amount: float) -> bool:
        # Обробити через Visa/Mastercard
        pass

class PayPalStrategy:
    def process(self, amount: float) -> bool:
        # Обробити через PayPal
        pass

# Вживання:
processor = PaymentProcessor(CreditCardStrategy())
processor.pay(100)  # Оплата через карту

processor = PaymentProcessor(PayPalStrategy())
processor.pay(100)  # Оплата через PayPal
```

**Factory Pattern:**
```python
# Створювання об'єктів без new
class ParserFactory:
    @staticmethod
    def get_parser(file_type: str) -> 'FileParser':
        if file_type == 'xlsx':
            return ExcelParser()
        elif file_type == 'pdf':
            return PDFParser()
        elif file_type == 'csv':
            return CSVParser()
        else:
            raise ValueError(f"Невідомий тип: {file_type}")

parser = ParserFactory.get_parser('xlsx')
data = parser.parse('file.xlsx')
```

#### 4. Performance Optimization

```python
# ❌ ПОГАНО: N+1 queries
users = User.objects.all()
for user in users:
    budget_count = user.budgets.count()  # Окремий запит!

# ✅ ДОБРЕ: Annotate
from django.db.models import Count

users = User.objects.annotate(
    budget_count=Count('budgets')
).all()

for user in users:
    print(user.budget_count)  # Жоден запит!

# ❌ ПОГАНО: Велики QuerySet
all_transactions = Transaction.objects.all()  # Мільйони!

# ✅ ДОБРЕ: Пагінація
from rest_framework.pagination import PageNumberPagination

class TransactionListView(ListAPIView):
    pagination_class = PageNumberPagination

# Автоматично: /api/transactions/?page=1&page_size=50
```

#### 5. Testing (TDD)

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

# ✅ Тест з pytest
@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(
        username='john',
        email='john@example.com',
        password='password123'
    )
    assert user.id is not None
    assert user.username == 'john'

# ✅ Тест API
@pytest.mark.django_db
def test_transaction_list_api(client):
    user = User.objects.create_user(username='john')
    
    response = client.get('/api/transactions/', HTTP_AUTHORIZATION=f'Bearer {token}')
    
    assert response.status_code == 200
    assert 'results' in response.data

# ✅ Тест сервісу (без БД)
def test_transaction_service():
    mock_user = Mock()
    
    result = TransactionService.create_transaction(
        mock_user,
        {'amount': 100, 'category': Mock()}
    )
    
    assert result is not None
```

---

## 👨‍💼 SENIOR LEVEL (5+ років)

### Обов'язкові навички

#### 1. Архітектурні рішення

```python
# Коли обирати:
# - Monolith: < 5 розробників, < 100k користувачів
# - Microservices: > 50 розробників, > 1 мільйон користувачів
# - Serverless: Спорадичні навантаження

# MyHaven сейчас: Monolith (правильна)
# У майбутньому: Можна розділити на:
# - users-service
# - transactions-service
# - budgets-service
```

#### 2. Масштабування

```
Single Server (10k users):
┌──────────────┐
│   Django App │
│   PostgreSQL │
│   Media      │
└──────────────┘

Multiple Servers (100k users):
┌─────────────────────────────┐
│   Load Balancer (nginx)     │
├─────────────┬───────────────┤
│  Django #1  │   Django #2   │  (stateless)
│  Django #3  │   Django #4   │
├─────────────────────────────┤
│   PostgreSQL (primary)      │  (read replicas)
│   PostgreSQL (replica)      │
│   Redis (cache)             │
│   S3 (media storage)        │
└─────────────────────────────┘

Millions of Users:
┌────────────────────────────────────────┐
│   CDN (media, static)                  │
├────────────────────────────────────────┤
│   Load Balancer                        │
├──────────────────────────────────────┬─┤
│   Microservices Cluster              │ │
│   (Kubernetes)                       │ │
├──────────────────────────────────────┼─┤
│   Database Cluster (PostgreSQL)      │ │
│   Message Queue (RabbitMQ/Kafka)     │ │
│   Caching Layer (Redis)              │ │
│   Search Engine (Elasticsearch)      │ │
└──────────────────────────────────────┴─┘
```

#### 3. Security Best Practices

```python
# ✅ Зберігати паролі правильно
from django.contrib.auth.hashers import make_password

user.password = make_password('user_password')  # Bcrypt, Argon2
user.save()

# ✅ API Rate Limiting
from rest_framework.throttling import UserRateThrottle

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'
    THROTTLE_RATES = {'burst': '100/hour'}

class TransactionListView(ListAPIView):
    throttle_classes = [BurstRateThrottle]

# ✅ CORS Security
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://myhaven.com',   # Продакшн
    'https://www.myhaven.com',
]

# ❌ НЕБЕЗПЕЧНО
CORS_ALLOW_ALL_ORIGINS = True

# ✅ JWT Security
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ALGORITHM': 'HS256',
}

# ✅ HTTPS тільки
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 📋 ЧАСТИНА 2: РОЗРОБКА ПРОЕКТУ

### Структура розроблення

```
Етап 1 (Тиждень 1-2): Критичні заправи
├── Реалізувати TOTP views (6 views)
├── Видалити мертві додатки (pages, reports)
├── Видалити processing.py
└── Додати тести для основного функціоналу

Етап 2 (Тиждень 3-4): Покращення кода
├── Рефакторити ExportDataView (Service Layer)
├── Додати Service до users/
├── Додати DI-контейнер
└── Додати Swagger документацію

Етап 3 (Місяць 2): Розширення функціоналу
├── Notification Service (email/telegram)
├── Budget alerts
├── Категорійні звіти
└── Експорт у CSV/PDF

Етап 4 (Місяці 3+): Масштабування
├── Redis кеш
├── Celery для фонових завдань
├── Docker & CI/CD
└── Kubernetes (якщо потрібно)
```

### Git Workflow (Best Practice)

```bash
# 1. Створити feature гілку
git checkout -b feature/totp-implementation

# 2. Зробити changes
git add backend/users/views.py
git commit -m "feat: implement TOTP setup, enable, disable views"

# 3. Push та PR
git push origin feature/totp-implementation
# Відкрити Pull Request в GitHub

# PR template:
"""
## Опис
Реалізовано TOTP (двофакторна аутентифікація):
- Генерація QR коду
- Верифікація коду
- Активація/деактивація 2FA

## Закриває
Closes #42

## Чек-лист
- [x] Код написаний
- [x] Тести додані
- [x] Документація оновлена
- [x] Немає breaking changes
"""

# 4. Code review
# Команда перевіряє, коментує
# Ви обговорюєте, вносите зміни

# 5. Merge
git merge feature/totp-implementation
git push origin main
```

### Комісійні повідомлення (Conventional Commits)

```bash
# Формат:
# <type>(<scope>): <subject>
# <body>
# <footer>

# Приклади:
git commit -m "feat(users): implement TOTP two-factor authentication

- Add TOTPSetupView for QR code generation
- Add TOTPEnableView for code verification
- Add TOTPDisableView for 2FA disable
- Add pyotp and qrcode dependencies

Closes #42"

git commit -m "fix(transactions): fix N+1 query in TransactionListAPI

Changed from filter().all() to select_related() to reduce DB queries from
N+1 to 1 for each category lookup.

Performance improvement: ~95% faster for lists with 1000+ items"

git commit -m "docs: add BACKEND_ARCHITECTURE.md

- Architecture overview
- Design patterns used
- SOLID analysis
- Developer skills guide"

git commit -m "refactor(transactions): extract ExportService

Breaking change: Moved export logic from views to services.

Migration:
- from users.views import ExportDataView
+ from users.services import ExportService"
```

---

## 🎯 СТИЛЬ КОДУ

### Правила для UI/UX

1. **Імена функцій - Англійська, доцільна**
   ```python
   ✅ get_user_transactions()
   ✅ check_budget_exceeded()
   ✅ export_all_data()
   
   ❌ получить_пользовательские_операции()
   ❌ get_user_trans()
   ❌ export()
   ```

2. **Коментарі - Українська, для підтримувачів**
   ```python
   ✅ # Перевіримо, чи перевищено бюджет за місяць
   ✅ # FIXME: Потребує оптимізації для > 100k транзакцій
   
   ❌ # Проверяем бюджет (кириллиця)
   ❌ # TODO: fix this (англійський коментар без деталей)
   ```

3. **Type Hints - Обов'язково**
   ```python
   ✅ def get_transactions(user: User, limit: int = 10) -> List[Transaction]:
   ✅ def match(self, description: str, amount: float) -> Tuple[Optional[Category], float]:
   
   ❌ def get_transactions(user, limit=10):
   ```

4. **Docstrings - Google Style**
   ```python
   ✅ Правильно:
   def create_budget(user: User, category: Category, month: date, amount: Decimal) -> Budget:
       """Створити новий бюджет для користувача.
       
       Args:
           user: Користувач, для якого створюємо бюджет
           category: Категорія видатків
           month: Місяць у форматі YYYY-MM-01
           amount: Ліміт бюджету
       
       Returns:
           Об'єкт Budget
       
       Raises:
           ValidationError: Якщо бюджет на цей місяць вже існує
       
       Example:
           >>> budget = create_budget(user, category, date(2026, 4, 1), 1000)
           >>> budget.amount
           Decimal('1000.00')
       """
   
   ❌ Неправильно:
   def create_budget(user, category, month, amount):
       # Create budget
       pass
   ```

### Логування

```python
import logging

logger = logging.getLogger(__name__)

# ✅ INFO - Нормальні дії
logger.info("User %s created new budget", user.id)
logger.info("Processed %d transactions from upload %s", count, upload.id)

# ✅ WARNING - Щось не так, але ще працює
logger.warning("User %s tried to delete non-existent budget", user.id)
logger.warning("Failed to parse %s from upload, skipped", row_num)

# ✅ ERROR - Серйозна помилка
logger.error("Failed to process upload %s: %s", upload.id, str(e))

# ✅ CRITICAL - Система впаде
logger.critical("Database connection lost!")

# ❌ ПОГАНО: print()
print("User created")  # Не зберігається, не видно в продакшені

# ❌ ПОГАНО: DEBUG у продакшені
logger.debug("User %s has %d transactions", user.id, tx_count)
# В продакшені DEBUG вимкнено, тому це не видно
```

---

## 📊 МЕТРИКИ ЯКОСТІ

### Test Coverage

```bash
# Запустити тести з покриттям
pytest --cov=backend --cov-report=html

# Результат:
# backend/users:        95%
# backend/transactions: 85%
# backend/budgets:      90%
# TOTAL:                90%

# 🎯 TARGET: >= 80%
```

### Code Quality (Pylint)

```bash
pylint backend/users/*.py

# Результат:
# backend/users/models.py:     10/10 (Perfect!)
# backend/users/views.py:       8.5/10 (Good)
# backend/users/services.py:    9/10 (Very Good)
```

### Performance

```
# Before optimization:
- List transactions: 500ms (N+1 queries)
- Get dashboard:     800ms (5 separate queries)

# After optimization:
- List transactions: 50ms (1 query + cache)
- Get dashboard:     100ms (1 optimized query)

# 🎯 TARGET: Response < 200ms
```

---

## 🚀 РОЗГОРТАННЯ

### Development (Local)

```bash
python manage.py runserver
# http://localhost:8000
```

### Staging (Test Server)

```bash
# .env.staging
DEBUG=False
ALLOWED_HOSTS=staging.myhaven.com
SECRET_KEY=...
DATABASE_URL=postgres://...

gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

### Production

```bash
# .env.production
DEBUG=False
ALLOWED_HOSTS=myhaven.com,www.myhaven.com
SECRET_KEY=<VERY_LONG_SECRET>
DATABASE_URL=postgres://...
SECURE_SSL_REDIRECT=True

# Запуск з gunicorn + nginx
gunicorn core.wsgi:application \
  --workers 4 \
  --bind 127.0.0.1:8000 \
  --timeout 60
```

---

## 📚 РЕСУРСИ ДЛЯ НАВЧАННЯ

### Книги
1. "Two Scoops of Django 3.2" - Best practices
2. "Django for Beginners" - For juniors
3. "Microservices Patterns" - For seniors

### Онлайн ресурси
1. https://docs.djangoproject.com - Official Django Docs
2. https://www.django-rest-framework.org - DRF Docs
3. https://testdriven.io - Django Testing
4. https://www.realpython.com - Quality tutorials

### Курси
1. Udemy: "Python Django Web Framework"
2. Real Python: "Django Async"
3. Pluralsight: "Django Microservices"

---

## 🎓 ВИСНОВОК

Проект готовий до розвитку! Архітектура добра, потребує:

1. ✅ **Для Junior:** Вивчити ORM, DRF, тестування
2. ✅ **Для Middle:** Service Layer, Design Patterns, Performance
3. ✅ **Для Senior:** Архітектура, Масштабування, DevOps

**Рекомендований порядок розгортання:**
1. Тести (TDD)
2. TOTP views
3. Service Layer рефакторинг
4. CI/CD & Docker
5. Масштабування

