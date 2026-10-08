"""Provider-independent product input."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    source: str
    source_id: str
    name: str
    category: str
    source_url: str
    observed_at: str
    is_mock: bool
