from django.urls import reverse
from rest_framework import serializers
from .models import Transaction, Category, TransactionUpload
from .categorization import find_category_by_name
from .uploads import display_name


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type']


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_date',
            'description',
            'amount',
            'category',
            'source',
        ]


class TransactionWriteSerializer(serializers.ModelSerializer):
    """Серіалізатор для створення/редагування транзакцій."""
    category_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'amount',
            'description',
            'transaction_date',
            'category',
            'category_name',
        ]
        read_only_fields = ['id']

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

        return attrs


class UploadSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source='bank.name', read_only=True, default=None)
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = TransactionUpload
        fields = [
            'id', 'bank', 'bank_name', 'file', 'file_url', 'file_name',
            'status', 'uploaded_at', 'total_transactions',
            'processed_transactions', 'processing_log',
        ]
        read_only_fields = [
            'id', 'status', 'uploaded_at',
            'total_transactions', 'processed_transactions', 'processing_log',
        ]
        # Шлях у storage не віддаємо: файл доступний лише через file_url
        # з перевіркою власника.
        extra_kwargs = {'file': {'write_only': True}}

    def get_file_url(self, obj):
        if not obj.file or not obj.pk:
            return None
        url = reverse('transactions:api-upload-file', args=[obj.pk])
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url

    def get_file_name(self, obj):
        return display_name(obj)
