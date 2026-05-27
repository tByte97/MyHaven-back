import logging
import os
from datetime import date

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account, Bank
from budgets.models import Budget
from budgets.serializers import BudgetCreateSerializer, BudgetSerializer
from transactions.models import Category, Transaction
from transactions.repositories import TransactionRepository
from transactions.serializers import (
    CategorySerializer,
    TransactionSerializer,
    TransactionWriteSerializer,
    UploadSerializer,
)
from transactions.services import process_upload

logger = logging.getLogger(__name__)


class IsActiveTelegramLink(BasePermission):
    message = 'Telegram profile is not linked.'

    def has_permission(self, request, view):
        telegram_user_id = request.headers.get('X-Telegram-User-Id')
        if not telegram_user_id:
            return False
        try:
            telegram_user_id = int(telegram_user_id)
        except (TypeError, ValueError):
            return False
        return request.user.is_authenticated and request.user.telegram_user_id == telegram_user_id


def _get_or_create_telegram_account(user):
    account, _ = Account.objects.get_or_create(
        user=user,
        account_name='Telegram',
        defaults={'account_type': 'CASH', 'currency': user.currency},
    )
    return account


class TelegramHealthAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request):
        return Response({
            'status': 'ok',
            'telegram_user_id': request.user.telegram_user_id,
            'capabilities': [
                'dashboard', 'statistics', 'categories',
                'transactions', 'budgets', 'calendar',
            ],
        })


class TelegramDashboardAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

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


class TelegramStatisticsAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

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


class TelegramTransactionListAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request):
        params = request.query_params
        repo = TransactionRepository(request.user)
        queryset = repo.get_filtered_transactions(
            category_id=params.get('category'),
            transaction_type=params.get('type'),
            date_from=params.get('date_from'),
            date_to=params.get('date_to'),
            search=params.get('search'),
        )

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 30))
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = TransactionSerializer(page_obj, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page,
        })

    def post(self, request):
        serializer = TransactionWriteSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        account = _get_or_create_telegram_account(request.user)
        transaction = serializer.save(
            account=account,
            source='telegram',
        )

        return Response(
            TransactionSerializer(transaction).data,
            status=status.HTTP_201_CREATED,
        )


class TelegramUploadStatementAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload_file = request.FILES.get('file')
        if not upload_file:
            return Response(
                {'detail': 'file is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = os.path.splitext(upload_file.name)[1].lower()
        allowed_exts = {'.pdf', '.xls', '.xlsx', '.csv'}
        if ext not in allowed_exts:
            return Response(
                {'detail': 'Unsupported file type. Use PDF/CSV or Excel (.xls, .xlsx).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = request.data.copy()
        payload['file'] = upload_file
        if not payload.get('bank') and payload.get('bank_name'):
            bank = Bank.objects.filter(name__iexact=payload.get('bank_name')).first()
            if bank:
                payload['bank'] = bank.id

        if not payload.get('bank'):
            return Response(
                {'detail': 'bank or bank_name is required for PDF/XLSX uploads.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UploadSerializer(data=payload, context={'request': request})
        serializer.is_valid(raise_exception=True)
        upload = serializer.save(user=request.user)

        try:
            process_upload(upload)
        except Exception as e:
            logger.exception("Помилка обробки завантаження #%s", upload.id)
            upload.status = 'FAILED'
            upload.processing_log = str(e)
            upload.save(update_fields=['status', 'processing_log'])

        return Response(
            UploadSerializer(upload, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class TelegramTransactionDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request, pk):
        transaction = get_object_or_404(
            Transaction, id=pk, account__user=request.user
        )
        return Response(TransactionSerializer(transaction).data)

    def patch(self, request, pk):
        transaction = get_object_or_404(
            Transaction, id=pk, account__user=request.user
        )
        serializer = TransactionWriteSerializer(
            transaction,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TransactionSerializer(transaction).data)

    def delete(self, request, pk):
        transaction = get_object_or_404(
            Transaction, id=pk, account__user=request.user
        )
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TelegramCategoryListAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request):
        categories = Category.objects.filter(user=request.user)
        system_categories = Category.objects.filter(is_system=True)
        combined = (categories | system_categories).order_by('type', 'name')
        return Response(CategorySerializer(combined, many=True).data)


class TelegramBudgetListAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request):
        queryset = Budget.objects.filter(user=request.user).select_related('category')
        month = request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        return Response(BudgetSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = BudgetCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        budget = serializer.save(user=request.user)
        return Response(BudgetSerializer(budget).data, status=status.HTTP_201_CREATED)


class TelegramBudgetDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request, pk):
        budget = get_object_or_404(Budget, id=pk, user=request.user)
        return Response(BudgetSerializer(budget).data)

    def patch(self, request, pk):
        budget = get_object_or_404(Budget, id=pk, user=request.user)
        serializer = BudgetCreateSerializer(
            budget,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BudgetSerializer(budget).data)

    def delete(self, request, pk):
        budget = get_object_or_404(Budget, id=pk, user=request.user)
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TelegramCalendarAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request):
        try:
            year = int(request.query_params.get('year', date.today().year))
            month = int(request.query_params.get('month', date.today().month))
        except (ValueError, TypeError):
            year, month = date.today().year, date.today().month

        repo = TransactionRepository(request.user)
        daily_data = list(repo.get_calendar_data(year, month))

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


class TelegramCalendarDayAPI(APIView):
    permission_classes = [IsAuthenticated, IsActiveTelegramLink]

    def get(self, request, year, month, day):
        repo = TransactionRepository(request.user)
        transactions = repo.get_calendar_day_transactions(year, month, day)
        return Response(TransactionSerializer(transactions, many=True).data)
