from rest_framework import serializers
from django.db.models import Sum
from .models import Budget
from transactions.categorization import find_category_by_name


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
    category_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_name', 'month', 'amount']
        read_only_fields = ['id']
        extra_kwargs = {
            'category': {'required': False},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        category_name = (attrs.pop('category_name', '') or '').strip()

        if not attrs.get('category') and category_name:
            request = self.context.get('request')
            if not request or not request.user or not request.user.is_authenticated:
                raise serializers.ValidationError({
                    'category_name': 'Authenticated user is required to resolve category_name.'
                })

            category = find_category_by_name(request.user, category_name)
            if not category:
                raise serializers.ValidationError({
                    'category_name': f'Category "{category_name}" was not found.'
                })
            attrs['category'] = category

        has_existing_category = bool(self.instance and self.instance.category_id)
        if not attrs.get('category') and not has_existing_category:
            raise serializers.ValidationError({
                'category': 'category or category_name is required.'
            })

        return attrs

    def validate_month(self, value):
        """Переконуємось що це перший день місяця."""
        return value.replace(day=1)
