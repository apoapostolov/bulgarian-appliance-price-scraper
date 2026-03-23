from pathlib import Path

from technomarket_fridge_scraper.config import ApplianceProfile, Category, ScraperConfig
from technomarket_fridge_scraper.scraper import discover_appliance_categories


def test_discover_appliance_categories_merges_technopolis_children(monkeypatch, tmp_path):
    html = """
    <html>
      <body>
        <a href="/en/Domakinski-elektrouredi/Gotvarski-pechki/Plotove-za-vgrajdane/c/P11110201">Hobs</a>
        <a href="/en/Domakinski-elektrouredi/Gotvarski-pechki/Plotove-za-vgrajdane/Induction/c/P11110202">Induction hobs</a>
        <a href="/en/Kompyutarni-aksesoari/Slushalki-i-mikrofoni/Slushalki/c/P11020501">Headphones</a>
      </body>
    </html>
    """

    profile = ApplianceProfile(
        appliance_type="hob",
        hub_path="/en/Domakinski-elektrouredi/Gotvarski-pechki/Plotove-za-vgrajdane/c/P11110201",
        category_root_name="Hobs",
        category_name_prefix=None,
        category_texts=[],
        categories=[
            Category(
                path="/en/Domakinski-elektrouredi/Gotvarski-pechki/Plotove-za-vgrajdane/c/P11110201",
                name="Hobs",
            )
        ],
        output_prefix="bulgarian_appliance_price_scraper_technopolis_hobs",
        metadata_cache_path=Path(tmp_path / "cache.json"),
        in_stock_only=True,
        fetch_product_details=False,
    )
    config = ScraperConfig(
        store="technopolis",
        base_url="https://www.technopolis.bg",
        user_agent="Mozilla/5.0",
        output_dir=Path(tmp_path),
        render_timeout_ms=15000,
        chromium_binaries=["chromium"],
        appliance_type="hob",
        profile=profile,
        categories=[],
    )

    monkeypatch.setattr("technomarket_fridge_scraper.scraper.render_dom_chromium", lambda *args, **kwargs: html)

    categories = discover_appliance_categories(config)
    assert [category.path for category in categories] == [
        "/en/Domakinski-elektrouredi/Gotvarski-pechki/Plotove-za-vgrajdane/c/P11110201",
        "/en/Domakinski-elektrouredi/Gotvarski-pechki/Plotove-za-vgrajdane/Induction/c/P11110202",
    ]
