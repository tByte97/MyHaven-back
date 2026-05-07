# TDD Guide for MyHaven Backend

**Version:** 1.0 | **Updated:** May 6, 2026

---

## 🎯 Що таке TDD?

**Test-Driven Development** — це процес розробки, де тести пишуться **ДО** коду:

1. **Red** — написи тест, який падає
2. **Green** — напиши мінімальний код, щоб тест пройшов
3. **Refactor** — вирівняй код та повтори

---

## 📚 Структура тестів у проекті

```
backend/
├── tests/
│   └── test_backend_cl.py          # Integration tests (backend + DB)
├── users/
│   └── tests.py                    # Tests for users app (services, views)
├── transactions/
│   └── tests.py                    # Tests for transactions app
├── telegram_api/
│   └── tests.py                    # Tests for Telegram API endpoints
└── budgets/
    └── tests.py                    # Tests for budgets app
```

---

## 🔴 Крок 1: Red — Написання тесту, що падає

### Приклад: Додання функції подвоєння суми

**Вимога:** Додати функцію, яка подвоює сум транзакцій користувача за місяць.

### Напиши тест (tests.py)

```python
# transactions/tests.py
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from transactions.models import Transaction, Category
from transactions.services import TransactionService
from accounts.models import Account, Bank


class TransactionServiceTests(TestCase):
    """TDD: Test-Driven Development for Transaction Services."""
    
    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Pass1234!',
        )
        self.bank = Bank.objects.create(name='TestBank')
        self.account = Account.objects.create(
            user=self.user,
            bank=self.bank,
            account_name='Test Account',
            account_type='BANK',
            currency='UAH',
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            type='EXPENSE',
        )
    
    def test_double_monthly_expenses_red(self):
        """
        RED: Test that double_monthly_expenses returns doubled sum.
        
        Given: User has 2 transactions in current month (-50.00, -30.00)
        When:  Call double_monthly_expenses(user, month=now)
        Then:  Should return -160.00 (doubled -80.00)
        """
        now = timezone.now()
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('-50.00'),
            description='Lunch',
            transaction_date=now,
        )
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            amount=Decimal('-30.00'),
            description='Snack',
            transaction_date=now,
        )
        
        result = TransactionService.double_monthly_expenses(
            user=self.user,
            month=now.month,
            year=now.year,
        )
        
        self.assertEqual(result, Decimal('-160.00'))
```

### Запусти тест — він повинен ВПАСТИ ❌

```bash
cd backend
python manage.py test transactions.tests.TransactionServiceTests.test_double_monthly_expenses_red
# або через pytest:
pytest transactions/tests.py::TransactionServiceTests::test_double_monthly_expenses_red -v
```

**Очікуваний результат:**
```
AttributeError: module 'transactions.services' has no attribute 'double_monthly_expenses'
```

---

## 🟢 Крок 2: Green — Мінімальний код для проходження тесту

### Реалізуй функцію (services.py)

```python
# transactions/services.py
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Transaction


def double_monthly_expenses(user, month: int, year: int) -> Decimal:
    """
    Calculate doubled monthly expenses for user.
    
    Args:
        user: CustomUser instance
        month: Month number (1-12)
        year: Year number (e.g., 2026)
    
    Returns:
        Doubled sum of expenses (already negative)
    """
    # Отримай витрати за місяц
    expenses = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        transaction_date__year=year,
        transaction_date__month=month,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Подвій результат
    return expenses * 2
```

### Запусти тест — він повинен ПРОЙТИ ✅

```bash
pytest transactions/tests.py::TransactionServiceTests::test_double_monthly_expenses_red -v
```

**Очікуваний результат:**
```
test_double_monthly_expenses_red PASSED ✓
```

---

## 🔵 Крок 3: Refactor — Вирівнювання коду

### 1. Запусти Ruff (linter)

```bash
ruff check backend/transactions/services.py --fix
```

### 2. Запусти Black (formatter)

```bash
black backend/transactions/services.py
```

### 3. Додай type hints (якщо немає)

```python
from typing import Union

def double_monthly_expenses(
    user: CustomUser,
    month: int,
    year: int,
) -> Decimal:  # ← Type hint важливий!
    """..."""
```

