import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from phishing_web_collector.models import FeedSource, PhishingEntry
from phishing_web_collector.taxonomies import RefreshInterval

logger = logging.getLogger(__name__)


class AbstractFeed(ABC):
    """Abstract base class for feed providers."""

    FEED_TYPE: FeedSource
    INTERVAL: int = RefreshInterval.DAILY.value
    FILE_EXTENSION: str = "txt"

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path) / self.FEED_TYPE.value
        self.storage_path.mkdir(exist_ok=True, parents=True)

    @abstractmethod
    def parse_feed(self, raw_data: str) -> List[PhishingEntry]:
        """Parse the raw feed data and return a list of PhishingEntry objects."""
        pass

    @abstractmethod
    async def fetch_feed(self) -> Optional[str]:
        """Fetch the feed data asynchronously and return it as a string."""
        pass

    @abstractmethod
    def fetch_feed_sync(self) -> Optional[str]:
        """Fetch the feed data synchronously and return it as a string."""
        pass

    # --- ASYNC ---
    async def refresh(self, force: bool = False) -> None:
        """Refresh the feed data asynchronously."""
        if force or self._should_refresh():
            logger.info(f"Refreshing feed: {self.FEED_TYPE.value}")
            raw_data = await self.fetch_feed()
            self._process_raw_data(raw_data)
        else:
            logger.info(f"Skipping refresh, feed is up to date: {self.FEED_TYPE.value}")

    async def retrieve(self) -> List["PhishingEntry"]:
        """Retrieve entries from the feed asynchronously."""
        await self.refresh()
        return self._retrieve_entries()

        # --- SYNC ---

    def refresh_sync(self, force: bool = False) -> None:
        """Refresh the feed data synchronously."""
        if force or self._should_refresh():
            logger.info(f"Refreshing feed: {self.FEED_TYPE.value}")
            raw_data = self.fetch_feed_sync()
            self._process_raw_data(raw_data)
        else:
            logger.info(f"Skipping refresh, feed is up to date: {self.FEED_TYPE.value}")

    def retrieve_sync(self) -> List["PhishingEntry"]:
        """Retrieve entries from the feed synchronously."""
        self.refresh_sync()
        return self._retrieve_entries()

    def _get_feed_path(self) -> Path:
        """Get the file path for the current feed based on the timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H")
        return (
            self.storage_path
            / f"{self.FEED_TYPE.value}_{timestamp}.{self.FILE_EXTENSION}"
        )

    def _should_refresh(self) -> bool:
        """Determine if the feed should be refreshed based on the last modified time and the refresh interval."""
        feed_path = self._get_feed_path()

        if not feed_path.exists():
            return True

        file_mtime = feed_path.stat().st_mtime

        now = time.time()
        interval_sec = self.INTERVAL
        should_refresh = (now - file_mtime) > interval_sec

        return should_refresh

    def _process_raw_data(self, raw_data: str) -> str:
        """Process and save the raw feed data to a file."""
        if raw_data:
            feed_path = self._get_feed_path()
            feed_path.write_text(raw_data, encoding="utf-8")
            logger.info(f"Feed saved: {feed_path}")
        else:
            logger.warning(
                f"Skipping save - No data fetched for {self.FEED_TYPE.value}"
            )

    def _retrieve_entries(self) -> List["PhishingEntry"]:
        """Retrieve and parse all entries from the stored feed files."""
        files = sorted(self.storage_path.iterdir(), key=lambda f: f.stat().st_mtime)
        if not files:
            logger.warning(f"No data found for feed: {self.FEED_TYPE.value}")
            return []

        logger.info(f"Feed range: {files[0].name} -> {files[-1].name}")

        unique_entries = set()
        for file in files:
            entries = self.parse_feed(file.read_text(encoding="utf-8"))
            unique_entries.update(entries)

        return list(unique_entries)
