from __future__ import annotations

import json
from typing import Callable, Iterable, List

from loguru import logger

from .parser import parse_attributes
from .utils import now_iso


def collect_by_keywords(api_client, site_id: str, keywords: Iterable[str], total_per_keyword: int, batch_id: str, on_progress: Callable[[float, str], None] | None = None) -> List[tuple]:
    all_rows: List[tuple] = []
    key_list = list(keywords)
    for i, keyword in enumerate(key_list, start=1):
        logger.info("collecting keyword: {}", keyword)
        fetched = 0
        offset = 0
        page_limit = min(50, total_per_keyword)
        while fetched < total_per_keyword:
            current_limit = min(page_limit, total_per_keyword - fetched)
            res = api_client.search_items(site_id=site_id, keyword=keyword, limit=current_limit, offset=offset)
            results = res.get("results", [])
            if not results:
                break
            for item in results:
                detail = api_client.get_item_detail(item.get("id", "")) if item.get("id") else {}
                attrs = detail.get("attributes", [])
                parsed = parse_attributes(attrs)
                row = (
                    batch_id,
                    keyword,
                    item.get("id", ""),
                    item.get("title", ""),
                    float(item.get("price", 0) or 0),
                    item.get("currency_id", ""),
                    int(detail.get("sold_quantity", item.get("sold_quantity", 0)) or 0),
                    int(item.get("available_quantity", 0) or 0),
                    str(item.get("seller", {}).get("id", "")),
                    item.get("seller", {}).get("nickname", ""),
                    item.get("category_id", ""),
                    item.get("listing_type_id", ""),
                    int(bool(item.get("shipping", {}).get("free_shipping", False))),
                    item.get("shipping", {}).get("logistic_type", ""),
                    item.get("address", {}).get("state_name", ""),
                    item.get("address", {}).get("city_name", ""),
                    item.get("permalink", ""),
                    item.get("thumbnail", ""),
                    parsed.get("brand", ""),
                    parsed.get("model", ""),
                    json.dumps(attrs, ensure_ascii=False),
                    now_iso(),
                )
                all_rows.append(row)
            fetched += len(results)
            offset += len(results)
            if len(results) < current_limit:
                break
        if on_progress:
            on_progress(i / len(key_list), f"{keyword} 完成，累计 {len(all_rows)} 条")
    return all_rows
