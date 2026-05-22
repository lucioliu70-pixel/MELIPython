from __future__ import annotations

import time
from typing import Any, Dict

import requests
from loguru import logger


class MeliApiClient:
    BASE_URL = "https://api.mercadolibre.com"

    def __init__(self, timeout: int = 20, sleep_seconds: float = 1.2, max_retries: int = 3, retry_429_sleep: int = 60):
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries
        self.retry_429_sleep = retry_429_sleep

    def _request(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
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
        return self._request(f"/sites/{site_id}/search", params={"q": keyword, "limit": limit, "offset": offset})

    def get_item_detail(self, item_id: str) -> Dict[str, Any]:
        return self._request(f"/items/{item_id}")

    def health_check(self, site_id: str) -> tuple[bool, str]:
        payload = self._request(f"/sites/{site_id}/search", params={"q": "moto", "limit": 1, "offset": 0})
        if not payload:
            return False, "API 无响应或被限制（请检查网络/频率）"
        result_count = len(payload.get("results", []))
        return True, f"API可用，测试返回 {result_count} 条结果"
