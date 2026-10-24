from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Account
from budgets.models import Budget

from .models import Category, Transaction


class CategoryOwnershipTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='owner', email='owner@example.com', password='Pass1234!',
            telegram_user_id=1001,
        )
        self.stranger = user_model.objects.create_user(
            username='stranger', email='stranger@example.com', password='Pass1234!',
        )
        self.own_expense = Category.objects.create(user=self.user, name='Їжа', type='EXPENSE')
        self.own_income = Category.objects.create(user=self.user, name='Зарплата', type='INCOME')
        self.system_expense = Category.objects.create(name='Інше', type='EXPENSE', is_system=True)
        self.foreign = Category.objects.create(
            user=self.stranger, name='Секретна категорія', type='EXPENSE',
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _create_transaction(self, category):
        return self.client.post('/transactions/api/create/', {
            'amount': '-50.00',
            'description': 'Кава',
            'transaction_date': timezone.now().isoformat(),
            'category': category.id,
        }, format='json')

    def test_cannot_assign_foreign_category_to_transaction(self):
        response = self._create_transaction(self.foreign)

        self.assertEqual(response.status_code, 400)
        self.assertIn('category', response.data)
        self.assertNotIn(self.foreign.name, str(response.data))
        self.assertFalse(Transaction.objects.exists())

    def test_foreign_category_error_matches_missing_category(self):
        foreign = self._create_transaction(self.foreign)
        missing = self.client.post('/transactions/api/create/', {
            'amount': '-50.00',
            'description': 'Кава',
            'transaction_date': timezone.now().isoformat(),
            'category': 999999,
        }, format='json')

        # Відповідь не повинна видавати, що категорія з таким ID існує.
        self.assertEqual(
            str(foreign.data['category'][0]).replace(str(self.foreign.id), 'ID'),
            str(missing.data['category'][0]).replace('999999', 'ID'),
        )

    def test_can_assign_own_and_system_categories(self):
        self.assertEqual(self._create_transaction(self.own_expense).status_code, 201)
        self.assertEqual(self._create_transaction(self.system_expense).status_code, 201)

    def test_telegram_patch_cannot_assign_foreign_category(self):
        account = Account.objects.create(user=self.user, account_name='Main')
        transaction = Transaction.objects.create(
            account=account, amount=Decimal('-10'), description='Таксі',
            transaction_date=timezone.now(), category=self.own_expense,
        )
        self.client.credentials(HTTP_X_TELEGRAM_USER_ID='1001')

        response = self.client.patch(
            f'/api/telegram/transactions/{transaction.id}/',
            {'category': self.foreign.id},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, self.own_expense)

    def _create_budget(self, **payload):
        data = {'month': '2026-10-15', 'amount': '1000.00', **payload}
        return self.client.post('/api/budgets/', data, format='json')

    def test_cannot_create_budget_for_foreign_category(self):
        response = self._create_budget(category=self.foreign.id)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Budget.objects.exists())

    def test_cannot_create_budget_for_income_category(self):
        by_id = self._create_budget(category=self.own_income.id)
        by_name = self._create_budget(category_name='Зарплата')

        self.assertEqual(by_id.status_code, 400)
        self.assertEqual(by_name.status_code, 400)
        self.assertFalse(Budget.objects.exists())

    def test_duplicate_budget_returns_validation_error(self):
        first = self._create_budget(category=self.own_expense.id)
        duplicate = self._create_budget(category=self.own_expense.id, month='2026-10-01')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(Budget.objects.count(), 1)

    def test_updating_budget_into_duplicate_returns_validation_error(self):
        Budget.objects.create(
            user=self.user, category=self.own_expense, month=date(2026, 10, 1), amount=100,
        )
        other = Budget.objects.create(
            user=self.user, category=self.system_expense, month=date(2026, 10, 1), amount=100,
        )

        response = self.client.patch(
            f'/api/budgets/{other.id}/', {'category': self.own_expense.id}, format='json',
        )

        self.assertEqual(response.status_code, 400)
        other.refresh_from_db()
        self.assertEqual(other.category, self.system_expense)

    def test_updating_budget_amount_keeps_working(self):
        budget = Budget.objects.create(
            user=self.user, category=self.own_expense, month=date(2026, 10, 1), amount=100,
        )

        response = self.client.patch(
            f'/api/budgets/{budget.id}/', {'amount': '250.00'}, format='json',
        )

        self.assertEqual(response.status_code, 200)
        budget.refresh_from_db()
        self.assertEqual(budget.amount, Decimal('250.00'))
