import json

from bs4 import BeautifulSoup

from technomarket_fridge_scraper.stores.zora import (
    extract_product_details,
    extract_products,
    extract_total_pages,
)


LISTING_HTML = """
<html>
  <body>
    <div class="_product-inner">
      <div class="_product-name">
        <h3>
          <a href="https://zora.bg/product/fmo-2063w">Микровълнова фурна Finlux FMO-2063W , 20 Литри, 700 W</a>
        </h3>
      </div>
      <div class="_product-details-properties">
        <ul>
          <li><span class="_product-details-properties-title">Обем/Вместимост, литри:</span><span class="_product-details-properties-value">20</span></li>
          <li><span class="_product-details-properties-title">Гаранция:</span><span class="_product-details-properties-value">24 м.</span></li>
          <li><span class="_product-details-properties-title">Мощност  W:</span><span class="_product-details-properties-value">700</span></li>
        </ul>
      </div>
      <input data-product='{"id":144916,"name":"Микровълнова фурна Finlux FMO-2063W , 20 Литри, 700 W","image":"https://cdncloudcart.com/402/products/images/144916/mikrovalnova-furna-finlux-fmo-2063w-655341779b51a_150x150.png?1699955119","link":"https://zora.bg/product/fmo-2063w","price":"<span data-nosnippet class=\\\"bgn2eur-primary-currency\\\">59,<sup class=\\\"price-decimals\\\">99</sup> €</span><span data-nosnippet class=\\\"bgn2eur-secondary-currency\\\">117,<sup class=\\\"price-decimals\\\">33</sup> лв.</span>"}'/>
      <a href="https://zora.bg/product/fmo-2063w">Купи</a>
      <a href="https://zora.bg/product/fmo-2063w">Прочети още</a>
    </div>
    <div class="pagination">
      <a href="/category/mikrovalnovi-furni?page=1">1</a>
      <a href="/category/mikrovalnovi-furni?page=2">2</a>
      <a href="/category/mikrovalnovi-furni?page=3">3</a>
    </div>
  </body>
</html>
"""


DETAIL_STATE = {
    "type": "product",
    "id": 144916,
    "parameter_id": 144916,
    "name": "Микровълнова фурна Finlux FMO-2063W , 20 Литри, 700 W",
    "brand": "Finlux",
    "sku": "FMO-2063W",
    "barcode": "1058000000000",
    "price": 71.59,
    "discount_price": 59.99,
    "currency": "EUR",
    "variants": [{"id": 1, "availability": "in_stock", "enable_sell": True, "text_key": "", "price": "71.59", "discount_price": "59.99"}],
}


DETAIL_HTML = f"""
<html>
  <head>
    <meta name="description" content="Размери: Широчина-45см.Височина-26см.Дълбочина -35 см.">
  </head>
  <body>
    <script id="js-cc-page-data" type="text/javascript">var cc_page_data = {json.dumps(DETAIL_STATE, ensure_ascii=False)};</script>
    <section id="product-characteristics" class="item-nav">
      <div class="_product-details-properties-wrapper hidden-sm hidden-xs">
        <div class="_product-details-properties">
          <ul>
            <li><span class="_product-details-properties-title">Функции:</span><span class="_product-details-properties-value"><a href="javascript:void(0);">5 степени на мощност</a></span></li>
            <li><span class="_product-details-properties-title">Гаранция:</span><span class="_product-details-properties-value"><a href="javascript:void(0);">24 м.</a></span></li>
            <li><span class="_product-details-properties-title">Мощност  W:</span><span class="_product-details-properties-value"><a href="javascript:void(0);">700</a></span></li>
          </ul>
        </div>
      </div>
    </section>
  </body>
</html>
"""


def test_extract_total_pages_zora():
    soup = BeautifulSoup(LISTING_HTML, "html.parser")
    assert extract_total_pages(soup) == 3


def test_extract_products_zora():
    rows = extract_products(
        html=LISTING_HTML,
        base_url="https://zora.bg",
        category_name="Microwaves",
        category_path="/category/mikrovalnovi-furni",
        page=1,
        in_stock_only=True,
    )
    assert len(rows) == 1
    row = rows[0].to_dict()
    assert row["store"] == "zora"
    assert row["product_code"] == "144916"
    assert row["price_eur"] == 59.99
    assert row["price_bgn"] == 117.33
    assert row["energy_class"] is None
    assert row["specs"]["capacity_l"] == 20
    assert row["specs"]["warranty_months"] == 24
    assert row["specs"]["power_w"] == 700


def test_extract_products_zora_preserves_decimal_bgn():
    html = """
    <html>
      <body>
        <div class="_product-inner">
          <div class="_product-name">
            <h3>
              <a href="https://zora.bg/product/cdmo-2065b">Микровълнова фурна Crown CDMO-2065B , 20 , 20 Литри, 700 W</a>
            </h3>
          </div>
          <input data-product='{"id":166479,"name":"Микровълнова фурна Crown CDMO-2065B , 20 , 20 Литри, 700 W","price":"<span data-nosnippet class=\\\"bgn2eur-primary-currency\\\">71,<sup class=\\\"price-decimals\\\">58</sup> €</span><span data-nosnippet class=\\\"bgn2eur-secondary-currency\\\">140,<sup class=\\\"price-decimals\\\">00</sup> лв.</span>"}'/>
          <a href="https://zora.bg/product/cdmo-2065b">Купи</a>
        </div>
      </body>
    </html>
    """
    rows = extract_products(
        html=html,
        base_url="https://zora.bg",
        category_name="Microwaves",
        category_path="/category/mikrovalnovi-furni",
        page=1,
        in_stock_only=True,
    )
    assert len(rows) == 1
    row = rows[0].to_dict()
    assert row["price_bgn"] == 140.0
    assert row["price_eur"] == 71.58


def test_extract_product_details_zora():
    details = extract_product_details(DETAIL_HTML)
    assert details["ean"] == "1058000000000"
    assert details["brand"] == "Finlux"
    assert details["sku"] == "FMO-2063W"
    assert details["energy_class"] is None
    assert details["detail_specs"]["power_w"] == 700
    assert details["detail_specs"]["warranty_months"] == 24
