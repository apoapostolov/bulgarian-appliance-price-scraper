from __future__ import annotations

import re


LISTING_SPEC_KEY_MAP = {
    "Ширина на уреда": "appliance_width_cm_range",
    "Височина на уреда": "appliance_height_cm_range",
    "Размери В/Ш/Д (см)": "dimensions_cm",
    "WIDTH": "width_cm",
    "HEIGHT": "height_cm",
    "DEPTH": "depth_cm",
    "WASHING CAPACITY": "washing_capacity_kg",
    "SPIN-RPM": "spin_rpm",
    "WARRANTY": "warranty_months",
    "ENERGY EFFICIENCY CLASS": "energy_class",
    "ENERGY CLASS": "energy_class",
    "NOISE EMISSION CLASS": "noise_emission_class",
    "SOUND POWER LEVEL": "sound_power_level_db",
    "COLOUR": "color",
    "COLOR": "color",
    "KIND": "type",
    "MODEL": "model",
    "BRAND": "brand",
}


DETAIL_SPEC_KEY_MAP = {
    "Ширина на уреда": "appliance_width_cm_range",
    "Височина на уреда": "appliance_height_cm_range",
    "Размери В/Ш/Д (см)": "dimensions_cm",
    "WIDTH": "width_cm",
    "HEIGHT": "height_cm",
    "DEPTH": "depth_cm",
    "WASHING CAPACITY": "washing_capacity_kg",
    "SPIN-RPM": "spin_rpm",
    "WARRANTY": "warranty_months",
    "ENERGY EFFICIENCY CLASS": "energy_class",
    "ENERGY CLASS": "energy_class",
    "NOISE EMISSION CLASS": "noise_emission_class",
    "SOUND POWER LEVEL": "sound_power_level_db",
    "COLOUR": "color",
    "COLOR": "color",
    "KIND": "type",
    "MODEL": "model",
    "BRAND": "brand",
    "Отваряне": "door_opening",
    "ГОДИШЕН РАЗХОД (kWh)": "annual_energy_kwh",
    "ГОДИШНА КОНСУМАЦИЯ НА ЕНЕРГИЯ": "annual_energy_kwh",
    "Полезен обем на фризера (нето)": "freezer_net_volume_l",
    "Полезен обем на хладилника (нето)": "fridge_net_volume_l",
    "Общ обем (бруто)": "gross_volume_l",
    "БРОЙ ВРАТИ": "door_count",
    "Позиция на замразителя": "freezer_position",
    "Тип": "type",
    "Цвят": "color",
    "Модел": "model",
    "Бранд": "brand",
    "Енергиен клас": "energy_class",
}


VALUE_TRANSLATIONS = {
    "type": {
        "Комбиниран": "combined",
        "Свободно Стоящ": "freestanding",
        "За Вграждане": "built_in",
        "Front loader": "front_loader",
        "Top loader": "top_loader",
        "Built-in": "built_in",
        "Freestanding": "freestanding",
    },
    "door_opening": {
        "Дясно": "right",
        "Ляво": "left",
        "Right": "right",
        "Left": "left",
    },
    "freezer_position": {
        "Горен": "top",
        "Долен": "bottom",
        "Top": "top",
        "Bottom": "bottom",
    },
    "color": {
        "Инокс": "inox",
        "Бял": "white",
        "Черен": "black",
        "Сребро": "silver",
        "Сив": "gray",
        "Черна Стомана": "black_steel",
        "Неръждаема Стомана": "stainless_steel",
        "White": "white",
        "Black": "black",
        "Silver": "silver",
        "Gray": "gray",
        "Grey": "gray",
        "Inox": "inox",
        "Stainless Steel": "stainless_steel",
        "Black Steel": "black_steel",
    },
}


def parse_price_to_int(text: str | None) -> int | None:
    if not text:
        return None
    cleaned = text.replace("\xa0", " ").strip()
    digits = re.sub(r"[^\d]", "", cleaned)
    return int(digits) if digits else None


