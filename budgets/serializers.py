from rest_framework import serializers
from django.db.models import Sum
from .models import Budget
from transactions.categorization import categories_visible_to, find_category_by_name


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Лише власні/системні категорії витрат; чужий ID — як неіснуючий.
        self.fields['category'].queryset = categories_visible_to(
            self._request_user()
        ).filter(type='EXPENSE')

    def _request_user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

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
            if category.type != 'EXPENSE':
                raise serializers.ValidationError({
                    'category_name': 'Budget can be set only for an expense category.'
                })
            attrs['category'] = category

        has_existing_category = bool(self.instance and self.instance.category_id)
        if not attrs.get('category') and not has_existing_category:
            raise serializers.ValidationError({
                'category': 'category or category_name is required.'
            })

        self._validate_unique_for_user(attrs)
        return attrs

    def _validate_unique_for_user(self, attrs):
        # user не входить у fields, тому стандартний UniqueTogetherValidator
        # не спрацьовує і дубль падав з IntegrityError (500).
        user = self._request_user()
        if user is None or not user.is_authenticated:
            return
        category = attrs.get('category') or getattr(self.instance, 'category', None)
        month = attrs.get('month') or getattr(self.instance, 'month', None)
        if category is None or month is None:
            return
        duplicates = Budget.objects.filter(user=user, category=category, month=month)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                'Budget for this category and month already exists.'
            )

    def validate_month(self, value):
        """Переконуємось що це перший день місяця."""
        return value.replace(day=1)
