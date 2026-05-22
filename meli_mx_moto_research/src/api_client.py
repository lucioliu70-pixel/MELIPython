from __future__ import annotations

import time
from typing import Any, Dict

import requests
from loguru import logger


class MeliApiClient:
    def __init__(
        self,
        timeout: int = 20,
        sleep_seconds: float = 1.2,
        max_retries: int = 3,
        retry_429_sleep: int = 60,
        base_url: str = "https://api.mercadolibre.com",
        search_path_template: str = "/sites/{site_id}/search",
        item_path_template: str = "/items/{item_id}",
    ):
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries
        self.retry_429_sleep = retry_429_sleep
        self.base_url = base_url.rstrip("/")
        self.search_path_template = search_path_template
        self.item_path_template = item_path_template

    def _request(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 429:
                    logger.warning("429 rate limited. wait {}s attempt {}/{}", self.retry_429_sleep, attempt, self.max_retries)
                    time.sleep(self.retry_429_sleep)
                    continue
                if resp.status_code == 403:
                    logger.error("403 forbidden for {}", url)
                    return {}
                resp.raise_for_status()
                time.sleep(self.sleep_seconds)
                return resp.json()
            except requests.Timeout:
                logger.warning("timeout for {} attempt {}/{}", url, attempt, self.max_retries)
            except requests.RequestException as e:
                logger.warning("request failed for {} attempt {}/{} error={}", url, attempt, self.max_retries, e)
            time.sleep(self.sleep_seconds)
        return {}

    def search_items(self, site_id: str, keyword: str, limit: int, offset: int) -> Dict[str, Any]:
        path = self.search_path_template.format(site_id=site_id)
        return self._request(path, params={"q": keyword, "limit": limit, "offset": offset})

    def get_item_detail(self, item_id: str) -> Dict[str, Any]:
        path = self.item_path_template.format(item_id=item_id)
        return self._request(path)

    def health_check(self, site_id: str) -> tuple[bool, str]:
        path = self.search_path_template.format(site_id=site_id)
        payload = self._request(path, params={"q": "moto", "limit": 1, "offset": 0})
        if not payload:
            return False, "API 无响应或被限制（请检查网络/频率）"
        result_count = len(payload.get("results", []))
        return True, f"API可用，测试返回 {result_count} 条结果"
