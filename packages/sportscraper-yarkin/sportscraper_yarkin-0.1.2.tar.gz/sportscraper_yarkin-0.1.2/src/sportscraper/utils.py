from __future__ import annotations
import functools
import logging
import time
from typing import Callable, Iterable, Tuple, Type

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth


def retry(
    max_attempts: int = 3,
    delay: float = 3.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    logger: logging.Logger | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exc = None
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:  # noqa: PERF203
                    attempt += 1
                    last_exc = e
                    (logger or logging).warning(
                        "Attempt %d/%d failed for %s: %s",
                        attempt, max_attempts, func.__name__, e
                    )
                    if attempt >= max_attempts:
                        (logger or logging).error("%s failed after %d attempts.",
                                                  func.__name__, max_attempts)
                        raise
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


def initialize_driver(headless: bool = True, extra_args: Iterable[str] | None = None) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if extra_args:
        for arg in extra_args:
            options.add_argument(arg)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver
