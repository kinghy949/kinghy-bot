"""截图服务 - Playwright优先，失败降级占位图"""
import asyncio
import logging
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)


class ScreenshotService:
    VIEWPORT = {"width": 1280, "height": 800}

    def take_screenshots(self, task_id: str, html_files: dict[str, str]) -> dict[str, str]:
        try:
            return asyncio.run(self._take_screenshots(task_id, html_files))
        except Exception as e:
            logger.warning("截图服务降级为占位图: %s", e)
            return {name: self._create_placeholder_image(task_id, name) for name in html_files}

    async def _take_screenshots(self, task_id: str, html_files: dict[str, str]) -> dict[str, str]:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return {name: self._create_placeholder_image(task_id, name) for name in html_files}

        results: dict[str, str] = {}
        async with async_playwright() as p:
            browser = None
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(viewport=self.VIEWPORT)
                for name, html_path in html_files.items():
                    page = await context.new_page()
                    try:
                        await page.goto(Path(html_path).as_uri(), wait_until="networkidle", timeout=15000)
                        await page.wait_for_timeout(400)
                        shot_path = self._screenshot_path(task_id, name)
                        await page.screenshot(path=str(shot_path), full_page=False)
                        results[name] = str(shot_path)
                    except Exception as e:
                        logger.warning("截图失败[%s]: %s", name, e)
                        results[name] = self._create_placeholder_image(task_id, name)
                    finally:
                        await page.close()
                await context.close()
            finally:
                if browser:
                    await browser.close()
        return results

    def _screenshot_path(self, task_id: str, feature_name: str) -> Path:
        safe = "".join(ch if ch.isalnum() else "_" for ch in feature_name).strip("_") or "feature"
        out = Config.SCREENSHOT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        return out / f"{safe}.png"

    def _create_placeholder_image(self, task_id: str, feature_name: str) -> str:
        path = self._screenshot_path(task_id, f"placeholder_{feature_name}")
        try:
            from PIL import Image, ImageDraw

            image = Image.new("RGB", (1280, 800), color=(236, 240, 245))
            draw = ImageDraw.Draw(image)
            draw.text((80, 80), f"截图生成失败\n{feature_name}", fill=(120, 120, 120))
            image.save(path)
        except Exception:
            path.write_text(f"placeholder for {feature_name}", encoding="utf-8")
        return str(path)
