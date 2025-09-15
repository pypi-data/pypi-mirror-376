# MichaelBaldezSeuModeloDeClientes

Pacote simples para modelamento de **Clientes**.

## Conteúdo
- `client_model/client.py` – implementação da classe `Client` e `VIPClient`.
- `examples/demo.py` – exemplo de uso.
- `PRE-ENTREGA-1.txt` – arquivo extra exigido.
- `setup.py` – script para empacotamento.

## Como usar
```python
from client_model.client import Client, VIPClient

c = Client('Ana', 'Silva', 'ana@example.com', balance=100.0)
print(c)
c.add_funds(50)
print(c.place_order(120))
