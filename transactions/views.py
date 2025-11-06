# transactions/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator


from datetime import timedelta, datetime, date
from django.utils import timezone
from decimal import Decimal
import os
import json

from .models import Transaction, TransactionUpload, Category
from .forms import UploadStatementForm
from .parsers import PrivatBankExcelParser, MonobankExcelParser, UniversalCSVParser, PDFStatementParser
from .categorization import CategoryMatcher, create_default_categories
from accounts.models import Account, Bank

class DecimalEncoder(json.JSONEncoder):    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)


@login_required
def dashboard_view(request):

    
    #POST запит 
    if request.method == 'POST':
        form = UploadStatementForm(request.POST, request.FILES, user=request.user) 
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            upload.save()
            
            try:
                process_upload(upload)
                messages.success(request, 'Виписку успішно завантажено та оброблено!')
            except Exception as e:
                upload.status = 'FAILED'
                upload.processing_log = str(e)
                upload.save()
                messages.error(request, f'Помилка обробки файлу: {str(e)}')
            

            return redirect('transactions:dashboard')
    
    #GET запит
    
    all_transactions = Transaction.objects.filter(account__user=request.user)
    has_transactions = all_transactions.exists()
    upload_form = UploadStatementForm(user=request.user)

    if has_transactions:
        month_ago = timezone.now() - timedelta(days=30)
        transactions_last_month = all_transactions.filter(
            transaction_date__gte=month_ago
        )

        expenses = transactions_last_month.filter(amount__lt=0).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        incomes = transactions_last_month.filter(amount__gt=0).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        expenses_by_category_qs = transactions_last_month.filter(
            amount__lt=0, category__isnull=False
        ).values('category__name').annotate(total=Sum('amount')).order_by('total')[:5]
        
        expenses_by_category_list = list(expenses_by_category_qs)
        expenses_by_category_json = json.dumps(expenses_by_category_list, cls=DecimalEncoder)
        
        recent_transactions = all_transactions.order_by('-transaction_date')[:10]
        
    else:
        expenses = Decimal('0')
        incomes = Decimal('0')
        expenses_by_category_list = [] 
        expenses_by_category_json = "[]"
        recent_transactions = []    

    context = {
        'total_expenses': abs(expenses),
        'total_incomes': incomes,
        'balance': incomes + expenses,
        'expenses_by_category': expenses_by_category_list,
        'expenses_by_category_json': expenses_by_category_json, 
        'recent_transactions': recent_transactions,
        'upload_form': upload_form,
        'has_transactions': has_transactions,
    }
    
    return render(request, 'transactions/dashboard.html', context)

def process_upload(upload):
    """
    ОНОВЛЕНА Обробка завантаженого файлу
    """
    
    upload.status = 'PROCESSING'
    upload.save()
    
    try:

        BANK_PARSERS = {
            'ПриватБанк': PrivatBankExcelParser,
            'Monobank': MonobankExcelParser,
        }


        bank_name = upload.bank.name
        
        if bank_name in BANK_PARSERS:
            parser_class = BANK_PARSERS[bank_name]
            parser = parser_class()
        else:

            parser = UniversalCSVParser()

        transactions_data = parser.parse(upload.file.path)
        upload.total_transactions = len(transactions_data)
        upload.save()
        
        account = get_or_create_account(upload.user, upload.bank)
        matcher = CategoryMatcher(upload.user)
        created_count = 0
        
        for trans_data in transactions_data:
            
            #Перевірка дубліків
            existing = Transaction.objects.filter(
                account=account,
                transaction_date=trans_data['date'],
                amount=trans_data['amount'],
                description=trans_data['description']
            ).first()
            
            if existing:
                continue 
            #Якщо дубліката немає продовжуємо обробку
            category, confidence = matcher.match(
                trans_data['description'],
                trans_data.get('bank_category', ''),
                float(trans_data['amount'])
            )
            
            Transaction.objects.create(
                account=account,
                category=category,
                amount=trans_data['amount'],
                description=trans_data['description'],
                transaction_date=trans_data['date'],
                raw_description=trans_data.get('description', ''), 
                bank_category=trans_data.get('bank_category', ''),
                matched_automatically=category is not None,
                confidence_score=confidence
            )

            created_count += 1
            upload.processed_transactions = created_count
            upload.save()
        
        upload.status = 'COMPLETED'
        upload.processing_log = f'Успішно оброблено {created_count} транзакцій'
        upload.save()
            
    except Exception as e:
        upload.status = 'FAILED'
        upload.processing_log = str(e)
        upload.save()
        raise


