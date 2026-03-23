from technomarket_fridge_scraper.details import extract_product_details


SAMPLE_DETAIL_HTML = """
<html>
  <body>
    <div class="collapsible paddet specifications" id="specifications">
      <div class="collapsed-content">
        <table>
          <tbody>
            <tr><td class="label">Ширина на уреда</td><td><span>Над 50 И До 60 См</span></td></tr>
            <tr><td class="label">Височина на уреда</td><td><span>Над 100 И До 170 См</span></td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="collapsible paddet" id="basics">
      <div class="collapsed-content">
        <div class="product-basic fr">
          <ul>
            <li><span class="icon-check"></span> КОМБИНИРАН ХЛАДИЛНИК </li>
            <li><span class="icon-check"></span> ОБЕМ НА ФРИЗЕРНА ЧАСТ: 71 л. </li>
          </ul>
        </div>
        <tm-pointandplace ean="3838782766541"></tm-pointandplace>
      </div>
    </div>
  </body>
</html>
"""


def test_extract_product_details():
    details = extract_product_details(SAMPLE_DETAIL_HTML)
    assert details["detail_features"] == [
        "КОМБИНИРАН ХЛАДИЛНИК",
        "ОБЕМ НА ФРИЗЕРНА ЧАСТ: 71 л.",
    ]
    assert details["detail_specs"] == {
        "appliance_width_cm_range": {"min_cm": 50, "max_cm": 60},
        "appliance_height_cm_range": {"min_cm": 100, "max_cm": 170},
    }
    assert details["ean"] == "3838782766541"
