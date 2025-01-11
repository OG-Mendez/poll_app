"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""



import django
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Question, Choice
from django.contrib.auth.models import User

# TODO: Configure your database in settings.py and sync before running tests.

class ViewTest(TestCase):
    """Tests for the application views."""

    if django.VERSION[:2] >= (1, 7):
        # Django 1.7 requires an explicit setup() when running tests in PTVS
        @classmethod
        def setUpClass(cls):
            super(ViewTest, cls).setUpClass()
            django.setup()

class PollsAPITestCase(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)

        self.create_poll_url = reverse('create_poll')
        self.get_questions_url = reverse('get_questions')
        self.vote_url = reverse('vote')
        self.results_url = reverse('results')
        self.poll_data = {
            "tag": "poll123",
            "question": "What's your favorite color?",
            "end_time": "2025-01-15T12:00:00Z",
            "choices": [
                {"option": "A", "text": "Red"},
                {"option": "B", "text": "Blue"},
                {"option": "C", "text": "Green"}
            ]
        }
    
    def test_create_poll(self):
        response = self.client.post(self.create_poll_url, self.poll_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)

    def test_get_questions(self):
        self.test_create_poll()  # Create poll first
        tag = "poll123"
        code = Question.objects.first().code  # Assume first question for simplicity
        response = self.client.get(f"{self.get_questions_url}?tag={tag}&code={code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("question", response.data)

    def test_vote(self):
        self.test_create_poll()  # Create poll first
        tag = "poll123"
        code = Question.objects.first().code  # Assume first question for simplicity
        response = self.client.post(f"{self.vote_url}?tag={tag}&code={code}", {"choice": "B"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_results(self):
        self.test_create_poll()  # Create poll first
        tag = "poll123"
        code = Question.objects.first().code  # Assume first question for simplicity
        Question.objects.first().end_time = "2024-01-01T00:00:00Z"  # Set poll to ended
        Question.objects.first().save()
        response = self.client.get(f"{self.results_url}?tag={tag}&code={code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("choices", response.data)
        self.assertIsInstance(response.data["choices"], list)
        self.assertGreater(len(response.data["choices"]), 0)
