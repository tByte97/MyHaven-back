from rest_framework import serializers
from .models import Transaction, Category, TransactionUpload
from .categorization import find_category_by_name


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

    class Meta:
        model = TransactionUpload
        fields = [
            'id', 'bank', 'bank_name', 'file', 'file_url',
            'status', 'uploaded_at', 'total_transactions',
            'processed_transactions', 'processing_log',
        ]
        read_only_fields = [
            'id', 'status', 'uploaded_at',
            'total_transactions', 'processed_transactions', 'processing_log',
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
