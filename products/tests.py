from rest_framework.test import APITestCase
from rest_framework import status


class ProductAPITest(APITestCase):

    def test_get_products(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)