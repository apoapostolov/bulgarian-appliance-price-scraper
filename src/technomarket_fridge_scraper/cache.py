from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass
class ApplianceMetadataCache:
    SCHEMA_VERSION = 2

    path: Path
    products: dict[str, dict[str, object]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "ApplianceMetadataCache":
        if not path.exists():
            return cls(path=path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            return cls(path=path)
        products = payload.get("products", {})
        return cls(path=path, products=products)

    def lookup(self, product_code: str, url: str) -> dict[str, object] | None:
        entry = self.products.get(product_code)
        if not entry:
            return None
        return {
            "detail_features": list(entry.get("detail_features", [])),
            "detail_specs": dict(entry.get("detail_specs", {})),
            "ean": entry.get("ean"),
        }

    def seed_from_rows(self, rows: list[dict[str, object]]) -> int:
        seeded = 0
        for row in rows:
            product_code = str(row.get("product_code") or "").strip()
            url = str(row.get("url") or "").strip()
            if not product_code or not url:
                continue
            detail_features = list(row.get("detail_features") or [])
            detail_specs = dict(row.get("detail_specs") or {})
            ean = row.get("ean")
            if not detail_features and not detail_specs and not ean:
                continue
            self.products[product_code] = {
                "url": url,
                "detail_features": detail_features,
                "detail_specs": detail_specs,
                "ean": ean,
            }
            seeded += 1
        return seeded

    def store(self, product_code: str, url: str, details: dict[str, object]) -> None:
        self.products[product_code] = {
            "url": url,
            "detail_features": list(details.get("detail_features", [])),
            "detail_specs": dict(details.get("detail_specs", {})),
            "ean": details.get("ean"),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "products": self.products,
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
