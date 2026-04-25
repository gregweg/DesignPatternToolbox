# Creational Patterns

Patterns in this category are concerned with **how objects are created**. Their
primary goals are controlling instantiation logic, decoupling callers from
concrete classes, and making the creation of complex objects manageable.

Each pattern answers a distinct question:

| Pattern | Question answered |
|---|---|
| **Singleton** | How do I ensure only one instance ever exists? |
| **Factory Method** | How do I let subclasses decide which class to instantiate? |
| **Abstract Factory** | How do I create families of compatible objects without naming their classes? |
| **Builder** | How do I construct a complex object step by step? |
| **Prototype** | How do I create a new object by copying an existing one? |

> All files are self-contained. Run demos from the `creational_patterns/`
> directory: `python singleton.py`, `python factory_method.py`, etc.

---

## Singleton (`singleton.py`)

### Motivation
Some resources are expensive to construct, represent a system-wide state that
must be consistent everywhere, or are semantically required to be unique —
a configuration store, a connection pool, a logging sink. Having multiple
instances would waste resources or produce inconsistent behaviour.

Singleton ensures that no matter how many times a class is "constructed", every
caller receives the same, already-initialised object.

### When to Use
- A single shared instance is required by design (config, pool, cache)
- Construction is expensive and the result should be reused
- Global access is needed without passing the object through every call chain
- You need lazy initialisation (create on first use, not on import)

### Key Rules
- **Single instance** — controlled via a metaclass `_instances` dict
- **Guard in `__init__`** — `if hasattr(self, "_initialised"): return` prevents
  re-running setup when Python calls `__init__` on the existing instance
- **Thread safety** — use double-checked locking for multi-threaded code:
  check once outside the lock (fast path), re-check inside (safe path)
- **Test isolation** — clear `_instances` between tests to avoid cross-test state

### Structure

| Class | Role |
|---|---|
| `_Meta` | Metaclass; enforces single instance (single-threaded) |
| `AppConfig` | Config singleton; reads from environment on first construction |
| `_ThreadSafeMeta` | Metaclass with double-checked locking (multi-threaded) |
| `ConnectionPool` | Thread-safe pool singleton; demonstrates concurrent safety |

---

## Factory Method (`factory_method.py`)

### Motivation
A class needs to produce objects, but the exact type should vary by context.
Hardcoding `CSVFormatter()` inside `DataExporter.export()` means changing the
format requires changing the exporter. Passing the type as a parameter leaks
construction knowledge into caller code.

Factory Method moves the decision to a method that subclasses override. The
base class contains the algorithm (`export()`); each subclass answers only the
"what to create" question by overriding `create_formatter()`. Adding a new
format means adding a new subclass — not touching existing code.

### When to Use
- A class must produce objects but the exact type should be decided by subclasses
- You want to follow the Open/Closed Principle: extend by adding a subclass,
  not by modifying existing classes
- The construction logic itself is trivial; the variation is in the type chosen

### Key Rules
- **Creator defines the interface** — `DataExporter.export()` calls
  `self.create_formatter()` without knowing which concrete type it returns
- **Subclasses override the factory method only** — all other behaviour is inherited
- **Product implements a common interface** — `Formatter`; the template method
  never casts or branches on the product type
- **Not just for subclassing** — the factory method can have a sensible default
  implementation that subclasses optionally override

### Structure

| Concept | Implementation |
|---|---|
| Product interface | `Formatter` — `format_header`, `format_row`, `format_footer`, `format_table` |
| Concrete products | `CSVFormatter`, `MarkdownFormatter`, `HTMLFormatter` |
| Creator | `DataExporter` — `export()` template, `create_formatter()` factory method |
| Concrete creators | `CSVExporter`, `MarkdownExporter`, `HTMLExporter` |

---

## Abstract Factory (`abstract_factory.py`)

### Motivation
A UI system supports multiple visual themes. `LightButton` and `DarkDialog`
must never be mixed — they are designed as a coherent family. If client code
directly instantiates `LightButton(...)` and `DarkDialog()`, a theme change
requires hunting down every instantiation site.

Abstract Factory groups the creation of a whole product family behind one
interface. The client receives a factory, calls `create_button()`,
`create_dialog()`, etc., and never names a concrete class. Swapping
`LightThemeFactory` for `DarkThemeFactory` switches the entire UI in one place.

