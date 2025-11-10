"""
Image Retriever Module

Uses Playwright to automate browser interactions and retrieve book page images
from various online sources (Google Drive, Calameo, custom viewers, etc.).
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
import re
from loguru import logger
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import base64


class ImageRetriever:
    """
    Retrieves book page images from web sources using browser automation.

    Supports:
    - Intercepting network requests for images
    - Automated navigation (scrolling, clicking)
    - Handling lazy-loaded content
    - Rate limiting and retry logic
    """

    def __init__(
        self,
        output_dir: Path,
        headless: bool = True,
        timeout: int = 30000,
        max_retries: int = 3,
        wait_for_images: int = 2000,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the image retriever.

        Args:
            output_dir: Directory to save retrieved images
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            max_retries: Maximum number of retry attempts
            wait_for_images: Time to wait for images to load (ms)
            user_agent: Custom user agent string
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.timeout = timeout
        self.max_retries = max_retries
        self.wait_for_images = wait_for_images
        self.user_agent = user_agent
        self.intercepted_images: List[bytes] = []
        self.page_count = 0
        self.is_calameo = False  # Track if source is Calameo (SVG-based)

    async def retrieve_images(
        self,
        url: str,
        strategy: str = "intercept",
        max_pages: Optional[int] = None,
    ) -> List[Path]:
        """
        Retrieve all book page images from the given URL.

        Args:
            url: Book viewer URL
            strategy: Retrieval strategy ("intercept", "screenshot", "download")
            max_pages: Maximum number of pages to retrieve

        Returns:
            List of paths to saved images
        """
        logger.info(f"Starting image retrieval from {url}")
        logger.info(f"Strategy: {strategy}, Max pages: {max_pages}")

        # Detect Calameo (uses SVG files)
        self.is_calameo = "calameo.com" in url.lower()
        if self.is_calameo:
            logger.info("Detected Calameo source - will only save SVG/SVGZ files")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            context_options = {"user_agent": self.user_agent} if self.user_agent else {}
            context = await browser.new_context(**context_options)

            page = await context.new_page()
            page.set_default_timeout(self.timeout)

            # Set up image interception if using intercept strategy
            if strategy == "intercept":
                await self._setup_image_interception(page)

            try:
                await page.goto(url, wait_until="networkidle")
                await asyncio.sleep(self.wait_for_images / 1000)

                if strategy == "intercept":
                    saved_paths = await self._retrieve_via_interception(page, max_pages)
                elif strategy == "screenshot":
                    saved_paths = await self._retrieve_via_screenshot(page, max_pages)
                elif strategy == "download":
                    saved_paths = await self._retrieve_via_download(page, max_pages)
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")

                logger.info(f"Successfully retrieved {len(saved_paths)} images")
                return saved_paths

            except Exception as e:
                logger.error(f"Error during image retrieval: {e}")
                raise
            finally:
                await browser.close()

    async def _setup_image_interception(self, page: Page) -> None:
        """Set up network request interception for images."""
        async def handle_response(response):
            try:
                url = response.url
                content_type = response.headers.get("content-type", "")

                # Check if response is an image or Calameo asset
                is_image = "image" in content_type.lower()
                is_calameo_asset = "calameoassets.com" in url and (".svg" in url or ".jpg" in url or ".png" in url)

                if is_image or is_calameo_asset:
                    # Get the image data
                    image_data = await response.body()
                    if image_data:
                        self.intercepted_images.append(image_data)
                        logger.info(f"Intercepted image: {url} ({len(image_data)} bytes, {content_type})")
            except Exception as e:
                logger.warning(f"Failed to intercept response from {response.url}: {e}")

        page.on("response", handle_response)

    async def _retrieve_via_interception(
        self, page: Page, max_pages: Optional[int] = None
    ) -> List[Path]:
        """Retrieve images by intercepting network requests."""
        saved_paths = []
        self.intercepted_images = []

        # Detect navigation elements (Next button, arrow keys, etc.)
        next_button_selectors = [
            'button[aria-label="Next page"]',  # Calameo specific
            "[aria-label*='next' i]",
            "button:has-text('Next')",
            "button:has-text('→')",
            "a:has-text('Next')",
            ".next-page",
            "#next-page",
        ]

        page_num = 1
        consecutive_empty_pages = 0
        max_empty_pages = 3

        while True:
            if max_pages and page_num > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            # Wait for images to load
            logger.info(f"Waiting for images on page {page_num}...")
            await asyncio.sleep(self.wait_for_images / 1000)

            # Save any new intercepted images
            if self.intercepted_images:
                logger.info(f"Found {len(self.intercepted_images)} intercepted images")
                for img_data in self.intercepted_images:
                    path = self._save_image(img_data, page_num)
                    if path:
                        saved_paths.append(path)
                        logger.info(f"Saved page {page_num}: {path}")
                        page_num += 1
                self.intercepted_images = []
                consecutive_empty_pages = 0
            else:
                logger.warning(f"No images intercepted on current page")
                consecutive_empty_pages += 1

            # Check if we've had too many empty pages in a row
            if consecutive_empty_pages >= max_empty_pages:
                logger.info(f"Stopping: {consecutive_empty_pages} consecutive pages with no images")
                break

            # Try to navigate to next page
            navigated = False
            for selector in next_button_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        logger.info(f"Clicking next button with selector: {selector}")
                        await button.click()
                        await asyncio.sleep(1)
                        navigated = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not navigated:
                logger.info("No button found, trying arrow key")
                # Try arrow key
                try:
                    await page.keyboard.press("ArrowRight")
                    await asyncio.sleep(1)
                    navigated = True
                except Exception as e:
                    logger.warning(f"Arrow key navigation failed: {e}")
                    break

            if not navigated:
                logger.info("Unable to navigate to next page, stopping")
                break

        return saved_paths

    async def _retrieve_via_screenshot(
        self, page: Page, max_pages: Optional[int] = None
    ) -> List[Path]:
        """Retrieve images by taking screenshots of each page."""
        saved_paths = []
        page_num = 1

        while True:
            if max_pages and page_num > max_pages:
                break

            try:
                # Take screenshot
                screenshot_path = self.output_dir / f"page_{page_num:03d}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                saved_paths.append(screenshot_path)
                logger.debug(f"Screenshot saved: {screenshot_path}")

                page_num += 1

                # Navigate to next page
                try:
                    await page.keyboard.press("ArrowRight")
                    await asyncio.sleep(1)
                except Exception:
                    break

            except Exception as e:
                logger.error(f"Error taking screenshot: {e}")
                break

        return saved_paths

    async def _retrieve_via_download(
        self, page: Page, max_pages: Optional[int] = None
    ) -> List[Path]:
        """Retrieve images by finding and downloading direct image URLs."""
        saved_paths = []

        # Find all image elements on the page
        images = await page.query_selector_all("img")

        page_num = 1
        for img in images:
            if max_pages and page_num > max_pages:
                break

            try:
                src = await img.get_attribute("src")
                if src:
                    # Download the image
                    if src.startswith("data:image"):
                        # Handle base64 encoded images
                        image_data = self._decode_base64_image(src)
                        if image_data:
                            path = self._save_image(image_data, page_num)
                            if path:
                                saved_paths.append(path)
                                page_num += 1
                    else:
                        # Handle URL images
                        response = await page.request.get(src)
                        if response.ok:
                            image_data = await response.body()
                            path = self._save_image(image_data, page_num)
                            if path:
                                saved_paths.append(path)
                                page_num += 1
            except Exception as e:
                logger.debug(f"Failed to download image: {e}")

        return saved_paths

    def _decode_base64_image(self, data_url: str) -> Optional[bytes]:
        """Decode a base64 data URL to bytes."""
        try:
            # Extract the base64 part
            match = re.match(r"data:image/[^;]+;base64,(.+)", data_url)
            if match:
                return base64.b64decode(match.group(1))
        except Exception as e:
            logger.debug(f"Failed to decode base64 image: {e}")
        return None

    def _save_image(self, image_data: bytes, page_num: int) -> Optional[Path]:
        """Save image data to disk with appropriate extension."""
        try:
            # Skip empty or too-small files
            if not image_data or len(image_data) < 100:
                logger.debug(f"Skipping empty or too-small file ({len(image_data)} bytes)")
                return None

            # Detect file type from content
            extension = None

            # Check for SVG/SVGZ (prioritize these for Calameo)
            if image_data.startswith(b'\x1f\x8b'):  # gzip header
                extension = ".svgz"
            elif image_data.startswith(b'<?xml') or image_data.startswith(b'<svg'):
                extension = ".svg"
            elif image_data.startswith(b'\xff\xd8\xff'):  # JPEG
                extension = ".jpg"
            elif image_data.startswith(b'\x89PNG'):  # PNG header
                extension = ".png"

            # For Calameo, only accept SVG/SVGZ files
            if self.is_calameo:
                if extension not in [".svg", ".svgz"]:
                    logger.debug(f"Skipping non-SVG file for Calameo (detected: {extension})")
                    return None

            # Fallback to .png if type detection failed
            if extension is None:
                extension = ".png"

            output_path = self.output_dir / f"page_{page_num:03d}{extension}"
            with open(output_path, "wb") as f:
                f.write(image_data)
            logger.info(f"Saved {extension} image: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return None

    def retrieve_images_sync(
        self,
        url: str,
        strategy: str = "intercept",
        max_pages: Optional[int] = None,
    ) -> List[Path]:
        """
        Synchronous wrapper for retrieve_images.

        Args:
            url: Book viewer URL
            strategy: Retrieval strategy
            max_pages: Maximum number of pages

        Returns:
            List of paths to saved images
        """
        return asyncio.run(self.retrieve_images(url, strategy, max_pages))
