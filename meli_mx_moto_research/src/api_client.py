from __future__ import annotations

import random
import time
from typing import Any, Dict, List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from loguru import logger


class MeliApiClient:
    def __init__(
        self,
        timeout: int = 20,
        sleep_seconds: float = 1.2,
        max_retries: int = 3,
        retry_429_sleep: int = 60,
        base_url: str = "https://listado.mercadolibre.com.mx",
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        random_delay_min: float = 1.2,
        random_delay_max: float = 2.4,
    ):
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries
        self.retry_429_sleep = retry_429_sleep
        self.base_url = base_url.rstrip("/")
        self.random_delay_min = random_delay_min
        self.random_delay_max = random_delay_max
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

    @staticmethod
    def keyword_to_slug(keyword: str) -> str:
        return "-".join(keyword.strip().split())

    def build_search_url(self, keyword: str) -> str:
        slug = self.keyword_to_slug(keyword)
        if not slug:
            slug = quote_plus(keyword)
        return f"{self.base_url}/{slug}"

    def _random_sleep(self) -> None:
        time.sleep(random.uniform(self.random_delay_min, self.random_delay_max))

    def fetch_search_page(self, keyword: str, offset: int = 0) -> str:
        base = self.build_search_url(keyword)
        url = base if offset <= 0 else f"{base}_Desde_{offset + 1}_NoIndex_True"
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 429:
                    logger.warning("429 rate limited. wait {}s attempt {}/{}", self.retry_429_sleep, attempt, self.max_retries)
                    time.sleep(self.retry_429_sleep)
                    continue
                if resp.status_code in (403, 503):
                    logger.error("{} forbidden/unavailable for {}", resp.status_code, url)
                    self._random_sleep()
                    continue
                resp.raise_for_status()
                self._random_sleep()
                return resp.text
            except requests.RequestException as e:
                logger.warning("page fetch failed attempt {}/{} url={} error={}", attempt, self.max_retries, url, e)
                self._random_sleep()
        return ""

    def parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("li.ui-search-layout__item")
        items: List[Dict[str, Any]] = []
        for card in cards:
            title_el = card.select_one("h3.poly-component__title-wrapper a") or card.select_one("a.poly-component__title")
            price_el = card.select_one("span.andes-money-amount__fraction")
            link = title_el.get("href", "") if title_el else ""
            title = title_el.get_text(strip=True) if title_el else ""
            price_txt = price_el.get_text(strip=True) if price_el else ""
            rating_el = card.select_one("span.poly-reviews__rating")
            reviews_el = card.select_one("span.poly-reviews__total")
            sold_el = card.select_one("span.poly-component__sold-quantity")
            shop_el = card.select_one("span.poly-component__seller")

            price = 0.0
            if price_txt.isdigit():
                price = float(price_txt)
            else:
                digits = "".join(ch for ch in price_txt if ch.isdigit())
                price = float(digits) if digits else 0.0

            items.append(
                {
                    "title": title,
                    "price": price,
                    "permalink": link,
                    "sold_info": sold_el.get_text(strip=True) if sold_el else "",
                    "rating": rating_el.get_text(strip=True) if rating_el else "",
                    "reviews": reviews_el.get_text(strip=True) if reviews_el else "",
                    "seller_nickname": shop_el.get_text(strip=True) if shop_el else "",
                }
            )
        return items

    def health_check(self, site_id: str = "MLM") -> tuple[bool, str]:
        html = self.fetch_search_page("cadena moto", offset=0)
        items = self.parse_search_results(html)
        if not items:
            return False, "网页采集不可用（可能被风控/网络拦截）"
        return True, f"网页采集可用，测试抓取 {len(items)} 条"
