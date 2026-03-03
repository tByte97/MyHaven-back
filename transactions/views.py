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
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Transaction, TransactionUpload, Category
from .forms import UploadStatementForm, ManualTransactionForm
from .serializers import TransactionSerializer
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
            transaction.user = request.user
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