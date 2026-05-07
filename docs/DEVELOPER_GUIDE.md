# Developer Onboarding Guide — MyHaven Backend

**Version:** 1.0 | **Updated:** May 6, 2026

---

## 🎯 Швидкий старт для розробника (2 хвилини)

### 1️⃣ Прочитай ці файли В ПЕРШУ ЧЕРГУ

| Файл | Що там | Для кого |
|------|--------|----------|
| [AI.md](AI.md) | Карта проекту, рішення | **ВСІ** - прочитай першим! |
| [.cursorrules](.cursorrules) | Правила кодування | ШІ-агент (і розробники) |
| [TDD_GUIDE.md](TDD_GUIDE.md) | Як писати тести | Розробники |
| [REGRESSION_TESTING.md](REGRESSION_TESTING.md) | Регресійне тестування | Розробники (перед коммітом) |

### 2️⃣ Встанови залежності

```bash
# Перейди у папку backend
cd backend

# Встанови залежності (включно Black, Ruff, pytest)
pip install -r requirements.txt

# Міграції БД
python manage.py migrate
```

### 3️⃣ Запусти тести перевірити, що все працює

```bash
# Запусти повний набір тестів
pytest -v

# Повинно бути щось на кшталт:
# ========================== 25 passed in 2.34s ==========================
```

### 4️⃣ Запусти сервер

```bash
python manage.py runserver
# Сервер на http://localhost:8000/
# Swagger UI на http://localhost:8000/api/docs/
```

---

## 🗂️ Структура проекту

```
MyHavenProject/
├── AI.md                     # ← Прочитай першим!
├── .cursorrules              # Правила для ШІ
├── TDD_GUIDE.md              # Як писати тести
├── REGRESSION_TESTING.md     # Регресійне тестування
├── run_checks.ps1            # Скрипт перевірок (Windows)
├── run_checks.sh             # Скрипт перевірок (Unix)
├── pytest.ini                # Налаштування pytest
│
└── backend/
    ├── conftest.py           # Фікстури для тестів
    ├── requirements.txt      # Залежності (Black, Ruff, pytest, ...)
    ├── manage.py
    │
    ├── core/                 # Django config
    ├── users/                # App: Users & Auth
    ├── accounts/             # App: Bank Accounts
    ├── transactions/         # App: Transactions (Core logic)
    ├── budgets/              # App: Budgets
    ├── telegram_api/         # App: Telegram Bot API (NEW)
    └── tests/                # Integration tests
```

---

## 🚀 Типовий рабочий день (Typical Workflow)

### Ранок: Синхронізація з Гітом

```bash
git pull origin main
pip install -r requirements.txt  # Якщо додали залежности
python manage.py migrate         # Якщо були міграції
```

### День: Розробка нової функції

**1. Прочитай завдання та подумай**
- Що потребує розробка?
- Які apps це стосується?
- Де писати код? (models, services, views?)

**2. Напиши тест (Red — TDD Крок 1)**
```bash
# Example: Додаємо функцію подвоєння суми
# File: backend/transactions/tests.py
def test_double_monthly_expenses_red(self):
    # Write test that FAILS
    result = TransactionService.double_monthly_expenses(user, 5, 2026)
    self.assertEqual(result, Decimal('-160.00'))

# Run test
pytest transactions/tests.py::TransactionServiceTests::test_double_monthly_expenses_red -v
# Result: FAILED ✗
```

**3. Напиши мінімальний код (Green — TDD Крок 2)**
```python
# File: backend/transactions/services.py
def double_monthly_expenses(user, month, year):
    expenses = Transaction.objects.filter(...).aggregate(...)
    return expenses * 2
```

```bash
# Run test
pytest transactions/tests.py::TransactionServiceTests::test_double_monthly_expenses_red -v
# Result: PASSED ✓
```

**4. Вирівняй код (Refactor — TDD Крок 3)**
```bash
# Запусти автоматичні проверки
./run_checks.ps1  # На Windows
# або
./run_checks.sh   # На Unix

# Це запустить:
# 1. Тести (pytest)
# 2. Linter (ruff)
# 3. Formatter (black)
```

**5. Запусти регресійні тести (Regression)**
```bash
# Перевір, що ти не "сломав" нічого
pytest -v
# Всі тести мають бути PASSED ✓
```

### Напередодні коммітту: Фінальні перевірки

```bash
# 1. Вирівняй код
./run_checks.ps1

# 2. Запусти регресію
pytest -v

# 3. Якщо ВСІ тести зелені → Коммітити!
git add [files]
git commit -m "feat: [description]"
git push origin [your-branch]
```

---

## 📂 Де писати код? (Architecture Decision Tree)

```
Моя нова функція —> ГДЕ ПИСАТИ?

├─ Це модель даних?
│  └─ → models.py (Transaction, Category, Budget, etc.)
│
├─ Це бізнес-логіка? (розрахунки, перевірки, обробка)
│  └─ → services.py (TransactionService, ExportService, etc.)
│
├─ Це запити до БД?
│  └─ → repositories.py (TransactionRepository, etc.)
│
├─ Це REST API endpoint?
│  └─ → views.py (APIView, generics.RetrieveUpdateAPIView)
│
├─ Це передача даних через API?
│  └─ → serializers.py (ModelSerializer)
│
├─ Це маршрути URL?
│  └─ → urls.py (path patterns)
│
└─ Це тест?
   └─ → tests.py (TestCase, pytest)
```

