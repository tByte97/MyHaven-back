from django.contrib import admin
from .models import Bank, Account

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'user', 'bank')
    list_filter = ('bank', 'user')
    search_fields = ('account_name', 'user__username')

admin.site.register(Bank)
admin.site.register(Account, AccountAdmin) 