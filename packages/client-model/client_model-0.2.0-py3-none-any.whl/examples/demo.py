import json
from client_model.client import Client, VIPClient

def main():
    # Criar clientes normais
    clients = [
        Client("Carlos", "Pereira", "carlos@example.com", balance=100.0, address="Rua das Flores, 10"),
        Client("Ana", "Silva", "ana@example.com", balance=150.0, address="Av. Brasil, 50"),
        Client("João", "Souza", "joao@example.com", balance=80.0),
    ]

    # Criar clientes VIP (herança)
    vip_clients = [
        VIPClient("Mariana", "Costa", "mari@example.com", balance=200.0, vip_level=3),
        VIPClient("Pedro", "Almeida", "pedro@example.com", balance=500.0, vip_level=5),
    ]

    all_clients = clients + vip_clients

    print("\n--- Clientes Criados ---")
    for c in all_clients:
        print(c)

    # Testar alguns métodos
    print("\n-- Testando add_funds e place_order --")
    clients[0].add_funds(50)
    try:
        result = clients[0].place_order(180)  # Deve dar erro se saldo insuficiente
        print(result)
    except Exception as e:
        print(f"Erro: {e}")

    # Testar desconto VIP
    print("\n-- Testando VIP discount --")
    for vip in vip_clients:
        original_amount = 120
        discounted = vip.apply_vip_discount(original_amount)
        print(f"{vip.full_name()} | Original: {original_amount} | Com desconto VIP: {discounted}")

    # Gerar arquivo JSON com todos os clientes
    data = {
        "clients": [
            {
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "balance": c.balance,
                "address": getattr(c, "address", "")
            } for c in all_clients
        ]
    }

    with open("clients_export.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n✅ Arquivo clients_export.json gerado com todos os clientes.")

if __name__ == "__main__":
    main()
