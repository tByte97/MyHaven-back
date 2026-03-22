import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Budget
from .serializers import BudgetSerializer, BudgetCreateSerializer

logger = logging.getLogger(__name__)


class BudgetViewSet(viewsets.ModelViewSet):
    """CRUD для бюджетів поточного користувача."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Budget.objects.filter(user=self.request.user).select_related('category')
        month = self.request.query_params.get('month')
        if month:
            qs = qs.filter(month=month)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BudgetCreateSerializer
        return BudgetSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = BudgetSerializer(queryset, many=True)
        return Response(serializer.data)
