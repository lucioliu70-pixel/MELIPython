from __future__ import annotations

import json
import re
from typing import Callable, Iterable, List

from loguru import logger

from .utils import now_iso


def _extract_item_id_from_link(link: str) -> str:
    match = re.search(r"(MLM\d+)", link or "")
    return match.group(1) if match else ""


def _sold_to_int(sold_info: str) -> int:
    if not sold_info:
        return 0
    digits = re.findall(r"\d+", sold_info.replace(".", ""))
    return int(digits[0]) if digits else 0


def collect_by_keywords(api_client, site_id: str, keywords: Iterable[str], total_per_keyword: int, batch_id: str, on_progress: Callable[[float, str], None] | None = None) -> List[tuple]:
    all_rows: List[tuple] = []
    key_list = list(keywords)
    for i, keyword in enumerate(key_list, start=1):
        logger.info("collecting keyword(web): {}", keyword)
        fetched = 0
        offset = 0
        page_size = 50
        while fetched < total_per_keyword:
            html = api_client.fetch_search_page(keyword=keyword, offset=offset)
            results = api_client.parse_search_results(html)
            if not results:
                break
            for item in results:
                item_id = _extract_item_id_from_link(item.get("permalink", ""))
                sold_quantity = _sold_to_int(item.get("sold_info", ""))
                attrs = {
                    "rating": item.get("rating", ""),
                    "reviews": item.get("reviews", ""),
                    "sold_info": item.get("sold_info", ""),
                }
                row = (
                    batch_id,
                    keyword,
                    item_id,
                    item.get("title", ""),
                    float(item.get("price", 0) or 0),
                    "MXN",
                    sold_quantity,
                    0,
                    "",
                    item.get("seller_nickname", ""),
                    "",
                    "",
                    0,
                    "",
                    "",
                    "",
                    item.get("permalink", ""),
                    "",
                    "",
                    "",
                    json.dumps(attrs, ensure_ascii=False),
                    now_iso(),
                )
                all_rows.append(row)
                fetched += 1
                if fetched >= total_per_keyword:
                    break
            offset += page_size
        if on_progress:
            on_progress(i / len(key_list), f"{keyword} 完成，累计 {len(all_rows)} 条")
    return all_rows
