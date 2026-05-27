from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account, Bank
from transactions.models import Category, Transaction

from .models import Budget
from .serializers import BudgetCreateSerializer, BudgetSerializer


class BudgetCriticalPathTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='budget_user',
            email='budget_user@example.com',
            password='Pass1234!',
        )
        self.other_user = get_user_model().objects.create_user(
            username='other_budget_user',
            email='other_budget_user@example.com',
            password='Pass1234!',
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Продукти',
            type='EXPENSE',
            keywords=['магазин'],
        )
        self.other_category = Category.objects.create(
            user=self.user,
            name='Транспорт',
            type='EXPENSE',
        )
        bank = Bank.objects.create(name='BudgetBank')
        self.account = Account.objects.create(
            user=self.user,
            bank=bank,
            account_name='Main',
            account_type='BANK',
            currency='UAH',
        )
        self.other_account = Account.objects.create(
            user=self.other_user,
            bank=bank,
            account_name='Other',
            account_type='BANK',
            currency='UAH',
        )

    def test_budget_serializer_spent_counts_only_matching_user_category_month_expenses(self):
        month = timezone.now().date().replace(day=1)
        budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            month=month,
            amount=Decimal('1000.00'),
        )
        current_month_date = timezone.make_aware(
            timezone.datetime(month.year, month.month, 10, 12, 0)
        )
        previous_month_date = current_month_date - timezone.timedelta(days=35)

        Transaction.objects.create(
            account=self.account,
            category=self.category,
            amount=Decimal('-100.00'),
            description='Groceries',
            transaction_date=current_month_date,
        )
        Transaction.objects.create(
            account=self.account,
            category=self.category,
            amount=Decimal('25.00'),
            description='Refund',
            transaction_date=current_month_date,
        )
        Transaction.objects.create(
            account=self.account,
            category=self.other_category,
            amount=Decimal('-300.00'),
            description='Taxi',
            transaction_date=current_month_date,
        )
        Transaction.objects.create(
            account=self.account,
            category=self.category,
            amount=Decimal('-500.00'),
            description='Old groceries',
            transaction_date=previous_month_date,
        )
        Transaction.objects.create(
            account=self.other_account,
            category=self.category,
            amount=Decimal('-999.00'),
            description='Foreign user groceries',
            transaction_date=current_month_date,
        )

        data = BudgetSerializer(budget).data

        self.assertEqual(data['spent'], Decimal('100.00'))

    def test_budget_create_serializer_resolves_category_name_and_normalizes_month(self):
        serializer = BudgetCreateSerializer(
            data={
                'category_name': 'продуктів',
                'month': '2026-05-22',
                'amount': '3000.00',
            },
            context={'request': SimpleNamespace(user=self.user)},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        budget = serializer.save(user=self.user)

        self.assertEqual(budget.category, self.category)
        self.assertEqual(budget.month.isoformat(), '2026-05-01')

    def test_budget_create_serializer_requires_category_or_category_name(self):
        serializer = BudgetCreateSerializer(
            data={'month': '2026-05-01', 'amount': '3000.00'},
            context={'request': SimpleNamespace(user=self.user)},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)