### When to Use
- Objects come in families that must be used together (theme, database dialect,
  platform-specific widgets)
- You want to enforce that products from different families are never mixed
- You want to swap the entire family without touching client code

### Key Rules
- **Client depends only on abstract factory and product interfaces** — no
  `isinstance` checks, no concrete class names in client code
- **Products within a family are compatible by construction** — they share
  visual language, API conventions, or protocol compatibility
- **One concrete factory per variant** — `LightThemeFactory`, `DarkThemeFactory`
- **Abstract Factory is a group of coordinated Factory Methods** — each
  creation method is effectively a Factory Method for its product type

### Structure

| Concept | Implementation |
|---|---|
| Abstract products | `Button`, `Dialog`, `Checkbox` |
| Abstract factory | `UIFactory` — `create_button`, `create_dialog`, `create_checkbox` |
| Light family | `LightButton`, `LightDialog`, `LightCheckbox`, `LightThemeFactory` |
| Dark family | `DarkButton`, `DarkDialog`, `DarkCheckbox`, `DarkThemeFactory` |
| Client | `render_checkout_screen(factory: UIFactory)` — no concrete types referenced |

---

## Builder (`builder.py`)

### Motivation
An `HttpRequest` has a URL, method, headers, query params, a body, a timeout,
and a retry count. A constructor with all of these becomes unreadable the
moment there are more than three arguments, and most combinations of optional
parameters are valid — leading to a telescoping constructor problem.

Builder makes construction explicit and readable. Each step configures one
concern. Steps chain together fluently so the construction reads almost like
a sentence. An optional Director encodes frequently-used shapes (e.g. "an
authenticated JSON request with standard timeout and retries") so boilerplate
does not spread across the codebase.

### When to Use
- The object has many optional or order-sensitive construction parameters
- Different representations of the same concept can be built from the same steps
- You want to prevent partially-constructed objects from being used
- You want named, readable construction (`bearer_auth`, `json_content`) instead
  of positional arguments

### Key Rules
- **Product retrieved only via `build()`** — never expose an incomplete object
- **Each step returns `self`** — enables fluent chaining
- **Validate in step methods**, not in `build()` — fail fast, at the point where
  an invalid value is supplied
- **Director is optional** — useful when the same sequence appears repeatedly;
  omit it when clients always need full control

### Structure

| Concept | Implementation |
|---|---|
| Product | `HttpRequest` — immutable once built (dataclass) |
| Builder | `HttpRequestBuilder` — step methods + `build()` |
| Convenience functions | `GET()`, `POST()`, `PUT()`, `PATCH()`, `DELETE()` — readable entry points |
| Director | `ApiClientDirector` — recipes for list, create, and update requests |

---

## Prototype (`prototype.py`)

### Motivation
A marketing system maintains master email templates. Each outbound message is
the same template with recipient-specific fields filled in. Rebuilding the
full template object for each recipient is wasteful; passing the master around
risks accidental mutation.

Prototype solves this by letting the master clone itself on demand. The clone
is a completely independent copy — modifying it never affects the master.
A registry stores named masters; callers check out copies without needing to
know the concrete class or its constructor.

### When to Use
- New instances differ only slightly from an existing, already-configured object
- Construction is expensive and a pre-warmed baseline should be reused
- The concrete class of the object is not known at the point of creation
- You want a catalogue of named, pre-configured objects (prototype registry)

### Key Rules
- **Always deep copy for mutable prototypes** — shallow copy leaves nested
  collections shared between the clone and the original
- **The prototype controls its own cloning** — `clone()` is a method on the
  object, not an external utility
- **Registry returns copies, never the master** — the master must remain pristine
- **Clone, then modify** — the common workflow: `obj = registry.get("name")`,
  then customise `obj` freely

### Structure

| Concept | Implementation |
|---|---|
| Prototype mixin | `Cloneable` — `clone()` backed by `copy.deepcopy` |
| Email prototype | `EmailTemplate` — clones and fills placeholders via `personalise()` |
| Dashboard prototype | `DashboardLayout` — mutable layout cloned per user |
| Registry | `PrototypeRegistry` — stores masters, returns deep copies via `get()` |
