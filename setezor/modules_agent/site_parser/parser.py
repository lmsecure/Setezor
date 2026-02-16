import os.path
import tempfile
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

from setezor.settings import MODULES_PATH, PLATFORM


class SiteParser:

    @classmethod
    async def parse(
            cls,
            task_id: str,
            url: str,
            with_screenshot: bool,
            with_wappalyzer: bool = True,
            timeout: float = 30000,
            is_retry: bool = False,
    ) -> dict:
        """
        Создаёт web архив страницы.
        """
        async with async_playwright() as p:
            with tempfile.TemporaryDirectory() as tmp:
                har_path = Path(tmp) / f'{task_id}.har'
                path_to_extension = os.path.join(
                    MODULES_PATH, 'site_parser', 'wappalyzer'
                )
                user_data_path = os.path.join(MODULES_PATH, 'site_parser', 'wappalyzer', 'user_data')
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=user_data_path,
                    executable_path=os.path.join(
                        MODULES_PATH, 'site_parser', 'browser',
                        'chrome' + ('.exe' if PLATFORM == 'Windows' else '')
                    ),
                    record_har_path=str(har_path),
                    record_har_content='embed',
                    ignore_https_errors=True,
                    headless=True,
                    args=[
                        f"--disable-extensions-except={path_to_extension}",
                        f"--load-extension={path_to_extension}",
                    ],
                )
                screenshot = None
                wappalyzer_data = None
                try:
                    page = await context.new_page()
                    try:
                        await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
                    except Exception:
                        try:
                            await page.goto(url)
                        except Exception:
                            if not is_retry:
                                await cls.parse(task_id, url, with_screenshot, with_wappalyzer, is_retry=True)
                            else:
                                raise

                    if with_screenshot:
                        screenshot = await page.screenshot(full_page=True)

                    if with_wappalyzer:
                        if len(context.service_workers) == 0:
                            service_worker = await context.wait_for_event('serviceworker')
                        else:
                            service_worker = context.service_workers[0]

                        try:    
                            async with asyncio.timeout(10):
                                wappalyzer_data = await service_worker.evaluate(
                                    '''async () => {
                                    return await Driver.getDetections()
                                    }'''
                                )
                        
                        except Exception:
                            if not is_retry:
                                await cls.parse(task_id, url, with_screenshot, with_wappalyzer, is_retry=True)
                            else:
                                raise
                finally:
                    await context.close()

                return {
                    'screenshot': screenshot,
                    'har': har_path.read_bytes(),
                    'wappalyzer_data': wappalyzer_data
                }