### 4. Запусти тест знову — він повинен ЩЕ ПРОЙТИ ✅

```bash
pytest transactions/tests.py::TransactionServiceTests::test_double_monthly_expenses_red -v
```

---

## 🧪 Більш складні сценарії (Advanced TDD)

### Сценарій: Користувач без транзакцій

```python
def test_double_monthly_expenses_no_transactions(self):
    """Test that function returns 0 when no transactions exist."""
    result = TransactionService.double_monthly_expenses(
        user=self.user,
        month=5,  # Future month without data
        year=2026,
    )
    self.assertEqual(result, Decimal('0'))
```

### Сценарій: Змішані дохідів і витрати

```python
def test_double_monthly_expenses_with_incomes(self):
    """Test that function only doubles expenses, ignoring incomes."""
    now = timezone.now()
    
    # Витрата
    Transaction.objects.create(
        user=self.user,
        account=self.account,
        category=self.category,
        amount=Decimal('-100.00'),  # Expense
        description='Cost',
        transaction_date=now,
    )
    
    # Дохід (повинна ігноруватися)
    Transaction.objects.create(
        user=self.user,
        account=self.account,
        category=self.category,
        amount=Decimal('200.00'),  # Income
        description='Refund',
        transaction_date=now,
    )
    
    result = TransactionService.double_monthly_expenses(
        user=self.user,
        month=now.month,
        year=now.year,
    )
    
    # Тільки -100 подвоєна = -200, не -600 (що було б, якби включили дохід)
    self.assertEqual(result, Decimal('-200.00'))
```

---

## ✅ Regression Testing — Захист від помилок

Коли додаєш нову функцію, **ЗАВЖДИ** запускай повний набір тестів:

```bash
# Запусти ВСІ тести в проекті
python manage.py test

# або через pytest з покриттям
pytest --cov=backend

# Результат повинен бути зеленим
# ================================================
# test session starts
# collected 25 items
# tests PASSED [100%]
# ================================================
```

---

## 📋 Checklist для AI-агента (Before Commit)

### Перед тим, як сказати "готово", перевір:

- [ ] **Тест написаний** — `test_*.py` файл існує
- [ ] **Тест падає** (Red) — `pytest test_new.py` → ❌ FAILED
- [ ] **Код написаний** — мінімальна реалізація
- [ ] **Тест проходить** (Green) — `pytest test_new.py` → ✅ PASSED
- [ ] **Код вирівняний** (Refactor) — `ruff --fix`, `black .`
- [ ] **Тест ЩЕ проходить** — після refactoring ✅ PASSED
- [ ] **Регресійні тести** — `pytest` всі тести проходять
- [ ] **Немає дублювання** — DRY principle
- [ ] **Type hints додані** — `def func(a: Type) -> Type:`
- [ ] **Docstring присутня** — `"""What does this do?"""`

---

## 🚀 Швидкий приклад (Complete Flow)

### 1. Red
```bash
pytest tests/test_new_feature.py
# FAILED ✗
```

### 2. Green
```python
# Write minimal code
def new_feature():
    return True
```

```bash
pytest tests/test_new_feature.py
# PASSED ✓
```

### 3. Refactor
```bash
ruff check . --fix
black .
pytest tests/test_new_feature.py
# PASSED ✓
```

### 4. Commit
```bash
git add tests/test_new_feature.py myapp/services.py
git commit -m "feat: Add new_feature with tests"
```

---

## 📞 Для ШІ-агента

Коли ти розробляєш нову функцію:

```
1. Скажи мені: "Я пишу тест для [функція]"
2. Запусти: pytest [test_file] → ❌ RED
3. Напиши мінімальний код
4. Запусти: pytest [test_file] → ✅ GREEN
5. Вирівняй: ruff --fix && black .
6. Перевір: ./run_checks.ps1 (або run_checks.sh)
7. Скажи: "✅ All tests pass, ready for commit"
```

**ВАЖЛИВО:** Якщо на кроці 6 щось падає — поверни до кроку 3!

---

**Last Updated:** May 6, 2026
