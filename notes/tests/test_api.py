from django.urls import reverse
from rest_framework.test import APITestCase
from notes.models import Note as NoteModel
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class NotesAPITest(APITestCase):

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        # Add token to client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        # Create test note
        self.note = NoteModel.objects.create(
            title="Test",
            text="Hello",
            original_language="en"
        )

    def test_list_notes(self):
        url = reverse('note-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.data) >= 1)

    def test_translate_cached(self):
        url = reverse('note-translate', args=[self.note.id])
        with patch('notes.views.translate_text_via_api') as mock_translate:
            mock_translate.return_value = "नमस्ते"
            resp = self.client.post(url, {'target_language': 'hi'}, format='json')
            self.assertEqual(resp.status_code, 200)
            self.assertIn('original', resp.data)
            self.assertIn('translated', resp.data)
            self.assertEqual(resp.data['translated'], "नमस्ते")

    def test_stats(self):
        url = '/api/stats/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('total_notes', resp.data)