---

## ⚠️ Типові помилки (Common Mistakes)

### ❌ Помилка 1: Логіка у views.py

```python
# ❌ НЕПРАВИЛЬНО
class MyView(APIView):
    def post(self, request):
        data = request.data
        # ... 100 рядків коду ...
        transaction = Transaction.objects.create(...)
        return Response(...)

# ✅ ПРАВИЛЬНО
class MyView(APIView):
    def post(self, request):
        service = MyService()
        result = service.do_something(data)
        return Response(result)
```

### ❌ Помилка 2: Тест без аертів

```python
# ❌ НЕПРАВИЛЬНО
def test_something(self):
    result = my_function()
    # Немає assertion!

# ✅ ПРАВИЛЬНО
def test_something(self):
    result = my_function()
    self.assertEqual(result, expected_value)
```

### ❌ Помилка 3: Редагування production-даних у тестах

```python
# ❌ НЕПРАВИЛЬНО
def test_delete(self):
    user = get_user_model().objects.first()  # Real user!
    user.delete()

# ✅ ПРАВИЛЬНО (створи test-дані)
def setUp(self):
    self.user = get_user_model().objects.create_user(...)
def test_delete(self):
    self.user.delete()
    self.assertFalse(get_user_model().objects.filter(id=self.user.id).exists())
```

### ❌ Помилка 4: Коммітити з падаючими тестами

```bash
# ❌ НЕПРАВИЛЬНО
pytest -v  # 2 tests FAILED
git commit -m "Fixed something"  # ✗ FORBIDDEN!

# ✅ ПРАВИЛЬНО
pytest -v  # ✓ 25 passed
git commit -m "Fixed something"  # ✓ OK!
```

---

## 🧪 Форматування кода перед коммітом

### Автоматичний способ (РЕКОМЕНДУЄТЬСЯ)

```bash
# Запусти один скрипт — все зробиться автоматично
./run_checks.ps1  # Windows
# або
./run_checks.sh   # Unix
```

### Ручний способ

```bash
# 1. Форматування (Black)
black backend/

# 2. Linting (Ruff)
ruff check backend/ --fix

# 3. Тести
pytest -v

# 4. Якщо все зелене → коммітити
```

---

## 🔄 Як працювати з ШІ-агентом

### Твоя роль:
1. Дай завдання: "Додай функцію [назва]"
2. Показуй результати тестів: "Тести падають?"
3. Перевіряй: "Регресія чиста?"
4. Коммітий: "Готово до merge?"

### Роль ШІ-агента:
1. Читає AI.md та .cursorrules
2. Пише Red тест (падає)
3. Пише Green код (проходить)
4. Запускає Refactor (ruff, black)
5. Запускає регресію (pytest)
6. Говорить: "✅ Готово!"

### Магічні слова:
```
"Напиши тест, що ПАДАЄ, потім код, що ПРОХОДИТЬ"
"Запусти ./run_checks.ps1"
"Чи регресія чиста? (pytest -v)"
"Готово до коммітку?"
```

---

## 📞 Команди для швидкого доступу

| Завдання | Команда |
|----------|---------|
| Запустити сервер | `python manage.py runserver` |
| Запустити тести | `pytest -v` |
| Запустити регресію | `pytest -v` (то же самое) |
| Запустити перевірки | `./run_checks.ps1` |
| Запустити конкретний тест | `pytest users/tests.py::UserServicesTests::test_export_service_contains_expected_sections -v` |
| Форматування коду | `black backend/` |
| Linting | `ruff check backend/ --fix` |
| Миграції | `python manage.py migrate` |
| Создать міграцію | `python manage.py makemigrations` |
| Swagger UI | `http://localhost:8000/api/docs/` |
| OpenAPI Schema | `http://localhost:8000/api/schema/` |

---

## ✅ Чеклист перед початком розробки

- [ ] Прочитав AI.md
- [ ] Встановив залежності (`pip install -r requirements.txt`)
- [ ] Запустив міграції (`python manage.py migrate`)
- [ ] Запустив тести (`pytest -v`) — усі зелені ✅
- [ ] Запустив сервер (`python manage.py runserver`)
- [ ] Відкрив Swagger UI (`http://localhost:8000/api/docs/`)
- [ ] Готовий розробляти!

---

## 🎓 Resources

- **Backend Docs:** [BACKEND_ARCHITECTURE.md](backend/BACKEND_ARCHITECTURE.md)
- **Code Review:** [CODE_REVIEW.md](backend/CODE_REVIEW.md)
- **Development Guide:** [DEVELOPMENT_GUIDE.md](backend/DEVELOPMENT_GUIDE.md)

---

**Last Updated:** May 6, 2026
**For Issues:** Check AI.md or .cursorrules
