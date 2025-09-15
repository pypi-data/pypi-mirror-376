# scrapy-playfox: Yet another camoufox integration for Scrapy

[![version](https://img.shields.io/pypi/v/scrapy-playfox.svg)](https://pypi.python.org/pypi/scrapy-playfox)
[![pyversions](https://img.shields.io/pypi/pyversions/scrapy-playfox.svg)](https://pypi.python.org/pypi/scrapy-playfox)

A [Scrapy](https://www.scrapy.org) download handler "extended" on [scrapy-playwright](https://github.com/scrapy-plugins/scrapy-playwright). scrapy-playfox plays a role like glue that sticks scrapy-playwright and camoufox together without touching any of them.

## Why Camoufox?

Camoufox is the most modern, effective & future-proof open source solution for avoiding bot detection and intelligent fingerprint rotation. It's perfect choice for scraping sort of strong anti-bot websites.

## Installation

`scrapy-playfox` is available on PyPI and can be installed with `pip`:

```shell
pip install scrapy-playfox
```

`Camoufox` is defined as a dependency so it gets installed automatically, however it might be necessary to install the browser that will be used:

```shell
camoufox fetch
```

## Activation

### Download handler

Replace the default `http` and/or `https` Download Handlers through [`DOWNLOAD_HANDLERS`](https://docs.scrapy.org/en/latest/topics/settings.html):

```python
# settings.py
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playfox.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playfox.handler.ScrapyPlaywrightDownloadHandler",
}
```

If this handler is only used by specified spiders, you can add custom settings in your spider like this:

```python
import scrapy

class MySpider(scrapy.Spider):
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playfox.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playfox.handler.ScrapyPlaywrightDownloadHandler',
        },
    }
```

Note that the `ScrapyPlaywrightDownloadHandler` class inherits from the default `http/https` handler. Unless explicitly marked, requests will be processed by the regular Scrapy download handler.

### Twisted reactor

[Install the `asyncio`-based Twisted reactor](https://docs.scrapy.org/en/latest/topics/asyncio.html#installing-the-asyncio-reactor):

```python
# settings.py
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
```

This is the default in new projects since [Scrapy 2.7](https://github.com/scrapy/scrapy/releases/tag/2.7.0).

## Common Settings

This is the commonly used settings in your spider. Learn more from Camoufox and scrapy-playwright documentations.

```python
from browserforge.fingerprints import Screen

custom_settings = {
    'PLAYWRIGHT_LAUNCH_OPTIONS': {
        'headless': False,
        'humanize': True,
        'screen': Screen(max_width=1280, max_height=800),
        'geoip': False,
    },
    'PLAYWRIGHT_CONTEXTS': {
        'persistent': {
            'user_data_dir': 'playfox_data',
        }
    }
}
```

## Basic Usage

Same as [scrapy-playwright](https://github.com/scrapy-plugins/scrapy-playwright?tab=readme-ov-file#basic-usage).

```python
import scrapy

class MySpider(scrapy.Spider):
    name = "awesome"

    def start_requests(self):
        # GET request
        yield scrapy.Request("https://httpbin.org/get", meta={"playwright": True})
        # POST request
        yield scrapy.FormRequest(
            url="https://httpbin.org/post",
            formdata={"foo": "bar"},
            meta={"playwright": True},
        )

    def parse(self, response, **kwargs):
        # 'response' contains the page as seen by the browser
        return {"url": response.url}
```
