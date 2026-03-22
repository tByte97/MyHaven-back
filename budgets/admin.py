from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'month', 'amount')
    list_filter = ('month', 'category')
    search_fields = ('user__username', 'category__name')
