"""
Shared test fixtures and helpers for ExpenseIQ API tests.
"""
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from api.models import Category, Expense, Income, Budget, Report


class BaseAPITestCase(APITestCase):
    """
    Base test case with shared setUp fixtures.
    All test classes inherit from this to get pre-populated test data.
    """

    def setUp(self):
        self.client = APIClient()
        self.now = timezone.now()

        # ── Categories ──
        self.cat_food = Category.objects.create(
            name='Food', icon='🍔', color='#10b981', monthly_budget=Decimal('500.00')
        )
        self.cat_transport = Category.objects.create(
            name='Transport', icon='🚗', color='#06b6d4', monthly_budget=Decimal('200.00')
        )
        self.cat_entertainment = Category.objects.create(
            name='Entertainment', icon='🎬', color='#8b5cf6', monthly_budget=Decimal('150.00')
        )

        # ── Expenses ──
        self.expense1 = Expense.objects.create(
            title='Grocery Shopping',
            amount=Decimal('142.50'),
            category='Food',
            payment_method='Credit Card',
            description='Weekly groceries',
            notes='From supermarket',
            expense_date=self.now - timedelta(days=1),
            is_recurring=False,
            tags=['groceries', 'weekly'],
        )
        self.expense2 = Expense.objects.create(
            title='Netflix Subscription',
            amount=Decimal('15.99'),
            category='Entertainment',
            payment_method='Debit Card',
            description='Monthly subscription',
            expense_date=self.now - timedelta(days=2),
            is_recurring=True,
            recurring_type='monthly',
        )
        self.expense3 = Expense.objects.create(
            title='Uber Rides',
            amount=Decimal('37.00'),
            category='Transport',
            payment_method='UPI',
            expense_date=self.now - timedelta(days=3),
        )
        # An old expense for analytics
        self.expense_old = Expense.objects.create(
            title='Old Restaurant Bill',
            amount=Decimal('85.00'),
            category='Food',
            payment_method='Cash',
            expense_date=self.now - timedelta(days=45),
        )

        # ── Income ──
        self.income1 = Income.objects.create(
            source='Salary',
            amount=Decimal('5200.00'),
            payment_source='Bank Transfer',
            income_date=self.now.replace(day=1),
            description='Monthly salary',
        )
        self.income2 = Income.objects.create(
            source='Freelance',
            amount=Decimal('1200.00'),
            payment_source='PayPal',
            income_date=self.now - timedelta(days=5),
            description='Web design project',
        )

        # ── Budget ──
        self.budget = Budget.objects.create(
            month=self.now.month,
            year=self.now.year,
            total_monthly_budget=Decimal('2500.00'),
            warning_threshold=80,
        )

    # ── Assertion Helpers ──
    def assert_success_response(self, response, status_code=200):
        """Assert standard success response shape."""
        self.assertEqual(response.status_code, status_code)
        data = response.json()
        self.assertTrue(data['success'])
        return data

    def assert_error_response(self, response, status_code):
        """Assert standard error response shape."""
        self.assertEqual(response.status_code, status_code)
        data = response.json()
        self.assertFalse(data['success'])
        return data

    def assert_paginated_response(self, response, expected_total=None):
        """Assert paginated response with meta info."""
        data = self.assert_success_response(response)
        self.assertIn('meta', data)
        meta = data['meta']
        self.assertIn('page', meta)
        self.assertIn('limit', meta)
        self.assertIn('total', meta)
        self.assertIn('totalPages', meta)
        self.assertIn('hasNextPage', meta)
        self.assertIn('hasPrevPage', meta)
        if expected_total is not None:
            self.assertEqual(meta['total'], expected_total)
        return data
