from __future__ import annotations

import json

from technomarket_fridge_scraper.cache import ApplianceMetadataCache
from technomarket_fridge_scraper.config import ApplianceProfile, ScraperConfig
from technomarket_fridge_scraper.scraper import enrich_with_product_details


def test_seed_from_rows(tmp_path):
    cache = ApplianceMetadataCache.load(tmp_path / "cache.json")
    seeded = cache.seed_from_rows(
        [
            {
                "product_code": "09220645",
                "url": "https://example.test/product",
                "detail_features": ["Model: CBNsfc 572i"],
                "detail_specs": {"model": "CBNsfc 572i"},
                "ean": "4016803132744",
            }
        ]
    )
    assert seeded == 1
    assert cache.lookup("09220645", "https://example.test/product") == {
        "detail_features": ["Model: CBNsfc 572i"],
        "detail_specs": {"model": "CBNsfc 572i"},
        "ean": "4016803132744",
    }


def test_enrich_with_product_details_uses_latest_export_cache(monkeypatch, tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    export_path = output_dir / "bulgarian_appliance_price_scraper_technopolis_refrigerators_20260323_101010.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "product_code": "09220645",
                    "url": "https://example.test/technopolis",
                    "detail_features": ["Model: CBNsfc 572i"],
                    "detail_specs": {"model": "CBNsfc 572i"},
                    "ean": "4016803132744",
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    profile = ApplianceProfile(
        appliance_type="refrigerator",
        hub_path="/en/Domakinski-elektrouredi/Hladilnici/c/P111003",
        category_root_name="Refrigerators",
        category_name_prefix=None,
        category_texts=[],
        categories=[],
        output_prefix="bulgarian_appliance_price_scraper_technopolis_refrigerators",
        metadata_cache_path=tmp_path / "cache.json",
        in_stock_only=True,
        fetch_product_details=True,
    )
    config = ScraperConfig(
        store="technopolis",
        base_url="https://www.technopolis.bg",
        user_agent="Mozilla/5.0",
        output_dir=output_dir,
        render_timeout_ms=15000,
        chromium_binaries=["chromium"],
        appliance_type="refrigerator",
        profile=profile,
        categories=[],
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("detail fetch should not be called for cached products")

    monkeypatch.setattr("technomarket_fridge_scraper.scraper.render_dom_chromium", fail_if_called)

    rows = [
        {
            "store": "technopolis",
            "category_name": "Refrigerators",
            "category_path": "/en/Domakinski-elektrouredi/Hladilnici/c/P111003",
            "page": 1,
            "product_code": "09220645",
            "sku": "09220645",
            "brand": "LIEBHERR",
            "name": "CBNsfc 572i",
            "title": "LIEBHERR CBNsfc 572i",
            "url": "https://example.test/technopolis",
            "in_stock": True,
            "price_bgn": 188900,
            "price_eur": 965.55,
            "old_price_bgn": None,
            "old_price_eur": None,
            "energy_class": "C",
            "specs": {},
            "detail_features": [],
            "detail_specs": {},
            "ean": None,
        }
    ]

    enriched = enrich_with_product_details(config, rows)
    assert enriched[0]["ean"] == "4016803132744"
    assert enriched[0]["detail_specs"] == {"model": "CBNsfc 572i"}
    assert enriched[0]["detail_features"] == ["Model: CBNsfc 572i"]
