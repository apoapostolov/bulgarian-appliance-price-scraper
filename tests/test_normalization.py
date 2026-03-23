from technomarket_fridge_scraper.normalization import (
    canonicalize_spec_value,
    parse_energy_class,
    parse_price_to_int,
)


def test_parse_price_to_int():
    assert parse_price_to_int("1.171 BGN") == 1171
    assert parse_price_to_int("663.03 лв.") == 66303


def test_parse_energy_class():
    assert parse_energy_class("a g D") == "D"


def test_parse_size_range_and_dimensions():
    assert canonicalize_spec_value(
        "appliance_width_cm_range",
        "Над 50 И До 60 См",
    ) == {"min_cm": 50, "max_cm": 60}
    assert canonicalize_spec_value(
        "dimensions_cm",
        "161.3/55.4/55.8",
    ) == {"height_cm": 161.3, "width_cm": 55.4, "depth_cm": 55.8}
    assert canonicalize_spec_value("color", "Инокс") == "inox"
    assert canonicalize_spec_value("freezer_position", "Горен") == "top"
    assert canonicalize_spec_value("freezer_position", "Долен") == "bottom"
