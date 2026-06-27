import json
from unittest.mock import MagicMock, patch

from api.tests.base import BaseAPITestCase


class AIAssistantTests(BaseAPITestCase):

    def test_ai_assistant_returns_error_when_no_input(self):
        response = self.client.post('/api/v1/ai/assistant', {}, format='multipart')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("Please provide", data['message'])

    @patch('api.views.ai_views.genai.Client')
    def test_ai_assistant_text_post_returns_ai_response(self, mock_client_cls):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            'message': 'Hello from AI',
            'action': None,
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        response = self.client.post('/api/v1/ai/assistant', {'text': 'Hello AI'}, format='multipart')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['message'], 'Hello from AI')
        self.assertIsNone(data['data']['action'])
        mock_client.models.generate_content.assert_called_once()