def get_or_create_account(user, bank):
    
    account = Account.objects.filter(user=user, bank=bank).first()
    
    if not account:
        bank_name = bank.name if bank else 'Основний рахунок'
        account = Account.objects.create(
            user=user,
            bank=bank,
            account_name=bank_name,
            account_type='BANK'
        )
    
    return account


@login_required
def transactions_list_view(request):
    """Список всіх транзакцій з фільтрами"""
    
    transactions = Transaction.objects.filter(
        account__user=request.user
    ).select_related('category', 'account', 'account__bank')
    
    # Фільтри
    category_id = request.GET.get('category')
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    
    bank_id = request.GET.get('bank')
    if bank_id:
        transactions = transactions.filter(account__bank_id=bank_id)
    
    date_from = request.GET.get('date_from')
    if date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)
    
    trans_type = request.GET.get('type')
    if trans_type == 'income':
        transactions = transactions.filter(amount__gt=0)
    elif trans_type == 'expense':
        transactions = transactions.filter(amount__lt=0)
    
    # Пагінація
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Дані для фільтрів
    categories = Category.objects.filter(user=request.user)
    banks = Bank.objects.filter(accounts__user=request.user).distinct()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'banks': banks,
        'current_filters': request.GET,
    }
    
    return render(request, 'transactions/list.html', context)


@login_required
def statistics_view(request):
    print("---STATISTICS VIEW DEBUG---")
    
    months = int(request.GET.get('months', 6))
    date_from = timezone.now() - timedelta(days=months*30)
    
    print(f"User: {request.user}")
    print(f"Months: {months}")
    print(f"Date from: {date_from}")
    
    # Перевірка чи є транзакції 
    total_transactions = Transaction.objects.filter(
        account__user=request.user
    ).count()
    print(f"Total transactions for user: {total_transactions}")
    
    transactions = Transaction.objects.filter(
        account__user=request.user,
        transaction_date__gte=date_from
    )
    
    print(f"Transactions in period: {transactions.count()}")
    
    # Статистика по місяцях
    monthly_stats_qs = transactions.annotate(
        month=TruncMonth('transaction_date')
    ).values('month').annotate(
        expenses=Sum('amount', filter=Q(amount__lt=0)),
        incomes=Sum('amount', filter=Q(amount__gt=0))
    ).order_by('month')
    
    monthly_stats = list(monthly_stats_qs)
    print(f"Monthly stats: {monthly_stats}")
    
    # Витрати по категоріях
    expenses_by_category_qs = transactions.filter(
        amount__lt=0,
        category__isnull=False
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('total')
    
    expenses_by_category = list(expenses_by_category_qs)
    print(f"Expenses by category: {expenses_by_category}")
    
    # Статистика по банкам
    by_bank_qs = transactions.values(
        'account__bank__name'
    ).annotate(
        expenses=Sum('amount', filter=Q(amount__lt=0)),
        incomes=Sum('amount', filter=Q(amount__gt=0))
    )
    
    by_bank = list(by_bank_qs)
    print(f"By bank: {by_bank}")
    
    # Серіалізація в JSON
    try:
        monthly_stats_json = json.dumps(monthly_stats, cls=DecimalEncoder)
        expenses_by_category_json = json.dumps(expenses_by_category, cls=DecimalEncoder)
        by_bank_json = json.dumps(by_bank, cls=DecimalEncoder)
        
        print("JSON serialization successful")
        print(f"Monthly JSON: {monthly_stats_json[:100]}...")
        
    except Exception as e:
        print(f"JSON serialization error: {e}")
        monthly_stats_json = '[]'
        expenses_by_category_json = '[]'
        by_bank_json = '[]'
    
    context = {
        'monthly_stats_json': monthly_stats_json,
        'expenses_by_category_json': expenses_by_category_json,
        'by_bank_json': by_bank_json,
        'months': months,
        
        'monthly_stats': monthly_stats,
        'expenses_by_category': expenses_by_category,
        'by_bank': by_bank,
    }
    
    print("--- END DEBUG ---\n")
    
    return render(request, 'transactions/statistics.html', context)


@login_required
def transaction_detail_view(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        account__user=request.user
    )
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'transactions/detail.html', context)


@login_required
def categories_view(request):
    categories = Category.objects.filter(
        Q(user=request.user) | Q(is_system=True)
    ).order_by('type', 'name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'transactions/categories.html', context)