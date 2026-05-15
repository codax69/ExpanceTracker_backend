"""
Tests for Income API endpoints.
Covers: CRUD, pagination, filtering, sorting, monthly summary.
"""
from decimal import Decimal
from datetime import timedelta

from django.db import models
from django.utils import timezone

from api.models import Income
from .base import BaseAPITestCase


class IncomeListTests(BaseAPITestCase):
    """GET /api/v1/income/ — listing, pagination, filtering."""

    def test_list_income_returns_paginated_response(self):
        """Should return paginated income list."""
        response = self.client.get('/api/v1/income/')
        data = self.assert_paginated_response(response, expected_total=2)
        self.assertEqual(len(data['data']), 2)

    def test_list_income_pagination(self):
        """Should paginate correctly."""
        response = self.client.get('/api/v1/income/', {'page': 1, 'limit': 1})
        data = self.assert_paginated_response(response, expected_total=2)
        self.assertEqual(len(data['data']), 1)
        self.assertTrue(data['meta']['hasNextPage'])

    def test_list_income_filter_by_source(self):
        """Should filter income by source."""
        response = self.client.get('/api/v1/income/', {'source': 'Salary'})
        data = self.assert_paginated_response(response, expected_total=1)
        self.assertEqual(data['data'][0]['source'], 'Salary')

    def test_list_income_filter_by_date_range(self):
        """Should filter income by date range."""
        start = (self.now - timedelta(days=6)).strftime('%Y-%m-%d')
        end = self.now.strftime('%Y-%m-%d')
        response = self.client.get('/api/v1/income/', {'startDate': start, 'endDate': end})
        data = self.assert_paginated_response(response)
        self.assertGreaterEqual(len(data['data']), 1)

    def test_list_income_sort_by_amount_asc(self):
        """Should sort income by amount ascending."""
        response = self.client.get('/api/v1/income/', {'sortBy': 'amount', 'sortOrder': 'asc'})
        data = self.assert_paginated_response(response)
        amounts = [item['amount'] for item in data['data']]
        self.assertEqual(amounts, sorted(amounts))

    def test_list_income_sort_by_amount_desc(self):
        """Should sort income by amount descending."""
        response = self.client.get('/api/v1/income/', {'sortBy': 'amount', 'sortOrder': 'desc'})
        data = self.assert_paginated_response(response)
        amounts = [item['amount'] for item in data['data']]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_list_income_response_format(self):
        """Should include _id alias and camelCase fields."""
        response = self.client.get('/api/v1/income/')
        data = self.assert_paginated_response(response)
        income = data['data'][0]
        self.assertIn('_id', income)
        self.assertIn('incomeDate', income)
        self.assertIn('paymentSource', income)
        self.assertIn('createdAt', income)
        self.assertEqual(income['_id'], str(income['id']))


class IncomeCreateTests(BaseAPITestCase):
    """POST /api/v1/income/ — creating income records."""

    def test_create_income_success(self):
        """Should create income and return 201."""
        payload = {
            'source': 'Dividends',
            'amount': '340.00',
            'paymentSource': 'Brokerage',
            'incomeDate': self.now.isoformat(),
            'description': 'Q1 dividends',
        }
        response = self.client.post('/api/v1/income/', payload, format='json')
        data = self.assert_success_response(response, 201)
        self.assertEqual(data['message'], 'Income added successfully')
        self.assertEqual(data['data']['source'], 'Dividends')
        self.assertEqual(data['data']['amount'], 340.00)
        self.assertEqual(Income.objects.count(), 3)

    def test_create_income_missing_required_fields(self):
        """Should return 400 for missing required fields."""
        payload = {'source': 'Incomplete'}
        response = self.client.post('/api/v1/income/', payload, format='json')
        self.assert_error_response(response, 400)

    def test_create_income_with_default_payment_source(self):
        """Should default paymentSource to Bank Transfer."""
        payload = {
            'source': 'Side Gig',
            'amount': '100.00',
            'incomeDate': self.now.isoformat(),
        }
        response = self.client.post('/api/v1/income/', payload, format='json')
        data = self.assert_success_response(response, 201)
        self.assertEqual(data['data']['paymentSource'], 'Bank Transfer')


