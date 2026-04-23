"""
Aggregate Pattern — Domain-Driven Design

Key rules:
  - The Aggregate Root is the ONLY entry point for mutations
  - Invariants (business rules) are enforced inside the boundary
  - Domain Events capture what happened, not just what changed
  - Nothing outside the boundary holds a reference to inner entities
  - Cross-aggregate references use keys only (e.g. sku str), not object refs
  - Persistence (Repository) operates on the root only, never on children
"""

from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
from typing import Protocol


# ---------------------------------------------------------------------------
# Value Objects — immutable, no identity, defined by their attributes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Money:
    amount: int  # cents
    currency: str = "USD"

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")
        return Money(self.amount - other.amount, self.currency)


@dataclass(frozen=True)
class OrderId:
    value: str = field(default_factory=lambda: str(uuid4()))


# ---------------------------------------------------------------------------
# Domain Events — immutable facts emitted by the aggregate root
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OrderItemAdded:
    order_id: str
    sku: str
    quantity: int

@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    total: Money

@dataclass(frozen=True)
class OrderCancelled:
    order_id: str


# ---------------------------------------------------------------------------
# Inner Entity — lives inside the aggregate boundary only.
# Prefixed with _ to signal it is not part of the public API.
# ---------------------------------------------------------------------------

@dataclass
class _OrderLine:
    sku: str
    quantity: int
    unit_price: Money

    @property
    def subtotal(self) -> Money:
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


# ---------------------------------------------------------------------------
# Aggregate Root — the only public interface for the Order aggregate
# ---------------------------------------------------------------------------

class Order:
    """
    Aggregate root for the Order aggregate.

    _OrderLine entities are fully encapsulated. Callers receive an immutable
    snapshot via the `lines` property and cannot mutate children directly.
    References to products are held by key (sku: str) only — Product is a
    separate aggregate accessed via its own Repository.
    """

    def __init__(self, order_id: OrderId) -> None:
        self._id = order_id
        self._lines: list[_OrderLine] = []
        self._placed = False
        self._cancelled = False
        self._events: list = []

    # --- identity (entities compare by id, not by value) ---

    @property
    def id(self) -> OrderId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    # --- commands (mutate state, enforce invariants) ---

    def add_item(self, sku: str, quantity: int, unit_price: Money) -> None:
        self._guard_not_placed("Cannot add items after order is placed")
        self._guard_not_cancelled("Cannot add items to a cancelled order")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self._lines.append(_OrderLine(sku, quantity, unit_price))
        self._events.append(OrderItemAdded(self._id.value, sku, quantity))

    def place(self) -> None:
        self._guard_not_placed("Order is already placed")
        self._guard_not_cancelled("Cannot place a cancelled order")
        if not self._lines:
            raise ValueError("Cannot place an empty order")
        self._placed = True
        self._events.append(OrderPlaced(self._id.value, self.total))

    def cancel(self) -> None:
        self._guard_not_cancelled("Order is already cancelled")
        self._cancelled = True
        self._events.append(OrderCancelled(self._id.value))

    # --- queries (read-only) ---

    @property
    def total(self) -> Money:
        result = Money(0)
        for line in self._lines:
            result = result + line.subtotal
        return result

    @property
    def lines(self) -> tuple[_OrderLine, ...]:
        """Immutable snapshot — prevents external mutation of inner entities."""
        return tuple(self._lines)

    def pop_events(self) -> list:
        events, self._events = self._events, []
        return events

    # --- guards ---

    def _guard_not_placed(self, msg: str) -> None:
        if self._placed:
            raise ValueError(msg)

    def _guard_not_cancelled(self, msg: str) -> None:
        if self._cancelled:
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Repository Protocol — persistence lives outside the aggregate
# ---------------------------------------------------------------------------

class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def get(self, order_id: OrderId) -> Order: ...


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    order = Order(OrderId())

    order.add_item("SKU-001", 2, Money(1500))   # 2x $15.00
    order.add_item("SKU-002", 1, Money(3000))   # 1x $30.00

    print(f"Total before place: ${order.total.amount / 100:.2f}")
    print(f"Lines: {order.lines}")

    order.place()
    print(f"Order placed. Events: {order.pop_events()}")

    try:
        order.add_item("SKU-003", 1, Money(500))
    except ValueError as e:
        print(f"Invariant enforced: {e}")

    order.cancel()
    print(f"Cancelled. Events: {order.pop_events()}")

    try:
        order.cancel()
    except ValueError as e:
        print(f"Invariant enforced: {e}")
