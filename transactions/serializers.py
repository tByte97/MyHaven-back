from rest_framework import serializers
from .models import Transaction, Category, TransactionUpload


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
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'description', 'transaction_date', 'category']
        read_only_fields = ['id']


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