class IncomeDetailTests(BaseAPITestCase):
    """GET/PUT/DELETE /api/v1/income/<id>/"""

    def test_get_income_by_id(self):
        """Should return income details by ID."""
        response = self.client.get(f'/api/v1/income/{self.income1.id}/')
        data = self.assert_success_response(response)
        self.assertEqual(data['data']['source'], 'Salary')
        self.assertEqual(data['data']['amount'], 5200.00)

    def test_get_income_not_found(self):
        """Should return 404 for non-existent income."""
        response = self.client.get('/api/v1/income/99999/')
        self.assert_error_response(response, 404)

    def test_update_income(self):
        """Should update income fields."""
        payload = {'source': 'Updated Salary', 'amount': '5500.00'}
        response = self.client.put(
            f'/api/v1/income/{self.income1.id}/', payload, format='json'
        )
        data = self.assert_success_response(response)
        self.assertEqual(data['data']['source'], 'Updated Salary')
        self.assertEqual(data['data']['amount'], 5500.00)
        self.assertEqual(data['message'], 'Income updated successfully')

    def test_update_income_partial(self):
        """Should partially update income."""
        payload = {'amount': '6000.00'}
        response = self.client.put(
            f'/api/v1/income/{self.income1.id}/', payload, format='json'
        )
        data = self.assert_success_response(response)
        self.assertEqual(data['data']['amount'], 6000.00)
        self.assertEqual(data['data']['source'], 'Salary')  # unchanged

    def test_update_income_not_found(self):
        """Should return 404 for updating non-existent income."""
        response = self.client.put('/api/v1/income/99999/', {'source': 'X'}, format='json')
        self.assert_error_response(response, 404)

    def test_delete_income(self):
        """Should delete income and return success."""
        count_before = Income.objects.count()
        response = self.client.delete(f'/api/v1/income/{self.income1.id}/')
        data = self.assert_success_response(response)
        self.assertEqual(data['message'], 'Income deleted successfully')
        self.assertEqual(Income.objects.count(), count_before - 1)

    def test_delete_income_not_found(self):
        """Should return 404 for deleting non-existent income."""
        response = self.client.delete('/api/v1/income/99999/')
        self.assert_error_response(response, 404)


class IncomeMonthlySummaryTests(BaseAPITestCase):
    """GET /api/v1/income/monthly-summary"""

    def test_monthly_summary_returns_aggregated_data(self):
        """Should return monthly income aggregation."""
        response = self.client.get('/api/v1/income/monthly-summary')
        data = self.assert_success_response(response)
        self.assertIsInstance(data['data'], list)
        self.assertGreaterEqual(len(data['data']), 1)

    def test_monthly_summary_format(self):
        """Each item should have _id (year/month), total, count."""
        response = self.client.get('/api/v1/income/monthly-summary')
        data = self.assert_success_response(response)
        for item in data['data']:
            self.assertIn('_id', item)
            self.assertIn('year', item['_id'])
            self.assertIn('month', item['_id'])
            self.assertIn('total', item)
            self.assertIn('count', item)
            self.assertIsInstance(item['total'], float)

    def test_monthly_summary_totals_are_correct(self):
        """Total for current month should match sum of income records."""
        response = self.client.get('/api/v1/income/monthly-summary')
        data = self.assert_success_response(response)
        now = timezone.now()
        current_month_items = [
            item for item in data['data']
            if item['_id']['month'] == now.month and item['_id']['year'] == now.year
        ]
        if current_month_items:
            expected_total = float(
                Income.objects.filter(
                    income_date__month=now.month,
                    income_date__year=now.year,
                ).aggregate(total=models.Sum('amount'))['total'] or 0
            )
            # Use assertAlmostEqual for floating point
            self.assertAlmostEqual(current_month_items[0]['total'], expected_total, places=0)
