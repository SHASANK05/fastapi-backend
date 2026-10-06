from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

class AuthAndCardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="securepassword123"
        )
        # Login to obtain JWT
        login_res = self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "securepassword123"
        }, format="json")
        self.token = login_res.data.get("access")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_jwt_login_successful(self):
        self.assertIsNotNone(self.token)

    def test_jwt_login_invalid_credentials(self):
        client = APIClient()
        res = client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "wrongpassword"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_card_masks_number_and_does_not_save_raw(self):
        card_data = {
            "cardholder_name": "Test User",
            "card_number": "4111222233334444",
            "expiry_month": 12,
            "expiry_year": 2028,
            "card_type": "Visa"
        }
        res = self.client.post("/api/cards/", card_data, format="json")
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # Verify saved data structure
        list_res = self.client.get("/api/cards/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        saved_cards = list_res.data
        self.assertTrue(len(saved_cards) > 0)
        first_card = saved_cards[0]
        self.assertEqual(first_card["last_4"], "4444")
        self.assertNotIn("4111222233334444", str(first_card))