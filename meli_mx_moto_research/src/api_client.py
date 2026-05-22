from __future__ import annotations

import random
import time
from typing import Any, Dict, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from loguru import logger
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class MeliApiClient:
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 4,
        retry_429_sleep: int = 60,
        base_url: str = "https://listado.mercadolibre.com.mx",
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        random_delay_min: float = 3.0,
        random_delay_max: float = 8.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_429_sleep = retry_429_sleep
        self.base_url = base_url.rstrip("/")
        self.random_delay_min = random_delay_min
        self.random_delay_max = random_delay_max
        self.user_agent = user_agent

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

    def _fetch_by_playwright(self, url: str) -> tuple[int, str]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=self.user_agent,
                locale="es-MX",
                viewport={"width": 1366, "height": 768},
            )
            page = context.new_page()
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                page.wait_for_timeout(1200)
                status = resp.status if resp else 0
                html = page.content()
                return status, html
            finally:
                context.close()
                browser.close()

    def fetch_search_page(self, keyword: str, offset: int = 0) -> str:
        base = self.build_search_url(keyword)
        url = base if offset <= 0 else f"{base}_Desde_{offset + 1}_NoIndex_True"

        for attempt in range(1, self.max_retries + 1):
            try:
                status, html = self._fetch_by_playwright(url)
                if status == 429 or "local_rate_limited" in html.lower():
                    logger.warning("rate limited for {} wait {}s attempt {}/{}", url, self.retry_429_sleep, attempt, self.max_retries)
                    time.sleep(self.retry_429_sleep)
                    continue
                if status in (403, 503):
                    logger.warning("status {} for {} attempt {}/{}", status, url, attempt, self.max_retries)
                    self._random_sleep()
                    continue
                if status >= 400:
                    logger.warning("status {} for {} attempt {}/{}", status, url, attempt, self.max_retries)
                    self._random_sleep()
                    continue
                self._random_sleep()
                return html
            except PlaywrightTimeoutError:
                logger.warning("playwright timeout for {} attempt {}/{}", url, attempt, self.max_retries)
                self._random_sleep()
            except Exception as e:
                logger.warning("playwright fetch failed for {} attempt {}/{} error={}", url, attempt, self.max_retries, e)
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
        if "local_rate_limited" in html.lower():
            return False, "触发 local_rate_limited，已启用自动等待重试策略"
        items = self.parse_search_results(html)
        if not items:
            return False, "网页采集不可用（可能被风控/网络拦截）"
        return True, f"网页采集可用，测试抓取 {len(items)} 条"
