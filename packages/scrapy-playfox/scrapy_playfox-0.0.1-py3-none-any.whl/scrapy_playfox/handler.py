import asyncio
import logging
from dataclasses import dataclass
from typing import TypeVar, override, Optional, Dict, Callable, Awaitable, Union

import scrapy_playwright.handler
from camoufox.async_api import AsyncNewBrowser
from playwright.async_api import (
    Request as PlaywrightRequest,
)
from scrapy import Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import NotSupported
from scrapy.utils.misc import load_object
from scrapy_playwright._utils import (
    _ThreadedLoopAdapter,
)
from scrapy_playwright.handler import BrowserContextWrapper

__all__ = ["ScrapyPlaywrightDownloadHandler"]
PlaywrightHandler = TypeVar("PlaywrightHandler", bound="ScrapyPlaywrightDownloadHandler")
logger = logging.getLogger("scrapy-playfox")

DEFAULT_BROWSER_TYPE = "firefox"
DEFAULT_CONTEXT_NAME = "default"
PERSISTENT_CONTEXT_PATH_KEY = "user_data_dir"


@dataclass
class Config(scrapy_playwright.handler.Config):
    @classmethod
    def from_settings(cls, settings):
        if settings.get("PLAYWRIGHT_CDP_URL"):
            msg = "Setting PLAYWRIGHT_CDP_URL is not supported for firefox implementation."
            logger.error(msg)
            raise NotSupported(msg)

        cfg = super().from_settings(settings)
        cfg.browser_type_name = DEFAULT_BROWSER_TYPE
        return cfg


class ScrapyPlaywrightDownloadHandler(scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler):
    def __init__(self, crawler: Crawler):
        super().__init__(crawler)
        self.config = Config.from_settings(crawler.settings)

        if self.config.use_threaded_loop:
            _ThreadedLoopAdapter.start(id(self))

        self.browser_launch_lock = asyncio.Lock()
        self.context_launch_lock = asyncio.Lock()
        self.context_wrappers: Dict[str, BrowserContextWrapper] = {}
        if self.config.max_contexts:
            self.context_semaphore = asyncio.Semaphore(value=self.config.max_contexts)

        # headers
        # if "PLAYWRIGHT_PROCESS_REQUEST_HEADERS" in crawler.settings:
        #     if crawler.settings["PLAYWRIGHT_PROCESS_REQUEST_HEADERS"] is None:
        #         self.process_request_headers = None
        #     else:
        #         self.process_request_headers = load_object(
        #             crawler.settings["PLAYWRIGHT_PROCESS_REQUEST_HEADERS"]
        #         )
        # else:
        #     self.process_request_headers = use_scrapy_headers
        self.process_request_headers = None

        self.abort_request: Optional[Callable[[PlaywrightRequest], Union[Awaitable, bool]]] = None
        if crawler.settings.get("PLAYWRIGHT_ABORT_REQUEST"):
            self.abort_request = load_object(crawler.settings["PLAYWRIGHT_ABORT_REQUEST"])

    @override
    async def _create_browser_context(
            self,
            name: str,
            context_kwargs: Optional[dict],
            spider: Optional[Spider] = None,
    ) -> scrapy_playwright.handler.BrowserContextWrapper:
        """Create a new context, also launching a local browser or connecting
        to a remote one if necessary.
        """
        if hasattr(self, "context_semaphore"):
            await self.context_semaphore.acquire()
        context_kwargs = context_kwargs or {}
        persistent = remote = False
        if context_kwargs.get(PERSISTENT_CONTEXT_PATH_KEY):
            # context = await self.browser_type.launch_persistent_context(**context_kwargs)
            await self._maybe_launch_browser(persistent=True, user_data_dir=context_kwargs.get(PERSISTENT_CONTEXT_PATH_KEY))
            context = self.browser
            persistent = True
        elif self.config.cdp_url:
            await self._maybe_connect_remote_devtools()
            context = await self.browser.new_context(**context_kwargs)
            remote = True
        elif self.config.connect_url:
            await self._maybe_connect_remote()
            context = await self.browser.new_context(**context_kwargs)
            remote = True
        else:
            await self._maybe_launch_browser()
            context = await self.browser.new_context(**context_kwargs)

        context.on(
            "disconnected", self._make_close_browser_context_callback(name, persistent, remote, spider)
        )
        self.stats.inc_value("playwright/context_count")
        self.stats.inc_value(f"playwright/context_count/persistent/{persistent}")
        self.stats.inc_value(f"playwright/context_count/remote/{remote}")
        logger.debug(
            "Browser context started: '%s' (persistent=%s, remote=%s)",
            name,
            persistent,
            remote,
            extra={
                "spider": spider,
                "context_name": name,
                "persistent": persistent,
                "remote": remote,
            },
        )
        if self.config.navigation_timeout is not None:
            context.set_default_navigation_timeout(self.config.navigation_timeout)
        self.context_wrappers[name] = scrapy_playwright.handler.BrowserContextWrapper(
            context=context,
            semaphore=asyncio.Semaphore(value=self.config.max_pages_per_context),
            persistent=persistent,
        )
        self._set_max_concurrent_context_count()
        return self.context_wrappers[name]

    @override
    async def _maybe_launch_browser(self, persistent: bool = False, user_data_dir: str = '') -> None:
        async with self.browser_launch_lock:
            if not hasattr(self, "browser"):
                logger.info("Launching browser %s", self.browser_type.name)
                # self.browser = await self.browser_type.launch(**self.config.launch_options)
                self.browser = await AsyncNewBrowser(playwright=self.playwright,
                                                     **self.config.launch_options,
                                                     persistent_context=persistent,
                                                     user_data_dir=user_data_dir)
                logger.info("Browser %s launched", self.browser_type.name)
                self.stats.inc_value("playwright/browser_count")
                self.browser.on("disconnected", self._browser_disconnected_callback)
