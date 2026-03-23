from technomarket_fridge_scraper.parser import extract_products, extract_total_pages
from bs4 import BeautifulSoup


SAMPLE_HTML = """
<html>
  <body>
    <div class="current-pages">
      <a class="active" href="/produkti/hladilnitzi-dolna-kamera">1</a>
      <a href="/produkti/hladilnitzi-dolna-kamera?page=2">2</a>
      <a href="/produkti/hladilnitzi-dolna-kamera?page=8">8</a>
    </div>
    <tm-product-item data-product="09220872">
      <a class="product-image" href="/hladilnitzi/gorenje-rk416eps4-09220872"></a>
      <div class="overview">
        <a class="title" data-brand="GORENJE" href="/hladilnitzi/gorenje-rk416eps4-09220872">
          <span class="type">ХЛАДИЛНИК</span>
          <span class="brand">GORENJE</span>
          <span class="name">RK416EPS4</span>
        </a>
        <div class="specifications">
          <div class="line"><span class="label">Продукт</span><span class="value">Хладилник</span></div>
        </div>
      </div>
      <div class="action">
        <div class="price">
          <span>
            <tm-price><span class="bgn_price">663.03 лв.</span><span class="euro_price">1.022,07 €</span></tm-price>
          </span>
        </div>
        <div class="action-buttons">
          <button class="tm-button gi2 add-cart" data-action="addCart"></button>
        </div>
      </div>
    </tm-product-item>
  </body>
</html>
"""


def test_extract_total_pages():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    assert extract_total_pages(soup) == 8


def test_extract_products():
    rows = extract_products(
        html=SAMPLE_HTML,
        base_url="https://www.technomarket.bg",
        category_name="Хладилници с долна камера",
        category_path="/produkti/hladilnitzi-dolna-kamera",
        page=1,
        in_stock_only=True,
    )
    assert len(rows) == 1
    row = rows[0].to_dict()
    assert row["store"] == "technomarket"
    assert row["product_code"] == "09220872"
    assert row["sku"] == "09220872"
    assert row["brand"] == "GORENJE"
    assert row["name"] == "RK416EPS4"
    assert row["price_bgn"] == 66303
    assert row["price_eur"] == 1022.07
    assert row["old_price_bgn"] is None
    assert row["old_price_eur"] is None
    assert row["in_stock"] is True
    assert row["specs"] == {}
