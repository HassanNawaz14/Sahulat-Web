from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScrapedBill:
    consumer_name: str = ""
    issue_date: str | None = None
    due_date: str | None = None
    status: str | None = None
    amount_payable: float = 0.0
    units_consumed: float | None = None
    previous_reading: float | None = None
    current_reading: float | None = None
    arrears: float = 0.0
    taxes: float = 0.0
    surcharges: float = 0.0
    meter_rent: float = 0.0
    fc_surcharge: float = 0.0
    tariff_slab: str | None = None
    raw_data: dict | None = None


class ScraperError(Exception):
    pass


class InvalidConsumerNumberError(ScraperError):
    pass


class PortalUnreachableError(ScraperError):
    pass


class ParsingFailedError(ScraperError):
    pass


class CaptchaDetectedError(ScraperError):
    pass


class NoBillFoundError(ScraperError):
    pass


class BaseScraper(ABC):
    provider_code: str = ""
    utility_type: str = ""
    consumer_number_pattern: str = ""
    requires_captcha: bool = False

    @abstractmethod
    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        ...

    def validate_consumer_number(self, consumer_number: str) -> bool:
        import re
        return bool(re.match(self.consumer_number_pattern, consumer_number.strip()))
