import datetime
import asyncio
from setezor.exceptions.loggers import get_logger
from playwright.async_api import async_playwright
import os

logger = get_logger(__package__, handlers=[])


class Screenshoter:
    @classmethod
    async def take_screenshot(cls, url: str, screenshots_folder: str, timeout: float):
        filename = url.replace("://", "_").replace("/", "_")
        tz = datetime.datetime.now(datetime.timezone(
            datetime.timedelta(0))).astimezone().tzinfo
        current_datetime = datetime.datetime.now(tz=tz).isoformat()
        filename = f"{current_datetime}_{filename}.png"
        path = os.path.join(screenshots_folder, filename)
        result = []
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            page = await browser.new_page(ignore_https_errors=True)
            await page.goto(url=url, wait_until='load')
            await asyncio.sleep(timeout)
            await page.screenshot(path=path, full_page=True)
            result.append(path)
            await browser.close()
        return path
