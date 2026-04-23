# Domain Modeling Patterns

Patterns in this category are concerned with accurately representing complex business
domains in code. Their primary goals are **consistency**, **encapsulation of business
rules**, and **meaningful vocabulary** that maps directly to the problem domain.

These patterns are complementary and commonly used together. The dependency direction is:

```
Specification ──┐
Repository    ──┤──► Entity ──► Value Object
Aggregate     ──┘
Domain Event  (emitted by Aggregate Roots; consumed externally)
```

> All files import from within this folder. Run demos from the `domain_modeling/`
> directory: `python value_object.py`, `python entity.py`, etc.

---

## Value Object (`value_object.py`)

### Motivation
Primitive types like `int` and `str` carry no domain meaning and no validation.
Passing a raw `int` as a price, a quantity, and a discount in the same function
signature makes code error-prone and hard to read. Value Objects wrap these
primitives in domain-meaningful, self-validating types.

Because they have no identity, two Value Objects with the same attributes are
completely interchangeable — there is no meaningful difference between one instance
of `Money(1000)` and another.

### When to Use
- A concept is defined entirely by its attributes, not by an identity
- The value should be validated at construction time (invalid instances never exist)
- Operations on the value should produce new instances rather than mutating the original
- The concept appears repeatedly across the codebase (money, addresses, date ranges, emails)

### Key Rules
- **Immutable** — use `@dataclass(frozen=True)`; operations return new instances
- **Self-validating** — `__post_init__` rejects invalid construction
- **Equality by value** — all attributes equal means the objects are equal
- **No identity field** — no `id`, no `uuid`

### Structure

| Class | Represents |
|---|---|
| `Money` | Currency-aware monetary amount in cents |
| `Email` | Validated email address |
| `Address` | Postal address |
| `DateRange` | Inclusive date interval with overlap/contains helpers |

---

## Entity (`entity.py`)

### Motivation
Some domain objects have a life of their own. A customer is still the same customer
after changing their email address or shipping address. A product is still the same
product after a price update. Identity, not attributes, defines what something *is*.

Entities model this: they carry a unique, stable ID and mutate over time while remaining
"the same object" throughout their lifecycle.

### When to Use
- The object has a lifecycle — it is created, changes state, and may be deleted
- Two objects with identical attributes can still be meaningfully different things
- Business rules constrain which state transitions are allowed

### Key Rules
- **Identity by ID** — `__eq__` and `__hash__` use the ID only
- **Mutable** — state changes via explicit command methods
- **Invariant enforcement** — commands reject invalid transitions (e.g. reserving more stock than available)
- **Typed IDs** — `CustomerId`, `ProductId` prevent accidentally passing the wrong ID

### Structure

| Class | Identity | Key invariants |
|---|---|---|
| `Customer` | `CustomerId` | Cannot deactivate twice; name cannot be empty |
| `Product` | `ProductId` | Stock cannot go negative; restock/reserve quantities must be positive |

---

## Domain Event (`domain_event.py`)

### Motivation
When something meaningful happens in the domain, other parts of the system often need
to react — send a confirmation email, update analytics, alert a warehouse. Calling
those systems directly from the domain object creates tight coupling and makes the
domain logic responsible for concerns that belong elsewhere.

Domain Events decouple cause from effect. The emitter records what happened and raises
an event. Subscribers react independently, with no knowledge of each other.

### When to Use
- A business occurrence should trigger reactions in other parts of the system
- You want to keep domain logic free of infrastructure concerns (email, analytics, etc.)
- You need an audit trail of what happened and when
- You are building an event-driven or microservices architecture

### Key Rules
- **Immutable** — frozen dataclass; they are facts about the past
- **Past tense naming** — `OrderPlaced`, `CustomerRegistered`, `PaymentFailed`
- **Self-contained** — carry all data needed to understand what happened
- **Emitted by Aggregate Roots** — the root collects events; infrastructure publishes them

### Structure

| Concept | Implementation |
|---|---|
| Base event | `DomainEvent` — common envelope with `event_id` and `occurred_at` |
| Concrete events | `CustomerRegistered`, `OrderPlaced`, `PaymentProcessed`, `PaymentFailed`, `InventoryLow` |
| Dispatch | `EventBus` — registers handlers per event type, runs them concurrently |

---

## Repository (`repository.py`)

