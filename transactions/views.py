"""
Views для модуля транзакцій.
Тонкі views — лише HTTP-рівень. Бізнес-логіка в services.py, дані — в repositories.py.
"""
import logging
import json
from datetime import datetime, date
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status as http_status

from .models import Transaction, TransactionUpload, Category
from .forms import UploadStatementForm, ManualTransactionForm
from .serializers import (
    TransactionSerializer, TransactionWriteSerializer,
    CategorySerializer, UploadSerializer,
)
from .repositories import TransactionRepository
from .services import process_upload
from accounts.models import Bank

logger = logging.getLogger(__name__)


# ─── Helpers ────────────────────────────────────────────────────

class DecimalEncoder(json.JSONEncoder):
    """JSON-encoder для Decimal і datetime (використовується в template views)."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


# ═══════════════════════════════════════════════════════════════
#  REST API Views (для Vue.js frontend)
# ═══════════════════════════════════════════════════════════════

class DashboardStatsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = TransactionRepository(request.user)
        kpi = repo.get_dashboard_kpi()
        recent = repo.get_recent_transactions()
        top_cats = repo.get_top_expense_categories()

        return Response({
            **kpi,
            'recent_transactions': TransactionSerializer(recent, many=True).data,
            'expenses_by_category': list(top_cats),
        })


class StatisticsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = TransactionRepository(request.user)
        try:
            months = int(request.query_params.get('months', 6))
        except (ValueError, TypeError):
            months = 6

        return Response({
            'monthly_summary': list(repo.get_monthly_statistics(months)),
            'expense_categories': list(repo.get_category_stats(months, 'EXPENSE')),
            'income_categories': list(repo.get_category_stats(months, 'INCOME')),
            'by_bank_stats': list(repo.get_bank_stats(months)),
            'requested_months': months,
        })


class UpdateFilterAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            selected_ids = request.data.get('uploads', [])
            if not selected_ids:
                request.session.pop('filter_upload_ids', None)
            else:
                request.session['filter_upload_ids'] = selected_ids
            request.session.modified = True
            return Response({'status': 'ok', 'message': 'Filter updated'})
        except Exception as ex:
            logger.exception("Помилка оновлення фільтра")
            return Response({'status': 'err', 'message': str(ex)}, status=400)


# ─── Transaction CRUD API ───────────────────────────────────────

class TransactionListAPI(ListAPIView):
    """Список транзакцій з фільтрацією та пагінацією."""
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        params = self.request.query_params
        repo = TransactionRepository(self.request.user)
        return repo.get_filtered_transactions(
            category_id=params.get('category'),
            transaction_type=params.get('type'),
            date_from=params.get('date_from'),
            date_to=params.get('date_to'),
            search=params.get('search'),
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 30))

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = self.get_serializer(page_obj, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page,
        })


class TransactionCreateAPI(APIView):
    """Ручне додавання транзакції."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Знаходимо або створюємо акаунт "Ручний"
        from accounts.models import Account
        account, _ = Account.objects.get_or_create(
            user=request.user,
            account_name='Ручний',
            defaults={'account_type': 'CASH', 'currency': 'UAH'},
        )

        transaction = serializer.save(
            account=account,
            source='manual',
        )
        return Response(
            TransactionSerializer(transaction).data,
            status=http_status.HTTP_201_CREATED,
        )


class TransactionDetailAPI(RetrieveUpdateDestroyAPIView):
    """Перегляд / редагування / видалення транзакції."""
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(
            account__user=self.request.user,
        ).select_related('category')


# ─── Categories API ─────────────────────────────────────────────

class CategoryListAPI(APIView):
    """Список категорій (системні + користувацькі)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(
            Q(user=request.user) | Q(is_system=True)
        ).order_by('type', 'name')
        return Response(CategorySerializer(categories, many=True).data)


# ─── Calendar API ───────────────────────────────────────────────

class CalendarAPI(APIView):
    """Дані для календаря витрат: щоденні суми за місяць."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            year = int(request.query_params.get('year', date.today().year))
            month = int(request.query_params.get('month', date.today().month))
        except (ValueError, TypeError):
            year, month = date.today().year, date.today().month

        repo = TransactionRepository(request.user)
        daily_data = list(repo.get_calendar_data(year, month))

        # Серіалізуємо дати та Decimal
        result = []
        for item in daily_data:
            result.append({
                'day': item['day'].isoformat() if item['day'] else None,
                'expenses': float(abs(item['expenses'] or 0)),
                'incomes': float(item['incomes'] or 0),
            })

        return Response({
            'year': year,
            'month': month,
            'days': result,
        })


class CalendarDayAPI(APIView):
    """Транзакції за конкретний день для календаря."""
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month, day):
        repo = TransactionRepository(request.user)
        transactions = repo.get_calendar_day_transactions(year, month, day)
        return Response(TransactionSerializer(transactions, many=True).data)


# ─── Uploads / File Manager API ────────────────────────────────

