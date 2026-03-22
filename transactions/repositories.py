import logging
import calendar as cal_mod
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta, date
from .models import Transaction

logger = logging.getLogger(__name__)


class TransactionRepository:
    """
    Єдина точка доступу до даних транзакцій користувача.
    Інкапсулює всі ORM-запити (Repository Pattern).
    """

    def __init__(self, user, upload_ids=None):
        self.user = user
        self.upload_ids = upload_ids or []

    def get_queryset(self):
        """Базовий queryset з урахуванням фільтра по завантаженнях."""
        qs = Transaction.objects.filter(
            account__user=self.user
        ).select_related('category', 'account', 'account__bank')

        if self.upload_ids:
            qs = qs.filter(source_upload__id__in=self.upload_ids)
        return qs

    # ─── KPI & Dashboard ────────────────────────────────────────

    def get_dashboard_kpi(self):
        """KPI за останні 30 днів: витрати, доходи, баланс."""
        month_ago = timezone.now() - timedelta(days=30)
        qs = self.get_queryset().filter(transaction_date__gte=month_ago)

        expenses = qs.filter(amount__lt=0).aggregate(t=Sum('amount'))['t'] or 0
        incomes = qs.filter(amount__gt=0).aggregate(t=Sum('amount'))['t'] or 0

        return {
            'total_expenses': abs(expenses),
            'total_incomes': incomes,
            'balance': incomes + expenses,
            'has_transactions': self.get_queryset().exists(),
        }

    def get_recent_transactions(self, limit=10):
        return self.get_queryset().order_by('-transaction_date')[:limit]

    def get_top_expense_categories(self, limit=5):
        """Топ категорій витрат за останні 30 днів."""
        month_ago = timezone.now() - timedelta(days=30)
        return self.get_queryset().filter(
            transaction_date__gte=month_ago,
            amount__lt=0,
            category__isnull=False,
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('total')[:limit]

    # ─── Statistics ─────────────────────────────────────────────

    def get_monthly_statistics(self, months=6):
        date_from = timezone.now() - timedelta(days=months * 30)
        return self.get_queryset().filter(
            transaction_date__gte=date_from
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            total_expenses=Sum('amount', filter=Q(amount__lt=0)),
            total_incomes=Sum('amount', filter=Q(amount__gt=0)),
        ).order_by('month')

    def get_category_stats(self, months=6, transaction_type='EXPENSE'):
        date_from = timezone.now() - timedelta(days=months * 30)
        qs = self.get_queryset().filter(transaction_date__gte=date_from)

        if transaction_type == 'EXPENSE':
            qs = qs.filter(amount__lt=0)
            order_by = 'total'
        else:
            qs = qs.filter(amount__gt=0)
            order_by = '-total'

        return qs.filter(category__isnull=False).values(
            'category__name'
        ).annotate(total=Sum('amount')).order_by(order_by)

    def get_bank_stats(self, months=6):
        date_from = timezone.now() - timedelta(days=months * 30)
        return self.get_queryset().filter(
            transaction_date__gte=date_from
        ).values('account__bank__name').annotate(
            expenses=Sum('amount', filter=Q(amount__lt=0)),
            incomes=Sum('amount', filter=Q(amount__gt=0)),
        ).order_by('account__bank__name')

    # ─── Calendar ───────────────────────────────────────────────

    def get_calendar_data(self, year, month):
        """Денні витрати + доходи за вказаний місяць."""
        last_day = cal_mod.monthrange(year, month)[1]
        start = date(year, month, 1)
        end = date(year, month, last_day)

        daily = self.get_queryset().filter(
            transaction_date__date__gte=start,
            transaction_date__date__lte=end,
        ).annotate(
            day=TruncDate('transaction_date'),
        ).values('day').annotate(
            expenses=Sum('amount', filter=Q(amount__lt=0)),
            incomes=Sum('amount', filter=Q(amount__gt=0)),
        ).order_by('day')

        return daily

    def get_calendar_day_transactions(self, year, month, day):
        """Транзакції за конкретний день."""
        target = date(year, month, day)
        return self.get_queryset().filter(
            transaction_date__date=target,
        ).order_by('-transaction_date')