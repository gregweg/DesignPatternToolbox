"""
Entity — Domain-Driven Design

An Entity has a unique identity that persists across time and state changes.
Two entities with identical attributes but different identities are NOT equal —
a customer named "Alice" at address X is a different person from another
customer named "Alice" at the same address if their IDs differ.

Key characteristics:
  - Has a stable, unique identifier assigned at creation
  - Mutable — its state changes over its lifetime
  - Equality by identity (ID), not by attributes
  - Encapsulates its own invariants (rejects invalid state transitions)

Contrast with Value Object: a Value Object has no identity and is equal to
any other Value Object with the same attributes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
from value_object import Email, Address, Money


# ---------------------------------------------------------------------------
# Identity types — typed wrappers prevent mixing up IDs accidentally
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CustomerId:
    value: str = field(default_factory=lambda: str(uuid4()))

@dataclass(frozen=True)
class ProductId:
    value: str = field(default_factory=lambda: str(uuid4()))


# ---------------------------------------------------------------------------
# Customer entity
# ---------------------------------------------------------------------------

class Customer:
    """
    Entity representing a customer. Identity is CustomerId.

    Two Customer objects with the same CustomerId are the same customer,
    even if their name or address has changed.
    """

    def __init__(self, customer_id: CustomerId, name: str, email: Email) -> None:
        if not name.strip():
            raise ValueError("Customer name cannot be empty")
        self._id = customer_id
        self._name = name
        self._email = email
        self._shipping_address: Address | None = None
        self._active = True

    # --- identity ---

    @property
    def id(self) -> CustomerId:
        return self._id

    # --- queries ---

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> Email:
        return self._email

    @property
    def shipping_address(self) -> Address | None:
        return self._shipping_address

    @property
    def is_active(self) -> bool:
        return self._active

    # --- commands ---

    def update_email(self, new_email: Email) -> None:
        self._email = new_email

    def set_shipping_address(self, address: Address) -> None:
        self._shipping_address = address

    def deactivate(self) -> None:
        if not self._active:
            raise ValueError("Customer is already inactive")
        self._active = False

    # --- identity-based equality ---

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Customer(id={self._id.value[:8]}…, name={self._name!r})"


# ---------------------------------------------------------------------------
# Product entity
# ---------------------------------------------------------------------------

class Product:
    """
    Entity representing a product. Identity is ProductId.

    Stock and price are mutable over the product's lifetime. Two products
    with the same name and price are still different products if their IDs differ.
    """

    def __init__(self, product_id: ProductId, name: str, price: Money, stock: int = 0) -> None:
        if stock < 0:
            raise ValueError("Initial stock cannot be negative")
        self._id = product_id
        self._name = name
        self._price = price
        self._stock = stock

    # --- identity ---

    @property
    def id(self) -> ProductId:
        return self._id

    # --- queries ---

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> Money:
        return self._price

    @property
    def stock(self) -> int:
        return self._stock

    # --- commands ---

    def restock(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")
        self._stock += quantity

    def reserve(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Reserve quantity must be positive")
        if quantity > self._stock:
            raise ValueError(f"Insufficient stock: requested {quantity}, available {self._stock}")
        self._stock -= quantity

    def update_price(self, new_price: Money) -> None:
        self._price = new_price

    # --- identity-based equality ---

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Product(id={self._id.value[:8]}…, name={self._name!r}, price={self._price}, stock={self._stock})"


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Same ID → same entity, even with different attributes
    cid = CustomerId()
    c1 = Customer(cid, "Alice",       Email("alice@example.com"))
    c2 = Customer(cid, "Alice Smith", Email("alice@example.com"))  # name differs
    print(f"Same id, different name — equal: {c1 == c2}")   # True

    # Different ID → different entity
    c3 = Customer(CustomerId(), "Alice", Email("alice@example.com"))
    print(f"Different id, same name   — equal: {c1 == c3}")  # False

    # Product invariants
    product = Product(ProductId(), "Widget", Money(999), stock=10)
    product.reserve(3)
    print(f"Stock after reserve(3): {product.stock}")        # 7

    try:
        product.reserve(100)
    except ValueError as e:
        print(f"Invariant enforced: {e}")

    # State change over lifetime
    product.update_price(Money(1099))
    print(f"Price updated: {product.price}")
