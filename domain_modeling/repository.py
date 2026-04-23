"""
Repository — Domain-Driven Design

A Repository provides a collection-like interface for accessing and persisting
Aggregate Roots. It decouples the domain layer from infrastructure concerns —
the domain declares what it needs (the Protocol), and infrastructure provides
the concrete implementation (database, in-memory, file system, etc.).

Key characteristics:
  - Operates on Aggregate Roots only — never on inner entities or value objects
  - Presents a collection-like interface: add, get, find, remove
  - The domain depends on the interface (Protocol), not the implementation
  - Swapping the implementation (e.g. in-memory for tests, Postgres for prod)
    requires no changes to domain code

This module demonstrates:
  - Repository Protocols (the domain contract)
  - In-memory implementations (useful for tests and this demo)
  - How domain code works against the interface, not the concrete type
"""

from __future__ import annotations
from typing import Protocol
from entity import Customer, CustomerId, Product, ProductId
from value_object import Email, Money


# ---------------------------------------------------------------------------
# Repository Protocols — declared in the domain layer
# ---------------------------------------------------------------------------

class CustomerRepository(Protocol):
    def add(self, customer: Customer) -> None: ...
    def get(self, customer_id: CustomerId) -> Customer: ...
    def find_by_email(self, email: Email) -> Customer | None: ...
    def remove(self, customer_id: CustomerId) -> None: ...


class ProductRepository(Protocol):
    def add(self, product: Product) -> None: ...
    def get(self, product_id: ProductId) -> Product: ...
    def find_all(self) -> list[Product]: ...
    def find_in_stock(self) -> list[Product]: ...


# ---------------------------------------------------------------------------
# In-memory implementations — live in the infrastructure layer
# ---------------------------------------------------------------------------

class InMemoryCustomerRepository:
    def __init__(self) -> None:
        self._store: dict[str, Customer] = {}

    def add(self, customer: Customer) -> None:
        if customer.id.value in self._store:
            raise ValueError(f"Customer already exists: {customer.id.value}")
        self._store[customer.id.value] = customer

    def get(self, customer_id: CustomerId) -> Customer:
        customer = self._store.get(customer_id.value)
        if customer is None:
            raise KeyError(f"Customer not found: {customer_id.value}")
        return customer

    def find_by_email(self, email: Email) -> Customer | None:
        return next((c for c in self._store.values() if c.email == email), None)

    def remove(self, customer_id: CustomerId) -> None:
        if customer_id.value not in self._store:
            raise KeyError(f"Customer not found: {customer_id.value}")
        del self._store[customer_id.value]


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._store: dict[str, Product] = {}

    def add(self, product: Product) -> None:
        self._store[product.id.value] = product

    def get(self, product_id: ProductId) -> Product:
        product = self._store.get(product_id.value)
        if product is None:
            raise KeyError(f"Product not found: {product_id.value}")
        return product

    def find_all(self) -> list[Product]:
        return list(self._store.values())

    def find_in_stock(self) -> list[Product]:
        return [p for p in self._store.values() if p.stock > 0]


# ---------------------------------------------------------------------------
# Example domain service — depends only on the Protocol, not the implementation
# ---------------------------------------------------------------------------

def transfer_stock(
    from_id: ProductId,
    to_id: ProductId,
    quantity: int,
    repo: ProductRepository,
) -> None:
    """
    Moves stock between two products. Works with any ProductRepository
    implementation — in-memory, Postgres, or otherwise.
    """
    source = repo.get(from_id)
    destination = repo.get(to_id)
    source.reserve(quantity)       # enforces invariant: cannot go below 0
    destination.restock(quantity)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Customer repository
    customers: CustomerRepository = InMemoryCustomerRepository()

    alice = Customer(CustomerId(), "Alice", Email("alice@example.com"))
    bob   = Customer(CustomerId(), "Bob",   Email("bob@example.com"))
    customers.add(alice)
    customers.add(bob)

    found = customers.find_by_email(Email("alice@example.com"))
    print(f"Found by email: {found}")

    fetched = customers.get(alice.id)
    print(f"Fetched by id:  {fetched}")

    customers.remove(alice.id)
    try:
        customers.get(alice.id)
    except KeyError as e:
        print(f"After remove:   {e}")

    # Product repository + domain service
    products: ProductRepository = InMemoryProductRepository()
    widget = Product(ProductId(), "Widget", Money(999),  stock=20)
    gadget = Product(ProductId(), "Gadget", Money(2499), stock=5)
    products.add(widget)
    products.add(gadget)

    print(f"\nAll products:      {products.find_all()}")
    print(f"In stock:          {products.find_in_stock()}")

    # Transfer stock via domain service
    transfer_stock(widget.id, gadget.id, 5, products)
    print(f"\nAfter transfer:")
    print(f"  Widget stock: {products.get(widget.id).stock}")   # 15
    print(f"  Gadget stock: {products.get(gadget.id).stock}")   # 10
