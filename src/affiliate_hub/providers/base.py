from typing import Protocol

from affiliate_hub.models import Product


class ProductProvider(Protocol):
    def fetch(self) -> list[Product]: ...
