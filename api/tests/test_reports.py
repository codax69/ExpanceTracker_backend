"""
Tests for Report API endpoints.
Covers: CSV generation, PDF generation, report history.
"""
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from api.models import Report
from .base import BaseAPITestCase


class ReportCSVTests(BaseAPITestCase):
    """POST /api/v1/reports/csv — CSV report generation."""

    def _get_date_range(self):
        """Helper: returns ISO date strings for last 30 days."""
        now = self.now
        start = (now - timedelta(days=30)).isoformat()
        end = now.isoformat()
        return start, end

    def test_generate_csv_report(self):
        """Should generate CSV file with correct headers."""
        start, end = self._get_date_range()
        response = self.client.post('/api/v1/reports/csv', {
            'startDate': start, 'endDate': end,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('expenses_report.csv', response['Content-Disposition'])

    def test_csv_contains_headers(self):
        """CSV should contain expected column headers."""
        start, end = self._get_date_range()
        response = self.client.post('/api/v1/reports/csv', {
            'startDate': start, 'endDate': end,
        }, format='json')
        content = response.content.decode('utf-8')
        first_line = content.split('\n')[0]
        self.assertIn('Title', first_line)
        self.assertIn('Amount', first_line)
        self.assertIn('Category', first_line)
        self.assertIn('Payment Method', first_line)
        self.assertIn('Date', first_line)

    def test_csv_contains_expense_data(self):
        """CSV should contain actual expense records."""
        start, end = self._get_date_range()
        response = self.client.post('/api/v1/reports/csv', {
            'startDate': start, 'endDate': end,
        }, format='json')
        content = response.content.decode('utf-8')
        self.assertIn('Grocery Shopping', content)
        self.assertIn('Netflix Subscription', content)

    def test_csv_creates_report_record(self):
        """Should save a Report record after CSV generation."""
        count_before = Report.objects.count()
        start, end = self._get_date_range()
        self.client.post('/api/v1/reports/csv', {
            'startDate': start, 'endDate': end,
        }, format='json')
        self.assertEqual(Report.objects.count(), count_before + 1)
        report = Report.objects.latest('created_at')
        self.assertEqual(report.format, 'csv')
        self.assertEqual(report.type, 'custom')

    def test_csv_missing_dates_returns_400(self):
        """Should return 400 when dates are missing."""
        response = self.client.post('/api/v1/reports/csv', {}, format='json')
        self.assert_error_response(response, 400)

    def test_csv_empty_date_range(self):
        """Should return valid CSV with just headers for empty date range."""
        response = self.client.post('/api/v1/reports/csv', {
            'startDate': '1990-01-01T00:00:00+00:00',
            'endDate': '1990-01-31T23:59:59+00:00',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        lines = [l for l in content.strip().split('\n') if l.strip()]
        self.assertEqual(len(lines), 1)  # Only header row


class ReportPDFTests(BaseAPITestCase):
    """POST /api/v1/reports/pdf — PDF report generation."""

    def _get_date_range(self):
        now = self.now
        return (now - timedelta(days=30)).isoformat(), now.isoformat()

    def test_generate_pdf_report(self):
        """Should generate PDF file."""
        start, end = self._get_date_range()
        response = self.client.post('/api/v1/reports/pdf', {
            'startDate': start, 'endDate': end,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('financial_report.pdf', response['Content-Disposition'])

    def test_pdf_is_valid_binary(self):
        """PDF content should start with %PDF magic bytes."""
        start, end = self._get_date_range()
        response = self.client.post('/api/v1/reports/pdf', {
            'startDate': start, 'endDate': end,
        }, format='json')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_creates_report_record(self):
        """Should save a Report record after PDF generation."""
        count_before = Report.objects.count()
        start, end = self._get_date_range()
        self.client.post('/api/v1/reports/pdf', {
            'startDate': start, 'endDate': end,
        }, format='json')
        self.assertEqual(Report.objects.count(), count_before + 1)
        report = Report.objects.latest('created_at')
        self.assertEqual(report.format, 'pdf')
        self.assertEqual(report.type, 'custom')

    def test_pdf_report_summary_values(self):
        """Report record should have correct summary totals."""
        start, end = self._get_date_range()
        self.client.post('/api/v1/reports/pdf', {
            'startDate': start, 'endDate': end,
        }, format='json')
        report = Report.objects.latest('created_at')
        self.assertGreaterEqual(float(report.total_expense), 0)
        self.assertGreaterEqual(float(report.total_income), 0)

    def test_pdf_missing_dates_returns_400(self):
        """Should return 400 when dates are missing."""
        response = self.client.post('/api/v1/reports/pdf', {}, format='json')
        self.assert_error_response(response, 400)


class ReportHistoryTests(BaseAPITestCase):
    """GET /api/v1/reports/history — paginated report history."""

    def setUp(self):
        super().setUp()
        # Create some report records
        now = timezone.now()
        for i in range(5):
            Report.objects.create(
                type='custom',
                start_date=now - timedelta(days=30),
                end_date=now,
                format='csv' if i % 2 == 0 else 'pdf',
                total_expense=Decimal('500.00'),
                total_income=Decimal('2000.00'),
                net_savings=Decimal('1500.00'),
            )

    def test_report_history_returns_paginated_list(self):
        """Should return paginated report history."""
        response = self.client.get('/api/v1/reports/history')
        data = self.assert_paginated_response(response, expected_total=5)
        self.assertEqual(len(data['data']), 5)

    def test_report_history_pagination(self):
        """Should paginate report history."""
        response = self.client.get('/api/v1/reports/history', {'page': 1, 'limit': 2})
        data = self.assert_paginated_response(response, expected_total=5)
        self.assertEqual(len(data['data']), 2)
        self.assertTrue(data['meta']['hasNextPage'])

    def test_report_history_response_format(self):
        """Should include reportRange, summary, and _id."""
        response = self.client.get('/api/v1/reports/history')
        data = self.assert_paginated_response(response)
        report = data['data'][0]
        self.assertIn('_id', report)
        self.assertIn('type', report)
        self.assertIn('format', report)
        self.assertIn('reportRange', report)
        self.assertIn('startDate', report['reportRange'])
        self.assertIn('endDate', report['reportRange'])
        self.assertIn('summary', report)
        self.assertIn('totalExpense', report['summary'])
        self.assertIn('totalIncome', report['summary'])
        self.assertIn('netSavings', report['summary'])

    def test_report_history_ordered_by_created_at_desc(self):
        """Reports should be ordered by creation date descending."""
        response = self.client.get('/api/v1/reports/history')
        data = self.assert_paginated_response(response)
        dates = [r['createdAt'] for r in data['data']]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_report_history_empty(self):
        """Should return empty list when no reports exist."""
        Report.objects.all().delete()
        response = self.client.get('/api/v1/reports/history')
        data = self.assert_paginated_response(response, expected_total=0)
        self.assertEqual(data['data'], [])
