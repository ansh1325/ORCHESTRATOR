"""
JARVIS Crawl4AI Superpower Engine
===================================
High-Performance, LLM-Optimized Stealth Web Crawler & Scraper.
Solves Live Scraping on Auth-Walled & Anti-Bot Protected Platforms:
1. Stealth & Magic Mode: Evasion of bot mitigation, Cloudflare, User-Agent rotation, patchright masking.
2. Authenticated Scraping: Reuses JARVIS's persistent browser profile (~/.llama_orchestrator/browser_profile)
   to access auth-walled platforms (LinkedIn, Twitter, LeetCode, GitHub, SaaS portals) with active credentials.
3. Fit-Markdown Generation: Strips boilerplate, ads, and noise, outputting dense, token-efficient Markdown for LLMs.
4. Concurrent Batch Scraping: Asynchronous multi-URL scraping with memory guards and rate limiting.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List

# Suppress cloud notice banner if requested
os.environ.setdefault("CRAWL4AI_NO_CLOUD_NOTICE", "1")

logger = logging.getLogger("Jarvis.Crawl4AI")

try:
    from crawl4ai import (
        AsyncWebCrawler,
        BrowserConfig,
        CrawlerRunConfig,
        CacheMode
    )
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    CRAWL4AI_AVAILABLE = True
except ImportError as err:
    logger.warning(f"Crawl4AI not installed or failed to import: {err}")
    CRAWL4AI_AVAILABLE = False


class Crawl4AIEngine:
    """
    Central Autonomous Crawl4AI Interface for JARVIS.
    Supports headless/headful, anti-bot stealth, persistent context (auth-walled),
    and structured fit-markdown synthesis.
    """

    @classmethod
    def get_shared_profile_path(cls) -> Path:
        """Returns the canonical persistent browser profile directory shared across JARVIS."""
        prof = Path.home() / ".llama_orchestrator" / "browser_profile"
        prof.mkdir(parents=True, exist_ok=True)
        return prof

    @classmethod
    def doctor(cls) -> dict[str, Any]:
        """
        Inspects Crawl4AI installation, patchright/browser engines, and persistent profile state.
        """
        shared_prof = cls.get_shared_profile_path()
        has_cookies = False
        cookies_file = shared_prof / "Default" / "Network" / "Cookies"
        if cookies_file.exists() and cookies_file.stat().st_size > 0:
            has_cookies = True

        health = {
            "crawl4ai_installed": CRAWL4AI_AVAILABLE,
            "browser_profile_path": str(shared_prof),
            "profile_exists": shared_prof.exists(),
            "has_saved_session_cookies": has_cookies,
            "engine_status": "ONLINE" if CRAWL4AI_AVAILABLE else "OFFLINE",
            "capabilities": [
                "Stealth & Anti-Bot Magic Mode (Patchright)",
                "Auth-Walled Platform Scraping (Persistent Browser Profile)",
                "Token-Optimized Fit-Markdown Generation",
                "Concurrent Batch Scraping",
                "Custom JS Execution & Dynamic Selector Wait"
            ]
        }
        return health

    @classmethod
    async def crawl_url(
        cls,
        url: str,
        magic: bool = True,
        stealth: bool = True,
        wait_for: Optional[str] = None,
        css_selector: Optional[str] = None,
        js_code: Optional[str] = None,
        headless: bool = True,
        timeout_ms: int = 45000,
        scan_full_page: bool = False
    ) -> dict[str, Any]:
        """
        Asynchronously crawls a target URL with stealth, anti-bot evasion, and markdown extraction.
        """
        if not CRAWL4AI_AVAILABLE:
            return {
                "success": False,
                "url": url,
                "error": "Crawl4AI is not installed in current environment."
            }

        try:
            browser_cfg = BrowserConfig(
                headless=headless,
                enable_stealth=stealth,
                ignore_https_errors=True
            )
            run_cfg = CrawlerRunConfig(
                magic=magic,
                simulate_user=True,
                remove_overlay_elements=True,
                remove_consent_popups=True,
                wait_for=wait_for,
                css_selector=css_selector,
                js_code=js_code,
                scan_full_page=scan_full_page,
                page_timeout=timeout_ms
            )

            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                res = await crawler.arun(url=url, config=run_cfg)
                
                raw_md = ""
                fit_md = ""
                if hasattr(res, "markdown"):
                    if hasattr(res.markdown, "raw_markdown"):
                        raw_md = res.markdown.raw_markdown or ""
                        fit_md = getattr(res.markdown, "fit_markdown", "") or raw_md
                    elif isinstance(res.markdown, str):
                        raw_md = res.markdown
                        fit_md = raw_md

                links = res.links if hasattr(res, "links") and isinstance(res.links, dict) else {}
                internal_links = links.get("internal", [])
                external_links = links.get("external", [])
                total_links = len(internal_links) + len(external_links)

                media = res.media if hasattr(res, "media") and isinstance(res.media, dict) else {}
                images = media.get("images", []) if isinstance(media, dict) else []

                return {
                    "success": bool(res.success),
                    "url": url,
                    "status_code": getattr(res, "status_code", 200),
                    "markdown": raw_md,
                    "fit_markdown": fit_md or raw_md,
                    "title": getattr(res, "title", "") or "",
                    "links_count": total_links,
                    "media_count": len(images),
                    "internal_links": [l.get("href") for l in internal_links[:15] if isinstance(l, dict) and l.get("href")],
                    "external_links": [l.get("href") for l in external_links[:15] if isinstance(l, dict) and l.get("href")],
                    "error": None if res.success else getattr(res, "error_message", "Crawl failed")
                }
        except Exception as e:
            logger.error(f"Crawl4AI exception crawling {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    @classmethod
    async def crawl_auth_walled(
        cls,
        url: str,
        service_hint: Optional[str] = None,
        magic: bool = True,
        wait_for: Optional[str] = None,
        js_code: Optional[str] = None,
        timeout_ms: int = 60000
    ) -> dict[str, Any]:
        """
        Specifically crawls an auth-walled or private portal page by injecting JARVIS's
        persistent browser session credentials.
        """
        if not CRAWL4AI_AVAILABLE:
            return {
                "success": False,
                "url": url,
                "error": "Crawl4AI is not installed in current environment."
            }

        shared_prof = cls.get_shared_profile_path()
        try:
            browser_cfg = BrowserConfig(
                headless=True,
                enable_stealth=True,
                use_persistent_context=True,
                user_data_dir=str(shared_prof),
                ignore_https_errors=True
            )
            run_cfg = CrawlerRunConfig(
                magic=magic,
                simulate_user=True,
                remove_overlay_elements=True,
                remove_consent_popups=True,
                wait_for=wait_for,
                js_code=js_code,
                page_timeout=timeout_ms
            )

            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                res = await crawler.arun(url=url, config=run_cfg)

                raw_md = ""
                fit_md = ""
                if hasattr(res, "markdown"):
                    if hasattr(res.markdown, "raw_markdown"):
                        raw_md = res.markdown.raw_markdown or ""
                        fit_md = getattr(res.markdown, "fit_markdown", "") or raw_md
                    elif isinstance(res.markdown, str):
                        raw_md = res.markdown
                        fit_md = raw_md

                return {
                    "success": bool(res.success),
                    "url": url,
                    "service": service_hint or "auth_walled_portal",
                    "status_code": getattr(res, "status_code", 200),
                    "markdown": raw_md,
                    "fit_markdown": fit_md or raw_md,
                    "title": getattr(res, "title", "") or "",
                    "authenticated_session_used": True,
                    "profile_path": str(shared_prof),
                    "error": None if res.success else getattr(res, "error_message", "Auth crawl failed")
                }
        except Exception as e:
            # Fallback if profile is locked: attempt standard stealth crawl
            logger.warning(f"Persistent context locked or failed ({e}); falling back to standard stealth crawl.")
            res = await cls.crawl_url(url=url, magic=True, stealth=True, wait_for=wait_for, js_code=js_code)
            res["auth_fallback_triggered"] = True
            return res

    @classmethod
    async def crawl_batch(
        cls,
        urls: list[str],
        max_concurrent: int = 5,
        magic: bool = True
    ) -> list[dict[str, Any]]:
        """
        Asynchronously crawls a batch of URLs concurrently with rate limiting and semaphore isolation.
        """
        if not CRAWL4AI_AVAILABLE or not urls:
            return []

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded_crawl(u: str) -> dict[str, Any]:
            async with semaphore:
                return await cls.crawl_url(u, magic=magic)

        tasks = [_bounded_crawl(u) for u in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)

    @classmethod
    def crawl_url_sync(cls, url: str, **kwargs) -> dict[str, Any]:
        """
        Synchronous convenience bridge for components running outside async event loops.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, cls.crawl_url(url, **kwargs))
                    return future.result(timeout=60)
            else:
                return loop.run_until_complete(cls.crawl_url(url, **kwargs))
        except RuntimeError:
            return asyncio.run(cls.crawl_url(url, **kwargs))
        except Exception as e:
            return {"success": False, "url": url, "error": str(e)}

    @classmethod
    def crawl_auth_walled_sync(cls, url: str, **kwargs) -> dict[str, Any]:
        """
        Synchronous convenience bridge for auth-walled scraping.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, cls.crawl_auth_walled(url, **kwargs))
                    return future.result(timeout=60)
            else:
                return loop.run_until_complete(cls.crawl_auth_walled(url, **kwargs))
        except RuntimeError:
            return asyncio.run(cls.crawl_auth_walled(url, **kwargs))
        except Exception as e:
            return {"success": False, "url": url, "error": str(e)}


crawl4ai_engine = Crawl4AIEngine()

