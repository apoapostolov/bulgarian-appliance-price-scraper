from __future__ import annotations

import json

from technobulgarian_scraper import mcp_server


def _write_export(path, rows):
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def test_latest_export_payloads_and_match_scoring(tmp_path):
    technomarket_export = tmp_path / "technobulgarian_scraper_technomarket_refrigerators_20260323_101010.json"
    technopolis_export = tmp_path / "technobulgarian_scraper_technopolis_refrigerators_20260323_101011.json"
    _write_export(
        technomarket_export,
        [
            {
                "store": "technomarket",
                "product_code": "09220645",
                "sku": "09220645",
                "brand": "LIEBHERR",
                "name": "CBNsfc 572i",
                "title": "LIEBHERR CBNsfc 572i",
                "ean": "4016803132744",
                "price_bgn": 188900,
                "url": "https://example.test/technomarket",
                "specs": {"width": "60 cm"},
                "detail_specs": {"model": "CBNsfc 572i"},
            }
        ],
    )
    _write_export(
        technopolis_export,
        [
            {
                "store": "technopolis",
                "product_code": "12345678",
                "sku": "12345678",
                "brand": "LIEBHERR",
                "name": "CBNsfc 572i",
                "title": "LIEBHERR CBNsfc 572i",
                "ean": "4016803132744",
                "price_bgn": 192900,
                "url": "https://example.test/technopolis",
                "specs": {},
                "detail_specs": {"model": "CBNsfc 572i"},
            }
        ],
    )

    payloads = mcp_server._latest_export_payloads(tmp_path)
    assert [payload["store"] for payload in payloads] == ["technomarket", "technopolis"]
    assert [payload["appliance_type"] for payload in payloads] == ["refrigerator", "refrigerator"]
    assert payloads[0]["row_count"] == 1

    exact_ean_score, exact_ean_reason = mcp_server._match_score(payloads[0]["rows"][0], "4016803132744")
    exact_sku_score, exact_sku_reason = mcp_server._match_score(payloads[0]["rows"][0], "09220645")
    title_score, title_reason = mcp_server._match_score(payloads[0]["rows"][0], "LIEBHERR CBNsfc 572i")

    assert (exact_ean_score, exact_ean_reason) == (100, "exact_ean")
    assert (exact_sku_score, exact_sku_reason) == (90, "exact_sku")
    assert (title_score, title_reason) == (80, "exact_title")


def test_latest_export_for_store_type(tmp_path):
    export = tmp_path / "technobulgarian_scraper_zora_microwaves_20260323_111111.json"
    _write_export(
        export,
        [
            {
                "store": "zora",
                "product_code": "ABC123",
                "sku": "ABC123",
                "brand": "LG",
                "name": "MH6535GIS",
                "title": "LG MH6535GIS",
                "ean": "8806098431234",
                "price_bgn": 24900,
                "url": "https://example.test/zora",
                "specs": {},
                "detail_specs": {},
            }
        ],
    )

    latest = mcp_server._latest_export_for_store_type(tmp_path, "zora", "microwave")
    assert latest is not None
    assert latest["file"] == export.name
    assert latest["appliance_type"] == "microwave"
