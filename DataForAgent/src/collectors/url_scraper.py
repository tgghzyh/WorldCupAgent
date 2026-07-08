"""HTTP 内容抓取器（纯 HTTP，不调用 LLM）。

职责：
- 抓取 URL 的 HTML 内容并清洗为可读文本
- 可选地解析为结构化字段（基于 CSS 选择器 / schema 规则）

未来若引入 Agent，本模块作为 Agent 的一个 Tool 存在。
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
import requests


class URLScraper:
    """纯 HTTP 抓取 + 规则化字段提取"""

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self, raw_path: Optional[Path] = None):
        self.raw_path = raw_path
        if self.raw_path is not None:
            self.raw_path.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    def fetch_html(self, url: str, timeout: int = 30) -> Optional[str]:
        """抓取原始 HTML"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            logger.info(f"已获取 HTML ({len(response.text)} 字符): {url}")
            return response.text
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return None

    def fetch_text(self, url: str, timeout: int = 30) -> Optional[str]:
        """抓取并清洗为纯文本（去除 script/style/nav 等）"""
        from bs4 import BeautifulSoup

        html = self.fetch_html(url, timeout=timeout)
        if html is None:
            return None

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = "\n".join(line for line in text.split("\n") if line.strip())
        return text

    def extract_with_schema(
        self,
        url: str,
        schema: Dict[str, str],
        timeout: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """基于 schema 的规则化字段提取（无 LLM）

        schema 格式：
            {"field_name": "CSS selector or regex pattern"}

        返回字段值，未命中则为 None。
        """
        from bs4 import BeautifulSoup

        html = self.fetch_html(url, timeout=timeout)
        if html is None:
            return None

        soup = BeautifulSoup(html, "lxml")
        result: Dict[str, Any] = {"_source_url": url}

        for field, selector in schema.items():
            try:
                if selector.startswith("//") or selector.startswith("/"):
                    elements = soup.select(selector)
                elif selector.startswith("regex:"):
                    pattern = selector[len("regex:"):]
                    text = soup.get_text("\n", strip=True)
                    match = re.search(pattern, text)
                    result[field] = match.group(1) if match and match.groups() else (match.group(0) if match else None)
                    continue
                else:
                    elements = soup.select(selector)

                if elements:
                    result[field] = elements[0].get_text(strip=True)
                else:
                    result[field] = None
            except Exception as e:
                logger.warning(f"字段提取失败 {field}: {e}")
                result[field] = None

        return result

    def batch_fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """批量抓取并以结构化形式返回（仅文本，不做 LLM 提取）"""
        results = []
        for url in urls:
            text = self.fetch_text(url)
            if text:
                results.append({
                    "_source_url": url,
                    "fetched_at": __import__("datetime").datetime.utcnow().isoformat(),
                    "text": text[:50000],
                })
        logger.info(f"批量抓取完成: {len(results)}/{len(urls)} 成功")
        return results


if __name__ == "__main__":
    scraper = URLScraper()
    print("URLScraper ready (no LLM dependency)")