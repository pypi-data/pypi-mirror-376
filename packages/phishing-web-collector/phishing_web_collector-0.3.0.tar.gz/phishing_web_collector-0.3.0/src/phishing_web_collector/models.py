from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from phishing_web_collector.taxonomies import FeedSource


@dataclass(frozen=True)
class PhishingEntry:
    """Data class representing a phishing entry."""

    url: str
    source: FeedSource
    fetch_date: datetime
    targeted_url: Optional[str] = None
    reference_url: Optional[str] = None

    def __hash__(self):
        return hash(self.url)


EntryFilter = Callable[["PhishingEntry"], bool]
