from rest_framework import serializers
from django.db.models import Sum, Q
from .models import Budget
from transactions.models import Category


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_name', 'month', 'amount', 'spent']
        read_only_fields = ['id']

    def get_spent(self, obj):
        """Фактичні витрати за цю категорію в цьому місяці."""
        from transactions.models import Transaction
        from django.utils import timezone
        import calendar

        year = obj.month.year
        month = obj.month.month
        last_day = calendar.monthrange(year, month)[1]

        total = Transaction.objects.filter(
            account__user=obj.user,
            category=obj.category,
            amount__lt=0,
            transaction_date__date__gte=obj.month,
            transaction_date__date__lte=obj.month.replace(day=last_day),
        ).aggregate(t=Sum('amount'))['t'] or 0

        return abs(total)


class BudgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'category', 'month', 'amount']
        read_only_fields = ['id']

    def validate_month(self, value):
        """Переконуємось що це перший день місяця."""
        return value.replace(day=1)
