"""
Specification — Domain-Driven Design

A Specification encapsulates a single business rule as a first-class object.
Specifications can be combined with AND (&), OR (|), and NOT (~) to build
complex rules from simple, named, individually-testable pieces.

Key characteristics:
  - Single responsibility: one rule per class, named after the domain concept
  - Composable: & | ~ operators produce new specifications without mutation
  - Reusable: the same specification works for filtering, validation, and querying
  - Readable: composed expressions read like business language

Common uses:
  - Filtering collections:  repo.find_all(InStock() & PriceAtMost(Money(2000)))
  - Validation before save: spec.is_satisfied_by(product) or raise
  - Query building:         translate spec tree into SQL WHERE clauses
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from entity import Product
from value_object import Money


# ---------------------------------------------------------------------------
# Base Specification — defines the interface and composition operators
# ---------------------------------------------------------------------------

class Specification(ABC):

    @abstractmethod
    def is_satisfied_by(self, candidate: object) -> bool: ...

    def __and__(self, other: Specification) -> Specification:
        return _And(self, other)

    def __or__(self, other: Specification) -> Specification:
        return _Or(self, other)

    def __invert__(self) -> Specification:
        return _Not(self)


# ---------------------------------------------------------------------------
# Logical combinators — kept private; use operators on Specification instead
# ---------------------------------------------------------------------------

class _And(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: object) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class _Or(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: object) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class _Not(Specification):
    def __init__(self, spec: Specification) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: object) -> bool:
        return not self._spec.is_satisfied_by(candidate)


# ---------------------------------------------------------------------------
# Concrete Product Specifications — one class per business rule
# ---------------------------------------------------------------------------

class InStock(Specification):
    """Product has at least one unit available."""

    def is_satisfied_by(self, candidate: object) -> bool:
        assert isinstance(candidate, Product)
        return candidate.stock > 0


class LowStock(Specification):
    """Product stock is at or below a given threshold."""

    def __init__(self, threshold: int = 5) -> None:
        self._threshold = threshold

    def is_satisfied_by(self, candidate: object) -> bool:
        assert isinstance(candidate, Product)
        return candidate.stock <= self._threshold


class PriceAtMost(Specification):
    """Product price does not exceed a given ceiling."""

    def __init__(self, max_price: Money) -> None:
        self._max = max_price

    def is_satisfied_by(self, candidate: object) -> bool:
        assert isinstance(candidate, Product)
        return (
            candidate.price.currency == self._max.currency
            and candidate.price.amount <= self._max.amount
        )


class PriceAtLeast(Specification):
    """Product price meets or exceeds a given floor."""

    def __init__(self, min_price: Money) -> None:
        self._min = min_price

    def is_satisfied_by(self, candidate: object) -> bool:
        assert isinstance(candidate, Product)
        return (
            candidate.price.currency == self._min.currency
            and candidate.price.amount >= self._min.amount
        )


class NameContains(Specification):
    """Product name contains a keyword (case-insensitive)."""

    def __init__(self, keyword: str) -> None:
        self._keyword = keyword.lower()

    def is_satisfied_by(self, candidate: object) -> bool:
        assert isinstance(candidate, Product)
        return self._keyword in candidate.name.lower()


# ---------------------------------------------------------------------------
# Helper — filter a list using any specification
# ---------------------------------------------------------------------------

def satisfying(products: list[Product], spec: Specification) -> list[Product]:
    return [p for p in products if spec.is_satisfied_by(p)]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from entity import Product, ProductId

    catalog = [
        Product(ProductId(), "Widget Pro",    Money(999),  stock=10),
        Product(ProductId(), "Gadget",         Money(2499), stock=0),
        Product(ProductId(), "Super Widget",   Money(1499), stock=3),
        Product(ProductId(), "Thingamajig",    Money(499),  stock=0),
        Product(ProductId(), "Premium Gadget", Money(4999), stock=8),
    ]

    in_stock       = InStock()
    affordable     = PriceAtMost(Money(1500))
    is_widget      = NameContains("widget")
    low_stock      = LowStock(threshold=5)

    # --- simple specifications ---
    print("In stock:")
    for p in satisfying(catalog, in_stock):
        print(f"  {p}")

    # --- AND composition ---
    print("\nIn stock AND affordable (≤ $15.00):")
    for p in satisfying(catalog, in_stock & affordable):
        print(f"  {p}")

    # --- OR composition ---
    print("\nWidget OR affordable:")
    for p in satisfying(catalog, is_widget | affordable):
        print(f"  {p}")

    # --- NOT composition ---
    print("\nNot in stock:")
    for p in satisfying(catalog, ~in_stock):
        print(f"  {p}")

    # --- chained composition: in stock, low stock, and affordable ---
    print("\nIn stock AND low stock AND affordable (needs reordering soon):")
    for p in satisfying(catalog, in_stock & low_stock & affordable):
        print(f"  {p}")
