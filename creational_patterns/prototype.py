"""
Prototype — Creational Design Pattern

Creates new objects by copying (cloning) an existing instance — the prototype.
The clone can then be modified independently of the original without re-running
expensive construction logic or re-specifying shared baseline configuration.

Key characteristics:
  - Cloning bypasses the constructor; useful when construction is expensive
    or when the exact class of the object is unknown at copy time
  - The prototype controls how it is copied (shallow vs deep)
  - A registry of named prototypes acts as a catalogue of pre-configured objects
    that callers check out copies of

Shallow copy: copies the container but not the nested objects it references.
  Mutating a nested list in the clone also changes the original — usually wrong.
Deep copy: copies the container AND all nested objects recursively.
  The clone is completely independent — the safe default for mutable prototypes.

Contrast with Builder: Builder constructs from scratch step by step.
Prototype starts from a known-good configuration and diverges from there.
Use Prototype when a baseline is complex and most new instances differ only
slightly from an existing one.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Prototype mixin — any object that knows how to clone itself
# ---------------------------------------------------------------------------

class Cloneable:
    """Provides a clone() method backed by copy.deepcopy."""

    def clone(self) -> Cloneable:
        return copy.deepcopy(self)


# ---------------------------------------------------------------------------
# Concrete Prototypes
# ---------------------------------------------------------------------------

@dataclass
class EmailTemplate(Cloneable):
    """
    A reusable email template. A master template is registered once;
    each outbound message clones it and fills in the recipient-specific
    placeholders, leaving the master intact.
    """
    subject:   str
    body:      str
    from_addr: str            = "noreply@example.com"
    cc:        list[str]      = field(default_factory=list)
    tags:      dict[str, str] = field(default_factory=dict)

    def personalise(self, name: str, **substitutions: str) -> EmailTemplate:
        """Return a clone with {{name}} and other placeholders filled in."""
        cloned = self.clone()
        cloned.subject = cloned.subject.replace("{{name}}", name)
        cloned.body    = cloned.body.replace("{{name}}", name)
        for key, value in substitutions.items():
            cloned.body = cloned.body.replace(f"{{{{{key}}}}}", value)
        return cloned


@dataclass
class DashboardLayout(Cloneable):
    """
    A configurable dashboard layout. System defaults are registered as
    prototypes; each user clones a default and customises their own copy
    without affecting anyone else's view.
    """
    name:    str
    columns: int                   = 3
    widgets: list[dict[str, Any]]  = field(default_factory=list)
    theme:   str                   = "light"
    pinned:  bool                  = False

    def add_widget(self, widget_type: str, **config: Any) -> DashboardLayout:
        self.widgets.append({"type": widget_type, **config})
        return self

    def pin(self) -> DashboardLayout:
        self.pinned = True
        return self


# ---------------------------------------------------------------------------
# Prototype Registry — a catalogue of named, pre-configured prototypes
# ---------------------------------------------------------------------------

class PrototypeRegistry:
    """
    Stores named master prototypes. Callers always receive a deep copy via
    get() so the registered master is never mutated by client code.
    """

    def __init__(self) -> None:
        self._store: dict[str, Cloneable] = {}

    def register(self, name: str, prototype: Cloneable) -> None:
        self._store[name] = prototype

    def get(self, name: str) -> Cloneable:
        if name not in self._store:
            raise KeyError(f"No prototype registered under {name!r}")
        return self._store[name].clone()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # ---- EmailTemplate ----
    master = EmailTemplate(
        subject="Hello {{name}}, your order is ready",
        body=(
            "Hi {{name}},\n\n"
            "Order #{{order_id}} has shipped.\n"
            "Expected delivery: {{delivery_date}}.\n\n"
            "Thanks,\nThe Team"
        ),
        tags={"campaign": "order-shipped"},
    )

    alice_email = master.personalise(
        "Alice", order_id="ORD-001", delivery_date="2024-03-15"
    )
    bob_email = master.personalise(
        "Bob", order_id="ORD-002", delivery_date="2024-03-17"
    )

    print("Master still has placeholders:")
    print(f"  {master.subject}")

    print("\nAlice's personalised email:")
    print(f"  Subject: {alice_email.subject}")
    print(f"  {alice_email.body}")

    # Deep copy — alice's cc list is independent of master's
    alice_email.cc.append("manager@example.com")
    print(f"\nMaster cc after Alice added to hers: {master.cc}")  # []

    # ---- DashboardLayout via Registry ----
    registry = PrototypeRegistry()

    default_layout = (
        DashboardLayout("default")
        .add_widget("chart",  title="Revenue",   size="large")
        .add_widget("table",  title="Orders",    size="medium")
        .add_widget("metric", title="NPS Score")
    )
    registry.register("default", default_layout)

    alice_dash = registry.get("default")
    assert isinstance(alice_dash, DashboardLayout)
    alice_dash.name  = "Alice's Dashboard"
    alice_dash.theme = "dark"
    alice_dash.add_widget("metric", title="My Open Tickets")

    bob_dash = registry.get("default")
    assert isinstance(bob_dash, DashboardLayout)
    bob_dash.name = "Bob's Dashboard"

    print(f"\nDefault layout widgets : {len(default_layout.widgets)}")  # 3
    print(f"Alice's widgets        : {len(alice_dash.widgets)}")         # 4
    print(f"Bob's widgets          : {len(bob_dash.widgets)}")           # 3
    print(f"Master name unchanged  : {default_layout.name == 'default'}")
