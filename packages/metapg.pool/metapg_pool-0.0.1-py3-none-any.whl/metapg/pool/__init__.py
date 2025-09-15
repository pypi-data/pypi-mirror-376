"""
metapg.pool - Connection pool for PostgreSQL databases.

A high-performance async and sync connection pool built on psycopg3.
"""

from metapg.pool.pool import (
    close_all_pools,
    close_pool,
    connection,
    cursor,
    get_pool,
    init_pool,
    transaction,
)

from .config import DatabaseConfig

__version__ = "0.0.1"
__all__ = [
    "close_all_pools",
    "close_pool",
    "connection",
    "cursor",
    "get_pool",
    "init_pool",
    "transaction",
    "DatabaseConfig",
]
