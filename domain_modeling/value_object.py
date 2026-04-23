"""
Value Object — Domain-Driven Design

A Value Object has no identity. Two value objects with the same attributes
are interchangeable — there is no meaningful difference between one $10.00
and another $10.00. They are immutable: any operation returns a new instance
rather than modifying the existing one.

Key characteristics:
  - Immutable (frozen dataclass; invalid state rejected at construction)
  - Equality by value (all attributes), not by reference
  - No identity field
  - Self-validating — construction fails if the value is invalid
  - Operations return new instances, never mutate in place
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import date


# ---------------------------------------------------------------------------
# Money — currency-aware monetary amount
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Money:
    amount: int  # in cents; avoids floating-point errors
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")
        if len(self.currency) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code: {self.currency}")

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        if self.amount < other.amount:
            raise ValueError("Result would be negative")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int) -> Money:
        return Money(self.amount * factor, self.currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    def __str__(self) -> str:
        return f"{self.currency} {self.amount / 100:.2f}"


# ---------------------------------------------------------------------------
# Email — validated email address
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", self.value):
            raise ValueError(f"Invalid email address: {self.value!r}")

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Address — postal address
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    postal_code: str
    country: str

    def __post_init__(self) -> None:
        if not self.street.strip() or not self.city.strip():
            raise ValueError("Street and city are required")

    def __str__(self) -> str:
        return f"{self.street}, {self.city} {self.postal_code}, {self.country}"


# ---------------------------------------------------------------------------
# DateRange — inclusive range between two dates
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"End {self.end} must be >= start {self.start}")

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    def overlaps(self, other: DateRange) -> bool:
        return self.start <= other.end and self.end >= other.start

    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days

    def __str__(self) -> str:
        return f"{self.start} to {self.end} ({self.duration_days} days)"


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from datetime import date

    # Money: operations return new instances
    price = Money(1500)
    tax = Money(150)
    total = price + tax
    print(f"Price: {price}  Tax: {tax}  Total: {total}")

    # Value equality — same attributes, same value
    m1 = Money(1000)
    m2 = Money(1000)
    print(f"Money value equality: {m1 == m2}")       # True
    print(f"Not the same object: {m1 is not m2}")    # True

    # Self-validating construction
    try:
        bad = Money(-1)
    except ValueError as e:
        print(f"Validation: {e}")

    try:
        bad_email = Email("not-an-email")
    except ValueError as e:
        print(f"Validation: {e}")

    # Address equality
    a1 = Address("123 Main St", "Springfield", "12345", "US")
    a2 = Address("123 Main St", "Springfield", "12345", "US")
    print(f"Address value equality: {a1 == a2}")     # True

    # DateRange
    q1 = DateRange(date(2024, 1, 1), date(2024, 3, 31))
    q2 = DateRange(date(2024, 3, 1), date(2024, 6, 30))
    print(f"Q1: {q1}")
    print(f"Q1 overlaps Q2: {q1.overlaps(q2)}")
    print(f"Q1 contains 2024-02-14: {q1.contains(date(2024, 2, 14))}")
