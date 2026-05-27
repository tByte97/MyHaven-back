from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from transactions.models import Transaction

from .models import Account, Bank


class AccountCriticalPathTests(TestCase):
    def test_calculated_balance_sums_only_related_transactions(self):
        user = get_user_model().objects.create_user(
            username='account_user',
            email='account_user@example.com',
            password='Pass1234!',
        )
        bank = Bank.objects.create(name='BalanceBank')
        main_account = Account.objects.create(
            user=user,
            bank=bank,
            account_name='Main',
            account_type='BANK',
            currency='UAH',
        )
        other_account = Account.objects.create(
            user=user,
            bank=bank,
            account_name='Other',
            account_type='BANK',
            currency='UAH',
        )

        Transaction.objects.create(
            account=main_account,
            amount=Decimal('500.00'),
            description='Income',
            transaction_date=timezone.now(),
        )
        Transaction.objects.create(
            account=main_account,
            amount=Decimal('-125.50'),
            description='Expense',
            transaction_date=timezone.now(),
        )
        Transaction.objects.create(
            account=other_account,
            amount=Decimal('999.00'),
            description='Other account income',
            transaction_date=timezone.now(),
        )

        self.assertEqual(main_account.calculated_balance, Decimal('374.50'))
