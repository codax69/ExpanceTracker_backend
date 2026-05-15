"""
Tests for Category API endpoints.
Covers: CRUD, duplicate prevention, validation.
"""
from decimal import Decimal

from api.models import Category
from .base import BaseAPITestCase


class CategoryListTests(BaseAPITestCase):
    """GET /api/v1/categories — listing categories."""

    def test_list_categories(self):
        """Should return all categories."""
        response = self.client.get('/api/v1/categories')
        data = self.assert_success_response(response)
        self.assertEqual(len(data['data']), 3)

    def test_list_categories_ordered_by_name(self):
        """Should return categories sorted by name."""
        response = self.client.get('/api/v1/categories')
        data = self.assert_success_response(response)
        names = [c['name'] for c in data['data']]
        self.assertEqual(names, sorted(names))

    def test_list_categories_response_format(self):
        """Should include all expected fields."""
        response = self.client.get('/api/v1/categories')
        data = self.assert_success_response(response)
        cat = data['data'][0]
        self.assertIn('id', cat)
        self.assertIn('name', cat)
        self.assertIn('icon', cat)
        self.assertIn('color', cat)
        self.assertIn('monthlyBudget', cat)
        self.assertIn('createdAt', cat)
        self.assertIsInstance(cat['monthlyBudget'], float)

    def test_list_categories_empty(self):
        """Should return empty list when no categories exist."""
        Category.objects.all().delete()
        response = self.client.get('/api/v1/categories')
        data = self.assert_success_response(response)
        self.assertEqual(data['data'], [])


class CategoryCreateTests(BaseAPITestCase):
    """POST /api/v1/categories — creating categories."""

    def test_create_category_success(self):
        """Should create category and return 201."""
        payload = {
            'name': 'Health',
            'icon': '💪',
            'color': '#ef4444',
            'monthlyBudget': '100.00',
        }
        response = self.client.post('/api/v1/categories', payload, format='json')
        data = self.assert_success_response(response, 201)
        self.assertEqual(data['message'], 'Category created')
        self.assertEqual(data['data']['name'], 'Health')
        self.assertEqual(data['data']['icon'], '💪')
        self.assertEqual(data['data']['monthlyBudget'], 100.00)

    def test_create_category_with_defaults(self):
        """Should use default icon and color when not provided."""
        payload = {'name': 'Misc'}
        response = self.client.post('/api/v1/categories', payload, format='json')
        data = self.assert_success_response(response, 201)
        self.assertEqual(data['data']['icon'], '📦')
        self.assertEqual(data['data']['color'], '#10b981')
        self.assertEqual(data['data']['monthlyBudget'], 0.0)

    def test_create_category_duplicate_returns_409(self):
        """Should return 409 for duplicate category name."""
        payload = {'name': 'Food'}
        response = self.client.post('/api/v1/categories', payload, format='json')
        self.assert_error_response(response, 409)

    def test_create_category_duplicate_case_insensitive(self):
        """Should reject duplicate category names regardless of case."""
        payload = {'name': 'FOOD'}
        response = self.client.post('/api/v1/categories', payload, format='json')
        self.assert_error_response(response, 409)

    def test_create_category_missing_name(self):
        """Should return 400 when name is missing."""
        payload = {'icon': '🏠'}
        response = self.client.post('/api/v1/categories', payload, format='json')
        self.assert_error_response(response, 400)


class CategoryUpdateTests(BaseAPITestCase):
    """PUT /api/v1/categories/<id> — updating categories."""

    def test_update_category_success(self):
        """Should update category fields."""
        payload = {'name': 'Fast Food', 'icon': '🍟', 'color': '#ff6600'}
        response = self.client.put(
            f'/api/v1/categories/{self.cat_food.id}', payload, format='json'
        )
        data = self.assert_success_response(response)
        self.assertEqual(data['message'], 'Category updated')
        self.assertEqual(data['data']['name'], 'Fast Food')
        self.assertEqual(data['data']['icon'], '🍟')

    def test_update_category_partial(self):
        """Should partially update category."""
        payload = {'monthlyBudget': '600.00'}
        response = self.client.put(
            f'/api/v1/categories/{self.cat_food.id}', payload, format='json'
        )
        data = self.assert_success_response(response)
        self.assertEqual(data['data']['monthlyBudget'], 600.00)
        self.assertEqual(data['data']['name'], 'Food')  # unchanged

    def test_update_category_not_found(self):
        """Should return 404 for non-existent category."""
        response = self.client.put(
            '/api/v1/categories/99999', {'name': 'X'}, format='json'
        )
        self.assert_error_response(response, 404)


class CategoryDeleteTests(BaseAPITestCase):
    """DELETE /api/v1/categories/<id>"""

    def test_delete_category_success(self):
        """Should delete category."""
        count_before = Category.objects.count()
        response = self.client.delete(f'/api/v1/categories/{self.cat_food.id}')
        data = self.assert_success_response(response)
        self.assertEqual(data['message'], 'Category deleted')
        self.assertEqual(Category.objects.count(), count_before - 1)

    def test_delete_category_not_found(self):
        """Should return 404 for non-existent category."""
        response = self.client.delete('/api/v1/categories/99999')
        self.assert_error_response(response, 404)