### Motivation
Domain objects should not know how they are persisted. If an `Order` or `Customer`
contains SQL queries or ORM calls, the domain logic becomes inseparable from the
database, making it difficult to test and impossible to swap the storage mechanism.

The Repository pattern introduces a collection-like interface between the domain and
persistence. The domain declares what it needs (a `Protocol`), and infrastructure
provides the concrete implementation. Swapping from in-memory to Postgres requires
no changes to domain code.

### When to Use
- You want to test domain logic without a real database
- You may need to swap the persistence mechanism later
- You want to keep domain objects free of infrastructure concerns
- You are working with Aggregate Roots that need to be fetched and saved

### Key Rules
- **Operates on Aggregate Roots only** — never saves inner entities or value objects directly
- **Interface in the domain layer** — defined as a `Protocol`; implementations live in infrastructure
- **Collection-like interface** — `add`, `get`, `find_*`, `remove`
- **One repository per Aggregate Root** — `CustomerRepository`, `ProductRepository`, not a generic `Repository`

### Structure

| Concept | Implementation |
|---|---|
| Domain contract | `CustomerRepository`, `ProductRepository` (`Protocol`) |
| Test/demo implementation | `InMemoryCustomerRepository`, `InMemoryProductRepository` |
| Domain service | `transfer_stock()` — depends only on the `Protocol`, not the implementation |

---

## Specification (`specification.py`)

### Motivation
Business rules like "a product is promotable if it is in stock, costs under $20, and
is not discontinued" can be scattered across service methods, buried in `if` chains,
or duplicated wherever they are needed. When the rule changes, every copy must be found
and updated.

The Specification pattern encapsulates each business rule as a named, composable object.
Rules are combined with `&`, `|`, and `~` to form complex expressions that read like
business language and can be tested in isolation.

### When to Use
- The same business rule is evaluated in multiple places (filtering, validation, UI hints)
- Business rules are complex or frequently composed in different combinations
- You want to name and test each rule independently
- Rules may need to be translated into queries (SQL WHERE clauses, search filters)

### Key Rules
- **One class per rule**, named after the business concept
- **Compose with operators** — `&` (AND), `|` (OR), `~` (NOT) produce new specifications
- **Combinators are private** (`_And`, `_Or`, `_Not`) — callers use only operators
- **Single method** — `is_satisfied_by(candidate) -> bool`

### Structure

| Class | Rule |
|---|---|
| `InStock` | `stock > 0` |
| `LowStock` | `stock <= threshold` |
| `PriceAtMost` | `price.amount <= ceiling` |
| `PriceAtLeast` | `price.amount >= floor` |
| `NameContains` | case-insensitive keyword in name |
| `satisfying()` | helper that filters a list using any specification |

---

## Aggregate (`aggregate.py`)

### Motivation
In complex domains, entities reference other entities, which reference others, creating
deeply interconnected graphs. When multiple parts of the system can reach in and mutate
deeply nested objects independently, enforcing business rules becomes impossible —
nothing owns consistency.

The Aggregate pattern draws a **consistency boundary** around a cluster of related
entities and value objects, designating one as the **Aggregate Root**. All mutations
pass through the root, which enforces invariants and emits domain events. Persistence
operates at the root level only, so no external code can silently modify children.

### When to Use
- Business rules span multiple related entities that must stay consistent together
- You need to prevent external code from mutating child entities directly
- Deleting the root should naturally cascade to all its children
- Cross-aggregate references should travel by key (an ID), not by object reference

### Key Rules
- The **Aggregate Root** is the only public mutation surface
- **Inner entities** are never referenced from outside the boundary
- **Value Objects** are immutable and identity-free (e.g. `Money`, `Address`)
- **Domain Events** are facts emitted by the root describing what changed
- **Repository** persists the root only — never individual child entities
- Navigation properties exist only within an aggregate; cross-aggregate links use keys

### Structure

| Concept | Implementation |
|---|---|
| Aggregate Root | `Order` |
| Inner Entity | `_OrderLine` (prefixed `_`; not part of the public API) |
| Value Objects | `Money`, `OrderId` |
| Domain Events | `OrderItemAdded`, `OrderPlaced`, `OrderCancelled` |
| Repository | `OrderRepository` (`Protocol`; operates on `Order` only) |
| Cross-aggregate ref | `sku: str` in `_OrderLine` — Product is a separate aggregate |

`Order.lines` returns an immutable `tuple` snapshot so callers can read child data
without being able to mutate the aggregate's internal state.
