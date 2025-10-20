from django.db import models
from django.conf import settings
# Create your models here.

class Bank(models.Model):
    # Модель для зберігання інформації про банки 
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва банку")
    logo = models.ImageField(upload_to='bank_logos/', blank=True, null=True, verbose_name="Логотип")


    class Meta:
        verbose_name = "Банк"
        verbose_name_plural = "Банки"

    def __str__(self):
        return self.name

class Account(models.Model):
    ACCOUNT_TYPES=(('BANK','Банківський рахунок'), ('CARD','Банківська картка'), ('CASH','Готівка'),)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE, related_name= 'accounts')
    bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts', verbose_name="Банк")

    account_name = models.CharField(max_length=100, verbose_name="Назва рахунку")
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='CARD')
    last_four_digits = models.CharField(max_length=4, blank=True, verbose_name="Останні 4 цифри")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='UAH')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'account_name')
        verbose_name = "Рахунок"
        verbose_name_plural = "Рахунки"

    def __str__(self):
        return self.account_name