class UploadListAPI(APIView):
    """Список завантажених виписок."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uploads = TransactionUpload.objects.filter(
            user=request.user,
        ).select_related('bank').order_by('-uploaded_at')
        serializer = UploadSerializer(uploads, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """Завантаження нової виписки."""
        serializer = UploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        upload = serializer.save(user=request.user)
        try:
            process_upload(upload)
        except Exception as e:
            logger.exception("Помилка обробки завантаження #%s", upload.id)
            upload.status = 'FAILED'
            upload.processing_log = str(e)
            upload.save()
        return Response(
            UploadSerializer(upload, context={'request': request}).data,
            status=http_status.HTTP_201_CREATED,
        )


class UploadDetailAPI(APIView):
    """Видалення завантаження."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        upload = get_object_or_404(TransactionUpload, id=pk, user=request.user)
        upload.file.delete()
        upload.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)


# ─── Banks API ──────────────────────────────────────────────────

class BankListAPI(APIView):
    """Список банків."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        banks = Bank.objects.all().values('id', 'name')
        return Response(list(banks))


# ═══════════════════════════════════════════════════════════════
#  Template Views (Django templates)
# ═══════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    """Головна сторінка з KPI, формою завантаження та останніми транзакціями."""

    # ── POST: завантаження виписки ──
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
                logger.exception("Помилка обробки завантаження #%s", upload.id)
                messages.error(request, f'Помилка обробки файлу: {e}')
        return redirect('transactions:dashboard')

    # ── GET: відображення даних ──
    selected_upload_ids = [
        int(uid) for uid in request.GET.getlist('uploads') if uid.isdigit()
    ]
    repo = TransactionRepository(request.user, upload_ids=selected_upload_ids)
    kpi = repo.get_dashboard_kpi()
    top_cats = list(repo.get_top_expense_categories())
    recent = repo.get_recent_transactions()

    context = {
        **kpi,
        'expenses_by_category': top_cats,
        'expenses_by_category_json': json.dumps(top_cats, cls=DecimalEncoder),
        'recent_transactions': recent,
        'upload_form': UploadStatementForm(user=request.user),
        'user_uploads': TransactionUpload.objects.filter(user=request.user).order_by('-uploaded_at'),
        'selected_upload_ids': selected_upload_ids,
    }
    return render(request, 'transactions/dashboard.html', context)


@login_required
def add_manual_transaction(request):
    """Додавання транзакції вручну."""
    if request.method == 'POST':
        form = ManualTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.source = 'manual'
            transaction.save()
    return redirect('transactions:dashboard')


@login_required
def transactions_list_view(request):
    """Список транзакцій з фільтрами та пагінацією."""
    transactions = Transaction.objects.filter(
        account__user=request.user
    ).select_related('category', 'account', 'account__bank')

    # ── Фільтри ──
    filters = {
        'category': request.GET.get('category'),
        'bank': request.GET.get('bank'),
        'date_from': request.GET.get('date_from'),
        'date_to': request.GET.get('date_to'),
        'type': request.GET.get('type'),
    }

    if filters['category']:
        transactions = transactions.filter(category_id=filters['category'])
    if filters['bank']:
        transactions = transactions.filter(account__bank_id=filters['bank'])
    if filters['date_from']:
        transactions = transactions.filter(transaction_date__gte=filters['date_from'])
    if filters['date_to']:
        transactions = transactions.filter(transaction_date__lte=filters['date_to'])
    if filters['type'] == 'income':
        transactions = transactions.filter(amount__gt=0)
    elif filters['type'] == 'expense':
        transactions = transactions.filter(amount__lt=0)

    # ── Пагінація ──
    paginator = Paginator(transactions, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'categories': Category.objects.filter(user=request.user),
        'banks': Bank.objects.filter(accounts__user=request.user).distinct(),
        'current_filters': request.GET,
        'page_obj': page_obj,
        'querystring': params.urlencode(),
    }
    return render(request, 'transactions/list.html', context)


@login_required
def statistics_view(request):
    """Сторінка статистики з графіками."""
    try:
        months = int(request.GET.get('months', 6))
    except (ValueError, TypeError):
        months = 6

    repo = TransactionRepository(request.user)
    monthly_stats = list(repo.get_monthly_statistics(months))
    expenses_by_category = list(repo.get_category_stats(months, 'EXPENSE'))
    by_bank = list(repo.get_bank_stats(months))

    context = {
        'monthly_stats_json': json.dumps(monthly_stats, cls=DecimalEncoder),
        'expenses_by_category_json': json.dumps(expenses_by_category, cls=DecimalEncoder),
        'by_bank_json': json.dumps(by_bank, cls=DecimalEncoder),
        'months': months,
        'monthly_stats': monthly_stats,
        'expenses_by_category': expenses_by_category,
        'by_bank': by_bank,
    }
    return render(request, 'transactions/statistics.html', context)


@login_required
def file_manager_view(request):
    uploads = TransactionUpload.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'transactions/file_manager.html', {'uploads': uploads})


@login_required
@require_POST
def delete_upload_view(request, upload_id):
    upload = get_object_or_404(TransactionUpload, id=upload_id, user=request.user)
    upload.file.delete()
    upload.delete()
    messages.success(request, 'Файл та транзакції успішно видалено.')
    return redirect('transactions:file_manager')


@login_required
def transaction_detail_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)
    return render(request, 'transactions/detail.html', {'transaction': transaction})


@login_required
def categories_view(request):
    categories = Category.objects.filter(
        Q(user=request.user) | Q(is_system=True)
    ).order_by('type', 'name')
    return render(request, 'transactions/categories.html', {'categories': categories})