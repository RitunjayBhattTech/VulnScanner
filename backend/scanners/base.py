from abc import ABC, abstractmethod
from typing import List

from backend.schemas.finding import RawFinding


class BaseScanner(ABC):
    """Abstract base class for all scanners."""

    def __init__(self, scan_id: str, target: str, scope: list, rate_limiter):
        self.scan_id = scan_id
        self.target = target
        self.scope = scope
        self.rate_limiter = rate_limiter

    @abstractmethod
    async def run(self) -> List[RawFinding]:
        """Execute the scan and return raw findings."""
        pass

    @abstractmethod
    def get_scanner_name(self) -> str:
        """Return the name of this scanner."""
        pass