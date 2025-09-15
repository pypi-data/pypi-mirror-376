from typing import Optional

class InsufficientFundsError(Exception):
    pass

class Client:
    total_clients = 0

    def __init__(self, first_name: str, last_name: str, email: str,
                 balance: float = 0.0, address: Optional[str] = None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.balance = float(balance)
        self.address = address or ""
        Client.total_clients += 1

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def add_funds(self, amount: float):
        if amount <= 0:
            raise ValueError("O valor a adicionar deve ser positivo")
        self.balance += float(amount)

    def place_order(self, total_amount: float):
        if total_amount <= 0:
            raise ValueError("O valor do pedido deve ser positivo")
        if total_amount > self.balance:
            raise InsufficientFundsError("Saldo insuficiente para realizar o pedido")
        self.balance -= float(total_amount)
        return f"Pedido realizado com sucesso. Saldo restante: {self.balance:.2f}"

    def apply_discount(self, percent: float):
        if not (0 <= percent <= 100):
            raise ValueError("O percentual deve estar entre 0 e 100")
        discount = (percent / 100) * self.balance
        self.balance += discount

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "balance": round(self.balance, 2),
            "address": self.address,
        }

class VIPClient(Client):
    def __init__(self, first_name: str, last_name: str, email: str,
                 balance: float = 0.0, address: Optional[str] = None,
                 vip_level: int = 1):
        super().__init__(first_name, last_name, email, balance, address)
        self.vip_level = int(vip_level)
        self.membership_id = f"VIP-{Client.total_clients:06d}"

    def apply_vip_discount(self, purchase_amount: float) -> float:
        discount_rate = min(0.15, 0.05 * self.vip_level)
        return float(purchase_amount) * (1 - discount_rate)
