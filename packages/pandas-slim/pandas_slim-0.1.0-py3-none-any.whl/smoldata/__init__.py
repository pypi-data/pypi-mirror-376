"""SmolData - A Python library to reduce pandas DataFrame memory usage."""

from .core import (
    reduce_mem_usage,
    check_if_integer,
    benchmark_methods,
    MemoryOptimizer
)

__version__ = "0.1.0"
__author__ = "Remi Ounadjela"
__email__ = "contact@example.com"

__all__ = [
    "reduce_mem_usage",
    "check_if_integer", 
    "benchmark_methods",
    "MemoryOptimizer"
]