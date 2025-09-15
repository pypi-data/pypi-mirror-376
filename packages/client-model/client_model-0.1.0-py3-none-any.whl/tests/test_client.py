import unittest
from client_model.client import Client, VIPClient, InsufficientFundsError

class TestClient(unittest.TestCase):

    def setUp(self):
        # Cria objetos de teste
        self.client = Client("Carlos", "Pereira", "carlos@example.com", balance=100.0)
        self.vip = VIPClient("Mariana", "Costa", "mari@example.com", balance=200.0, vip_level=3)

    def test_full_name(self):
        self.assertEqual(self.client.full_name(), "Carlos Pereira")
        self.assertEqual(self.vip.full_name(), "Mariana Costa")

    def test_add_funds(self):
        self.client.add_funds(50)
        self.assertEqual(self.client.balance, 150)

    def test_place_order_success(self):
        result = self.client.place_order(50)
        self.assertEqual(self.client.balance, 50)
        self.assertIn("Pedido realizado com sucesso", result)

    def test_place_order_insufficient(self):
        with self.assertRaises(InsufficientFundsError):
            self.client.place_order(200)

    def test_apply_discount(self):
        self.client.apply_discount(10)  # 10%
        self.assertAlmostEqual(self.client.balance, 110.0)

    def test_vip_discount(self):
        original_amount = 100
        discounted = self.vip.apply_vip_discount(original_amount)
        self.assertLess(discounted, original_amount)

    def test_str_method(self):
        self.assertEqual(str(self.client), "Carlos Pereira <carlos@example.com>")
        self.assertEqual(str(self.vip), "Mariana Costa <mari@example.com>")

if __name__ == '__main__':
    unittest.main()
