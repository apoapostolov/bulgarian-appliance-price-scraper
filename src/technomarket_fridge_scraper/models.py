from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ApplianceProduct:
    store: str
    category_name: str
    category_path: str
    page: int
    product_code: str
    sku: str
    brand: str
    name: str
    title: str
    url: str
    in_stock: bool
    price_bgn: int | float | None
    price_eur: int | float | None
    old_price_bgn: int | float | None
    old_price_eur: int | float | None
    energy_class: str | None
    specs: dict[str, object]
    detail_features: list[str]
    detail_specs: dict[str, object]
    ean: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FridgeProduct = ApplianceProduct
