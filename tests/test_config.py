from pathlib import Path

from technomarket_fridge_scraper.config import load_config


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.toml"


def test_load_default_profile():
    config = load_config(CONFIG_PATH)
    assert config.store == "technomarket"
    assert config.appliance_type == "refrigerator"
    assert config.profile.output_prefix == "bulgarian_appliance_price_scraper_technomarket_refrigerators"
    assert config.profile.metadata_cache_path.as_posix().endswith("refrigerator_metadata.json")


def test_load_selected_profile():
    config = load_config(CONFIG_PATH, store_override="technopolis", appliance_type_override="oven")
    assert config.store == "technopolis"
    assert config.appliance_type == "oven"
    assert config.profile.output_prefix == "bulgarian_appliance_price_scraper_technopolis_ovens"
    assert config.profile.categories[0].path.endswith("/P11110101")


def test_load_technopolis_refrigerator_profile():
    config = load_config(CONFIG_PATH, store_override="technopolis", appliance_type_override="refrigerator")
    assert config.store == "technopolis"
    assert config.appliance_type == "refrigerator"
    assert config.profile.categories == []
    assert config.profile.category_texts[0] == "Refrigerator bottom freezer"
    assert config.profile.hub_path.endswith("/P111003")


def test_load_zora_profile():
    config = load_config(CONFIG_PATH, store_override="zora", appliance_type_override="microwave")
    assert config.store == "zora"
    assert config.profile.output_prefix == "bulgarian_appliance_price_scraper_zora_microwaves"
    assert config.profile.categories[0].path == "/category/mikrovalnovi-furni"
