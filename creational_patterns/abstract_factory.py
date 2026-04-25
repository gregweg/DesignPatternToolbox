"""
Abstract Factory — Creational Design Pattern

Provides an interface for creating a *family* of related objects without
specifying their concrete classes. Each concrete factory produces a suite of
products guaranteed to be compatible with each other.

Key characteristics:
  - Client code is written against factory and product *interfaces* only
  - Swapping the factory swaps the entire product family in one place
  - Products within a family are designed to work together; mixing products
    from different factories is prevented by construction

Contrast with Factory Method: Factory Method uses inheritance — a subclass
overrides one factory method to change one product type. Abstract Factory
uses composition — a factory *object* is injected and provides a whole suite
of related creation methods. Abstract Factory is essentially a group of
coordinated Factory Methods living on one object.
"""

from __future__ import annotations
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Abstract Products — one interface per product kind in the family
# ---------------------------------------------------------------------------

class Button(ABC):
    """A clickable UI element."""

    @abstractmethod
    def render(self) -> str: ...

    @abstractmethod
    def on_click(self) -> str: ...


class Dialog(ABC):
    """A modal container that hosts a primary action button."""

    @abstractmethod
    def render(self, title: str, body: str, button: Button) -> str: ...


class Checkbox(ABC):
    """A toggleable boolean control."""

    @abstractmethod
    def render(self, label: str, checked: bool) -> str: ...


# ---------------------------------------------------------------------------
# Abstract Factory — declares creation methods for each product kind
# ---------------------------------------------------------------------------

class UIFactory(ABC):
    """
    Creates a family of UI widgets that share a visual theme.
    All products from the same factory are guaranteed to be compatible.
    """

    @abstractmethod
    def create_button(self, label: str) -> Button: ...

    @abstractmethod
    def create_dialog(self) -> Dialog: ...

    @abstractmethod
    def create_checkbox(self) -> Checkbox: ...


# ---------------------------------------------------------------------------
# Light Theme — Concrete Factory + Products
# ---------------------------------------------------------------------------

class LightButton(Button):
    def __init__(self, label: str) -> None:
        self._label = label

    def render(self) -> str:
        return f"[ {self._label} ]"

    def on_click(self) -> str:
        return f"Light: '{self._label}' clicked"


class LightDialog(Dialog):
    def render(self, title: str, body: str, button: Button) -> str:
        width = 40
        border = "-" * width
        return (
            f"+{border}+\n"
            f"| {title:<{width - 1}}|\n"
            f"+{border}+\n"
            f"| {body:<{width - 1}}|\n"
            f"| {button.render():<{width - 1}}|\n"
            f"+{border}+"
        )


class LightCheckbox(Checkbox):
    def render(self, label: str, checked: bool) -> str:
        mark = "x" if checked else " "
        return f"[{mark}] {label}"


class LightThemeFactory(UIFactory):
    def create_button(self, label: str) -> Button:
        return LightButton(label)

    def create_dialog(self) -> Dialog:
        return LightDialog()

    def create_checkbox(self) -> Checkbox:
        return LightCheckbox()


# ---------------------------------------------------------------------------
# Dark Theme — Concrete Factory + Products
# ---------------------------------------------------------------------------

class DarkButton(Button):
    def __init__(self, label: str) -> None:
        self._label = label

    def render(self) -> str:
        return f"  {self._label.upper()}  "

    def on_click(self) -> str:
        return f"Dark: '{self._label}' clicked"


class DarkDialog(Dialog):
    def render(self, title: str, body: str, button: Button) -> str:
        width = 40
        return (
            f"{'=' * width}\n"
            f"  {title}\n"
            f"{'=' * width}\n"
            f"  {body}\n"
            f"  {button.render()}\n"
            f"{'=' * width}"
        )


class DarkCheckbox(Checkbox):
    def render(self, label: str, checked: bool) -> str:
        mark = ">" if checked else " "
        return f"({mark}) {label}"


class DarkThemeFactory(UIFactory):
    def create_button(self, label: str) -> Button:
        return DarkButton(label)

    def create_dialog(self) -> Dialog:
        return DarkDialog()

    def create_checkbox(self) -> Checkbox:
        return DarkCheckbox()


# ---------------------------------------------------------------------------
# Client code — depends only on abstractions, never on concrete classes
# ---------------------------------------------------------------------------

def render_checkout_screen(factory: UIFactory) -> None:
    """
    Receives a factory and uses it exclusively. It never references
    LightButton, DarkDialog, or any other concrete class — the factory
    decides which family of widgets to materialise.
    """
    confirm  = factory.create_button("Confirm Order")
    cancel   = factory.create_button("Cancel")
    dialog   = factory.create_dialog()
    remember = factory.create_checkbox()

    print(dialog.render("Checkout", "Review your order before confirming.", confirm))
    print(remember.render("Remember my details", True))
    print(cancel.render())
    print(confirm.on_click())


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Light Theme ===")
    render_checkout_screen(LightThemeFactory())

    print("\n=== Dark Theme ===")
    render_checkout_screen(DarkThemeFactory())

    # Swapping the factory is the *only* change needed to switch the entire UI family
