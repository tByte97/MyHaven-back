"""
conftest.py — Pytest configuration and shared fixtures for MyHaven Backend
Location: backend/conftest.py (or backend/tests/conftest.py)
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Bank, Account
from budgets.models import Budget
from transactions.models import Category, Transaction, TransactionUpload


# Получаємо модель користувача
User = get_user_model()


# ════════════════════════════════════════════════════════════════
# Fixtures for Users
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass1234!',
    )


@pytest.fixture
def test_user_2(db):
    """Create a second test user (for user isolation tests)."""
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='TestPass1234!',
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='AdminPass1234!',
    )


# ════════════════════════════════════════════════════════════════
# Fixtures for Banks & Accounts
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def test_bank(db):
    """Create a test bank."""
    return Bank.objects.create(
        name='TestBank',
    )


@pytest.fixture
def bank_account(db, test_user, test_bank):
    """Create a test bank account."""
    return Account.objects.create(
        user=test_user,
        bank=test_bank,
        account_name='Test Account',
        account_type='BANK',
        currency='UAH',
    )


@pytest.fixture
def cash_account(db, test_user):
    """Create a test cash account."""
    return Account.objects.create(
        user=test_user,
        bank=None,
        account_name='Wallet',
        account_type='CASH',
        currency='UAH',
    )


# ════════════════════════════════════════════════════════════════
# Fixtures for Categories
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def expense_category(db, test_user):
    """Create a test expense category."""
    return Category.objects.create(
        user=test_user,
        name='Food',
        type='EXPENSE',
        keywords=['shop', 'market', 'supermarket'],
    )


@pytest.fixture
def income_category(db, test_user):
    """Create a test income category."""
    return Category.objects.create(
        user=test_user,
        name='Salary',
        type='INCOME',
        keywords=['salary', 'wage'],
    )


@pytest.fixture
def system_category(db):
    """Create a system-wide category."""
    return Category.objects.create(
        user=None,
        name='Other',
        type='EXPENSE',
        is_system=True,
    )


# ════════════════════════════════════════════════════════════════
# Fixtures for Transactions
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def expense_transaction(db, test_user, bank_account, expense_category):
    """Create a test expense transaction."""
    return Transaction.objects.create(
        account=bank_account,
        category=expense_category,
        amount=Decimal('-50.00'),
        description='Groceries',
        transaction_date=timezone.now(),
    )


@pytest.fixture
def income_transaction(db, test_user, bank_account, income_category):
    """Create a test income transaction."""
    return Transaction.objects.create(
        account=bank_account,
        category=income_category,
        amount=Decimal('1000.00'),
        description='Salary',
        transaction_date=timezone.now(),
    )


@pytest.fixture
def monthly_transactions(db, test_user, bank_account, expense_category):
    """Create multiple transactions for a month."""
    now = timezone.now()
    transactions = []
    
    for day in range(1, 6):  # 5 transactions
        tx = Transaction.objects.create(
            account=bank_account,
            category=expense_category,
            amount=Decimal(f'-{day * 10}.00'),
            description=f'Expense day {day}',
            transaction_date=now.replace(day=min(day, 28)),
        )
        transactions.append(tx)
    
    return transactions


# ════════════════════════════════════════════════════════════════
# Fixtures for Budgets
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def monthly_budget(db, test_user, expense_category):
    """Create a monthly budget."""
    now = timezone.now()
    return Budget.objects.create(
        user=test_user,
        category=expense_category,
        month=now.date().replace(day=1),
        amount=Decimal('500.00'),
    )


# ════════════════════════════════════════════════════════════════
# Fixtures for Uploads
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def transaction_upload(db, test_user, test_bank):
    """Create a test transaction upload."""
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    return TransactionUpload.objects.create(
        user=test_user,
        bank=test_bank,
        file=SimpleUploadedFile(
            'statement.csv',
            b'dummy,data',
            content_type='text/csv',
        ),
    )


# ════════════════════════════════════════════════════════════════
# Composite Fixtures (for complex scenarios)
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def full_user_setup(db, test_user, bank_account, expense_category, 
                     income_category, monthly_transactions, monthly_budget):
    """
    Complete user setup with:
    - User account
    - Bank account
    - Categories (expense + income)
    - Multiple transactions
    - Monthly budget
    """
    return {
        'user': test_user,
        'account': bank_account,
        'expense_category': expense_category,
        'income_category': income_category,
        'transactions': monthly_transactions,
        'budget': monthly_budget,
    }


# ════════════════════════════════════════════════════════════════
# Pytest Markers
# ════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>1s)"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as a regression test"
    )


# ════════════════════════════════════════════════════════════════
# Django Settings for Tests
# ════════════════════════════════════════════════════════════════

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
