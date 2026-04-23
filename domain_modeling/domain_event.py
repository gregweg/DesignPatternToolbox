"""
Domain Event — Domain-Driven Design

A Domain Event is an immutable record that something meaningful happened in
the domain. Events are named in the past tense — they are facts, not requests.
They decouple the part of the system that causes something to happen from the
parts that need to react to it.

Key characteristics:
  - Immutable (frozen dataclass) — they describe the past, which cannot change
  - Named in past tense: OrderPlaced, CustomerRegistered, PaymentFailed
  - Carry all the data needed to understand what happened
  - Emitted by Aggregate Roots; consumed by handlers elsewhere
  - Enable loose coupling: the emitter has no knowledge of its consumers

This module also includes a simple in-process EventBus. In production, events
are typically published to a message broker (Kafka, RabbitMQ, SNS) so that
other services can react without direct coupling.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable, Type, TypeVar
from uuid import uuid4

E = TypeVar("E", bound="DomainEvent")
Handler = Callable[["DomainEvent"], Awaitable[None]]


# ---------------------------------------------------------------------------
# Base Domain Event — all events share a common envelope
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Concrete events — one class per meaningful occurrence, named in past tense
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CustomerRegistered(DomainEvent):
    customer_id: str = ""
    name: str = ""
    email: str = ""

@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    total_cents: int = 0

@dataclass(frozen=True)
class PaymentProcessed(DomainEvent):
    order_id: str = ""
    amount_cents: int = 0
    provider: str = ""

@dataclass(frozen=True)
class PaymentFailed(DomainEvent):
    order_id: str = ""
    reason: str = ""

@dataclass(frozen=True)
class InventoryLow(DomainEvent):
    product_id: str = ""
    current_stock: int = 0
    threshold: int = 0


# ---------------------------------------------------------------------------
# Event Bus — in-process pub/sub
# ---------------------------------------------------------------------------

class EventBus:
    """
    Dispatches events to registered async handlers.

    Handlers are registered per event type. Multiple handlers per event type
    are supported and run concurrently. In production this thin interface
    would be backed by a message broker rather than direct in-process calls.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = {}

    def subscribe(self, event_type: Type[E], handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        print(f"[bus] {type(event).__name__} → {len(handlers)} handler(s)")
        await asyncio.gather(*(h(event) for h in handlers))


# ---------------------------------------------------------------------------
# Example handlers — each reacts to a specific event type
# ---------------------------------------------------------------------------

async def on_customer_registered(event: DomainEvent) -> None:
    assert isinstance(event, CustomerRegistered)
    print(f"  [email]     Welcome email sent to {event.email}")

async def on_order_placed_warehouse(event: DomainEvent) -> None:
    assert isinstance(event, OrderPlaced)
    print(f"  [warehouse] Pick list created for order {event.order_id}")

async def on_order_placed_analytics(event: DomainEvent) -> None:
    assert isinstance(event, OrderPlaced)
    print(f"  [analytics] Revenue event recorded: {event.total_cents / 100:.2f} USD")

async def on_inventory_low(event: DomainEvent) -> None:
    assert isinstance(event, InventoryLow)
    print(f"  [alert]     Stock low — product {event.product_id}: {event.current_stock} remaining (threshold {event.threshold})")

async def on_payment_failed(event: DomainEvent) -> None:
    assert isinstance(event, PaymentFailed)
    print(f"  [support]   Payment failed for order {event.order_id}: {event.reason}")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

async def main() -> None:
    bus = EventBus()

    bus.subscribe(CustomerRegistered, on_customer_registered)
    bus.subscribe(OrderPlaced,        on_order_placed_warehouse)
    bus.subscribe(OrderPlaced,        on_order_placed_analytics)   # two handlers for same event
    bus.subscribe(InventoryLow,       on_inventory_low)
    bus.subscribe(PaymentFailed,      on_payment_failed)

    await bus.publish(CustomerRegistered(customer_id="C-1", name="Alice", email="alice@example.com"))
    await bus.publish(OrderPlaced(order_id="ORD-1", customer_id="C-1", total_cents=5000))
    await bus.publish(InventoryLow(product_id="SKU-001", current_stock=2, threshold=5))
    await bus.publish(PaymentFailed(order_id="ORD-2", reason="Insufficient funds"))


if __name__ == "__main__":
    asyncio.run(main())
