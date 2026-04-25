"""
Factory Method — Creational Design Pattern

Defines an interface for creating a single type of object, but delegates the
decision of which concrete class to instantiate to subclasses. The creator
class has a factory method that subclasses override; the rest of the creator
uses the factory method without ever referencing a concrete product.

Key characteristics:
  - Decouples the "what to create" decision from the "how to use it" logic
  - Adding a new product type requires only a new creator subclass — existing
    code is untouched (Open/Closed Principle)
  - The factory method is usually the *only* thing that differs between
    creator subclasses; all other behaviour is inherited

Contrast with Abstract Factory: Factory Method deals with one product type
and uses inheritance (subclass overrides one method). Abstract Factory
deals with a *family* of related product types and uses composition
(a factory object is injected, providing a suite of creation methods).
"""

from __future__ import annotations
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Product — the interface all created objects implement
# ---------------------------------------------------------------------------

class Formatter(ABC):
    """Converts tabular data to an exportable string representation."""

    @abstractmethod
    def format_header(self, columns: list[str]) -> str: ...

    @abstractmethod
    def format_row(self, row: list[str]) -> str: ...

    @abstractmethod
    def format_footer(self) -> str: ...

    def format_table(self, columns: list[str], rows: list[list[str]]) -> str:
        """Template method — assembles header, rows, and footer in order."""
        parts = [self.format_header(columns)]
        parts.extend(self.format_row(r) for r in rows)
        footer = self.format_footer()
        if footer:
            parts.append(footer)
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Concrete Products
# ---------------------------------------------------------------------------

class CSVFormatter(Formatter):
    def format_header(self, columns: list[str]) -> str:
        return ",".join(columns)

    def format_row(self, row: list[str]) -> str:
        # Quote values that contain commas
        return ",".join(f'"{v}"' if "," in v else v for v in row)

    def format_footer(self) -> str:
        return ""


class MarkdownFormatter(Formatter):
    def format_header(self, columns: list[str]) -> str:
        header  = "| " + " | ".join(columns) + " |"
        divider = "| " + " | ".join("---" for _ in columns) + " |"
        return header + "\n" + divider

    def format_row(self, row: list[str]) -> str:
        return "| " + " | ".join(row) + " |"

    def format_footer(self) -> str:
        return ""


class HTMLFormatter(Formatter):
    def format_header(self, columns: list[str]) -> str:
        cells = "".join(f"<th>{c}</th>" for c in columns)
        return f"<table>\n<thead><tr>{cells}</tr></thead>\n<tbody>"

    def format_row(self, row: list[str]) -> str:
        cells = "".join(f"<td>{v}</td>" for v in row)
        return f"  <tr>{cells}</tr>"

    def format_footer(self) -> str:
        return "</tbody>\n</table>"


# ---------------------------------------------------------------------------
# Creator — defines the factory method and the algorithm that uses it
# ---------------------------------------------------------------------------

class DataExporter(ABC):
    """
    Creator. Subclasses override create_formatter() to change the output
    format. The export() method — the template — uses the formatter without
    knowing or caring which concrete type it is.
    """

    @abstractmethod
    def create_formatter(self) -> Formatter:
        """Factory method — subclasses decide which Formatter to produce."""
        ...

    def export(self, columns: list[str], rows: list[list[str]]) -> str:
        """Uses the product without referencing any concrete class."""
        formatter = self.create_formatter()
        return formatter.format_table(columns, rows)


# ---------------------------------------------------------------------------
# Concrete Creators
# ---------------------------------------------------------------------------

class CSVExporter(DataExporter):
    def create_formatter(self) -> Formatter:
        return CSVFormatter()


class MarkdownExporter(DataExporter):
    def create_formatter(self) -> Formatter:
        return MarkdownFormatter()


class HTMLExporter(DataExporter):
    def create_formatter(self) -> Formatter:
        return HTMLFormatter()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    columns = ["Name", "Role", "Team"]
    rows = [
        ["Alice",   "Engineer", "Platform"],
        ["Bob",     "Designer", "Product"],
        ["Charlie", "Manager",  "Ops"],
    ]

    exporters: list[DataExporter] = [
        CSVExporter(),
        MarkdownExporter(),
        HTMLExporter(),
    ]

    for exporter in exporters:
        print(f"--- {type(exporter).__name__} ---")
        print(exporter.export(columns, rows))
        print()