def parse_price_to_number(text: str | None) -> int | float | None:
    if not text:
        return None
    cleaned = text.replace("\xa0", " ").strip()
    digits = re.sub(r"[^0-9,.\s]", "", cleaned).replace(" ", "")
    if not digits:
        return None

    if "," in digits and "." in digits:
        if digits.rfind(",") > digits.rfind("."):
            digits = digits.replace(".", "").replace(",", ".")
        else:
            digits = digits.replace(",", "")
    elif "," in digits:
        parts = digits.split(",")
        if len(parts[-1]) in {1, 2}:
            digits = "".join(parts[:-1]) + "." + parts[-1]
        else:
            digits = "".join(parts)
    elif "." in digits:
        parts = digits.split(".")
        if len(parts[-1]) in {1, 2}:
            digits = "".join(parts[:-1]) + "." + parts[-1]
        else:
            digits = "".join(parts)

    try:
        value = float(digits)
    except ValueError:
        return None
    return int(value) if value.is_integer() else value


def parse_int(text: str | None) -> int | None:
    if isinstance(text, int):
        return text
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    return int(match.group(1))


def parse_number(text: str | None) -> float | int | None:
    if isinstance(text, (int, float)):
        return text
    if not text:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None
    value = match.group(1).replace(",", ".")
    if "." in value:
        number = float(value)
        return int(number) if number.is_integer() else number
    return int(value)


def parse_energy_class(text: str | None) -> str | None:
    if isinstance(text, str) and len(text) == 1 and text in "ABCDEFG":
        return text
    if not text:
        return None
    match = re.findall(r"\b([A-G])\b", text.upper())
    if match:
        return match[-1]
    match = re.search(r"([A-G])\s*$", text.upper())
    if match:
        return match.group(1)
    return None


def parse_cm_range(text: str | None) -> dict[str, int] | str | None:
    if isinstance(text, dict):
        return text
    if not text:
        return None
    numbers = [int(value) for value in re.findall(r"\d+", text)]
    if len(numbers) >= 2:
        return {"min_cm": numbers[0], "max_cm": numbers[1]}
    return text


def parse_dimensions(text: str | None) -> dict[str, float] | str | None:
    if isinstance(text, dict):
        return text
    if not text:
        return None
    parts = [part.strip() for part in text.replace("см.", "").replace("См.", "").split("/") if part.strip()]
    if len(parts) != 3:
        return text
    try:
        height, width, depth = (float(part.replace(",", ".")) for part in parts)
    except ValueError:
        return text
    return {
        "height_cm": height,
        "width_cm": width,
        "depth_cm": depth,
    }


def canonicalize_label(label: str) -> str:
    mapped = DETAIL_SPEC_KEY_MAP.get(label, LISTING_SPEC_KEY_MAP.get(label))
    if mapped:
        return mapped
    if re.fullmatch(r"[A-Z0-9][A-Z0-9 /&\\-]*", label):
        return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return label


def canonicalize_spec_value(key: str, value: object | None) -> object:
    if key in {"appliance_width_cm_range", "appliance_height_cm_range"}:
        return parse_cm_range(value)
    if key == "dimensions_cm":
        return parse_dimensions(value)
    if key in {"annual_energy_kwh", "freezer_net_volume_l", "fridge_net_volume_l", "gross_volume_l", "door_count", "spin_rpm", "warranty_months"}:
        return parse_int(value)
    if key in {"width_cm", "height_cm", "depth_cm", "washing_capacity_kg", "sound_power_level_db", "power_w", "capacity_l", "basket_count", "place_settings", "noise_level_db", "weight_kg"}:
        return parse_number(value)
    if key in {"features", "other_features", "defrost_function", "end_signal", "display", "half_load", "inverter_motor", "tank_material", "dimensions_text", "control_type"}:
        return value
    if key == "freezer_position" and value is not None:
        return VALUE_TRANSLATIONS[key].get(value, value)
    if key == "energy_class":
        return parse_energy_class(value)
    if key in VALUE_TRANSLATIONS and value is not None:
        return VALUE_TRANSLATIONS[key].get(value, value)
    return value
