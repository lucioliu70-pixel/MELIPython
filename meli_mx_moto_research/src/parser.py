from __future__ import annotations

from typing import Any, Dict, List

ATTRIBUTE_NAME_MAP = {
    "marca": "brand",
    "brand": "brand",
    "modelo": "model",
    "model": "model",
    "número de pieza": "part_number",
    "numero de pieza": "part_number",
    "part number": "part_number",
    "tipo de vehículo": "vehicle_type",
    "tipo de vehiculo": "vehicle_type",
    "vehicle type": "vehicle_type",
    "condición": "condition",
    "condicion": "condition",
    "condition": "condition",
    "tipo de producto": "product_type",
    "product type": "product_type",
}


def parse_attributes(attributes: List[Dict[str, Any]]) -> Dict[str, str]:
    parsed = {
        "brand": "",
        "model": "",
        "part_number": "",
        "vehicle_type": "",
        "condition": "",
        "product_type": "",
    }
    for a in attributes or []:
        key = str(a.get("name", "")).strip().lower()
        mapped = ATTRIBUTE_NAME_MAP.get(key)
        if mapped and not parsed[mapped]:
            parsed[mapped] = str(a.get("value_name") or "")
    return parsed
