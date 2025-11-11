from rest_framework import serializers
from .models import Transaction, Category

# "Перекладач" для моделі Category
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type']

# "Перекладач" для моделі Transaction
class TransactionSerializer(serializers.ModelSerializer):
    # Ми кажемо, що поле 'category' має бути "розшифроване"
    # за допомогою іншого "перекладача"
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 
            'transaction_date', 
            'description', 
            'amount', 
            'category' # 'category' тепер буде JSON-об'єктом, а не ID
        ]