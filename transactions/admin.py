from django.contrib import admin
from .models import Transaction, Category, TransactionUpload

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'description', 'amount', 'category', 'get_user')
    list_filter = ('account__bank', 'category', 'account__user')
    search_fields = ('description', 'account__user__username')

    @admin.display(description='User')
    def get_user(self, obj):
        return obj.account.user

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Category)
admin.site.register(TransactionUpload)