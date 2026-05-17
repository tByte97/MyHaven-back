from django.db import models
from django.conf import settings
from accounts.models import Account, Bank

class Category(models.Model):
    TRANSACTION_TYPES = (('INCOME', 'Дохід'), ('EXPENSE', 'Витрата'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    is_system = models.BooleanField(default=False)  

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions', null = True, blank = True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    SOURCE_CHOICES = (
        ('import', 'Імпорт з банку'),
        ('manual', 'Вручну'),
        ('telegram', 'Telegram Бот'),
    )
    source = models.CharField(
        max_length=20, 
        choices=SOURCE_CHOICES, 
        default='import'
    )

    raw_description = models.TextField(blank=True) 
    bank_category = models.CharField(max_length=200, blank=True)  
    matched_automatically = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)
    source_upload = models.ForeignKey(
        'TransactionUpload', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='transactions')

    class Meta:
        ordering = ['-transaction_date']
        verbose_name = "Транзакція"
        verbose_name_plural = "Транзакції"

    def __str__(self):
        return f"{self.description}: {self.amount}"


class TransactionUpload(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Очікує'),
        ('PROCESSING', 'В обробці'),
        ('COMPLETED', 'Завершено'),
        ('FAILED', 'Помилка'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='bank_statements/%Y/%m/')
    bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_transactions = models.IntegerField(default=0)
    processed_transactions = models.IntegerField(default=0)
    processing_log = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Завантаження виписки"
        verbose_name_plural = "Завантаження виписок"

    def __str__(self):
        return f"Завантаження від {self.user.email} о {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"