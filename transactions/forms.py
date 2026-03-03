from django import forms
from .models import Transaction, TransactionUpload
from accounts.models import Bank


class UploadStatementForm(forms.ModelForm):
    class Meta:
        model = TransactionUpload
        fields = ('bank', 'file')
        labels = {
            'bank': 'Оберіть банк',
            'file': 'Файл виписки (.csv, .xls, .xlsx)',
        }
        widgets = {
            'bank': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'required': True,
                'accept': '.csv,.xls,.xlsx,.pdf',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['bank'].queryset = Bank.objects.all()
        self.fields['bank'].empty_label = "--- Оберіть банк ---"
        self.fields['bank'].required = True


class ManualTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_date', 'description', 'category']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Сума'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'На що витратили?'}),
        }