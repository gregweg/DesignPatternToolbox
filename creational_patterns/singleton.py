"""
Singleton — Creational Design Pattern

Ensures a class has at most one instance and provides a global access point
to that instance. Useful for resources that are expensive to create, represent
a system-wide state, or must be strictly unique.

Key characteristics:
  - Only one instance exists per process (or per scope in test environments)
  - Global access via the class itself — no need to pass the instance around
  - Lazy initialisation — the instance is created on first access, not on import

Thread safety note:
  Basic __new__ overrides are not thread-safe. The thread-safe variant below
  uses double-checked locking: a lock is only acquired on first initialisation,
  so subsequent accesses pay no synchronisation cost.

Contrast with module-level globals: a module-level variable is also a
singleton of sorts, but provides no control over initialisation order,
no lazy creation, and no swap-out mechanism for tests.
"""

from __future__ import annotations
import os
import threading
from typing import Any


# ---------------------------------------------------------------------------
# Basic Singleton — fine for single-threaded applications
# ---------------------------------------------------------------------------

class _Meta(type):
    """Metaclass that enforces a single instance per class."""
    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AppConfig(metaclass=_Meta):
    """
    Application configuration singleton.

    Reads settings from environment variables on first construction.
    Every subsequent call to AppConfig() returns the same, already-initialised
    object — __init__ is called again by Python but the guard exits early.
    """

    def __init__(self) -> None:
        if hasattr(self, "_initialised"):
            return
        self._initialised = True
        self.debug: bool      = os.getenv("DEBUG", "false").lower() == "true"
        self.db_url: str      = os.getenv("DATABASE_URL", "sqlite:///local.db")
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

    def __repr__(self) -> str:
        return (
            f"AppConfig(debug={self.debug}, "
            f"db_url={self.db_url!r}, "
            f"max_retries={self.max_retries})"
        )


# ---------------------------------------------------------------------------
# Thread-safe Singleton — use for multi-threaded applications
# ---------------------------------------------------------------------------

class _ThreadSafeMeta(type):
    """Metaclass with double-checked locking for thread-safe initialisation."""
    _instances: dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                # second check inside the lock — another thread may have
                # created the instance between the outer check and acquiring the lock
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConnectionPool(metaclass=_ThreadSafeMeta):
    """
    Thread-safe connection pool singleton.

    In production code this would manage a pool of live database connections.
    Here it demonstrates that concurrent construction still yields one instance.
    """

    def __init__(self) -> None:
        if hasattr(self, "_initialised"):
            return
        self._initialised = True
        self._pool_size: int     = int(os.getenv("POOL_SIZE", "5"))
        self._available: list[str] = [f"conn-{i}" for i in range(self._pool_size)]

    @property
    def pool_size(self) -> int:
        return self._pool_size

    def acquire(self) -> str | None:
        return self._available.pop() if self._available else None

    def release(self, conn: str) -> None:
        self._available.append(conn)

    def __repr__(self) -> str:
        return f"ConnectionPool(size={self._pool_size}, available={len(self._available)})"


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Basic singleton — both variables point to the same object
    cfg1 = AppConfig()
    cfg2 = AppConfig()
    print(f"Same AppConfig instance: {cfg1 is cfg2}")   # True
    print(cfg1)

    # Thread-safe singleton: 20 threads all call ConnectionPool() concurrently
    instances: list[ConnectionPool] = []

    def make_pool() -> None:
        instances.append(ConnectionPool())

    threads = [threading.Thread(target=make_pool) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    unique_ids = {id(i) for i in instances}
    print(f"\n{len(instances)} threads, {len(unique_ids)} unique instance(s)")  # 1

    # State is shared — acquiring through one reference is visible through another
    pool_a = ConnectionPool()
    pool_b = ConnectionPool()
    conn = pool_a.acquire()
    print(f"\nAcquired via pool_a: {conn}")
    print(f"pool_b reflects same state: {pool_b}")
