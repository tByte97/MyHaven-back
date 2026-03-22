from django.db import models
from django.conf import settings
from transactions.models import Category


class Budget(models.Model):
    """Бюджет на місяць для певної категорії."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets',
        limit_choices_to={'type': 'EXPENSE'},
    )
    month = models.DateField(
        help_text="Перший день місяця, напр. 2026-03-01",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Ліміт бюджету",
    )

    class Meta:
        unique_together = ('user', 'category', 'month')
        ordering = ['-month', 'category__name']
        verbose_name = "Бюджет"
        verbose_name_plural = "Бюджети"

    def __str__(self):
        return f"{self.category.name} — {self.month:%Y-%m}: {self.amount}"
