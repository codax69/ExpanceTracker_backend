"""
Views for ExpenseIQ API — Income endpoints.
Mirrors: /api/v1/income/*
"""
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone
from datetime import timedelta

from ..models import Income
from ..serializers import IncomeSerializer
from ..utils import ApiResponse


class IncomeListCreateView(APIView):
    """GET /api/v1/income/ — list with filters & pagination
       POST /api/v1/income/ — create new income"""

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        sort_by = request.query_params.get('sortBy', 'income_date')
        sort_order = request.query_params.get('sortOrder', 'desc')
        source = request.query_params.get('source')
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')

        # Map camelCase sort fields
        sort_field_map = {
            'incomeDate': 'income_date',
            'amount': 'amount',
            'source': 'source',
        }
        sort_field = sort_field_map.get(sort_by, sort_by)
        if sort_field not in ['income_date', 'amount', 'source']:
            sort_field = 'income_date'

        queryset = Income.objects.filter(user=request.user)

        if source:
            queryset = queryset.filter(source=source)
        if start_date:
            queryset = queryset.filter(income_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(income_date__lte=end_date)

        ordering = f"{'-' if sort_order == 'desc' else ''}{sort_field}"
        queryset = queryset.order_by(ordering)

        total = queryset.count()
        offset = (page - 1) * limit
        incomes = queryset[offset:offset + limit]

        serializer = IncomeSerializer(incomes, many=True)
        return ApiResponse.paginated(serializer.data, page, limit, total)

    def post(self, request):
        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            income = serializer.save(user=request.user)
            return ApiResponse.created(
                IncomeSerializer(income).data,
                message='Income added successfully'
            )
        return ApiResponse.error('Validation failed', 400, serializer.errors)


class IncomeDetailView(APIView):
    """GET/PUT/DELETE /api/v1/income/<id>/"""

    def _get_income(self, pk):
        try:
            return Income.objects.get(pk=pk, user=self.request.user)
        except Income.DoesNotExist:
            return None

    def get(self, request, pk):
        income = self._get_income(pk)
        if not income:
            return ApiResponse.error('Income not found', 404)
        return ApiResponse.success(IncomeSerializer(income).data)

    def put(self, request, pk):
        income = self._get_income(pk)
        if not income:
            return ApiResponse.error('Income not found', 404)
        serializer = IncomeSerializer(income, data=request.data, partial=True)
        if serializer.is_valid():
            income = serializer.save()
            return ApiResponse.success(
                IncomeSerializer(income).data,
                message='Income updated successfully'
            )
        return ApiResponse.error('Validation failed', 400, serializer.errors)

    def delete(self, request, pk):
        income = self._get_income(pk)
        if not income:
            return ApiResponse.error('Income not found', 404)
        income.delete()
        return ApiResponse.success(message='Income deleted successfully')


class IncomeMonthlySummaryView(APIView):
    """GET /api/v1/income/monthly-summary"""

    def get(self, request):
        now = timezone.now()
        start_date = now - timedelta(days=365)  # Last 12 months

        data = (
            Income.objects
            .filter(user=request.user, income_date__gte=start_date)
            .annotate(
                month=ExtractMonth('income_date'),
                year=ExtractYear('income_date'),
            )
            .values('month', 'year')
            .annotate(
                total=Sum('amount'),
                count=Count('id'),
            )
            .order_by('year', 'month')
        )

        result = [
            {
                '_id': {'year': item['year'], 'month': item['month']},
                'total': float(item['total'] or 0),
                'count': item['count'],
            }
            for item in data
        ]
        return ApiResponse.success(result)
