from __future__ import annotations

import os
from urllib.parse import urljoin

import pytest
import requests
from bs4 import BeautifulSoup

from technomarket_fridge_scraper.parser import extract_products as technomarket_extract_products
from technomarket_fridge_scraper.parser import extract_total_pages as technomarket_extract_total_pages
from technomarket_fridge_scraper.discovery import discover_categories as technomarket_discover_categories
from technomarket_fridge_scraper.render import render_dom_chromium
from technomarket_fridge_scraper.stores.technopolis import (
    discover_categories_from_html as technopolis_discover_categories,
    extract_products as technopolis_extract_products,
    extract_total_pages as technopolis_extract_total_pages,
)
from technomarket_fridge_scraper.stores.zora import (
    discover_categories_from_html as zora_discover_categories,
    extract_products as zora_extract_products,
    extract_total_pages as zora_extract_total_pages,
)


RUN_LIVE_SCRAPER_TESTS = os.getenv("RUN_LIVE_SCRAPER_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_LIVE_SCRAPER_TESTS,
    reason="Set RUN_LIVE_SCRAPER_TESTS=1 to run live website scraper smoke tests.",
)


def test_live_technomarket_refrigerator_smoke():
    base_url = "https://www.technomarket.bg"
    hub_path = "/hladilnitzi"
    hub_html = requests.get(urljoin(base_url, hub_path), timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
    categories = technomarket_discover_categories(
        hub_html,
        {
            "С долна камера",
            "С горна камера",
            "Side By Side",
            "С една врата",
            "Хладилни витрини",
            "Фризери",
            "Всички хладилници",
            "Винарни",
        },
    )
    assert categories

    category_html = requests.get(
        urljoin(base_url, categories[0].path),
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    ).text
    soup = BeautifulSoup(category_html, "html.parser")
    assert technomarket_extract_total_pages(soup) >= 1
    rows = technomarket_extract_products(
        html=category_html,
        base_url=base_url,
        category_name=categories[0].name,
        category_path=categories[0].path,
        page=1,
        in_stock_only=True,
    )
    assert rows


def test_live_technopolis_refrigerator_smoke():
    base_url = "https://www.technopolis.bg"
    hub_url = urljoin(base_url, "/en/Domakinski-elektrouredi/Hladilnici/c/P111003")
    hub_html = render_dom_chromium(hub_url, 15000, ["chromium", "chromium-browser", "google-chrome", "chrome"])
    soup = BeautifulSoup(hub_html, "html.parser")
    categories = technopolis_discover_categories(
        hub_html,
        {
            "Refrigerator bottom freezer",
            "Refrigerator upper freezer",
            "Refrigerators Side by Side",
            "One Door Refrigerators",
            "Minibar",
            "Build-In Refrigerators",
            "Wine coolers",
            "Show windows",
        },
    )
    assert categories
    assert technopolis_extract_total_pages(soup) >= 1
    rows = technopolis_extract_products(
        html=hub_html,
        base_url=base_url,
        category_name="Refrigerators",
        category_path="/en/Domakinski-elektrouredi/Hladilnici/c/P111003",
        page=1,
        in_stock_only=True,
    )
    assert rows


def test_live_zora_microwave_smoke():
    base_url = "https://zora.bg"
    category_url = urljoin(base_url, "/category/mikrovalnovi-furni")
    category_html = requests.get(category_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(category_html, "html.parser")
    categories = zora_discover_categories(category_html, {"Микровълнови фурни", "Микровълнови"})
    assert categories
    assert zora_extract_total_pages(soup) >= 1
    rows = zora_extract_products(
        html=category_html,
        base_url=base_url,
        category_name=categories[0].name,
        category_path=categories[0].path,
        page=1,
        in_stock_only=True,
    )
    assert rows
