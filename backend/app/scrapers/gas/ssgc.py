import re

from bs4 import BeautifulSoup

from app.scrapers.base import (
    BaseScraper,
    ScrapedBill,
    CaptchaDetectedError,
    NoBillFoundError,
    ParsingFailedError,
    PortalUnreachableError,
)
from app.scrapers.common.http_client import get_client


class SsgcScraper(BaseScraper):
    provider_code = "ssgc"
    utility_type = "gas"
    consumer_number_pattern = r"^\d{10,12}$"

    BILL_URL = "https://viewbill.ssgc.com.pk/web/billpdfs/"

    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        if not self.validate_consumer_number(consumer_number):
            from app.scrapers.base import InvalidConsumerNumberError
            raise InvalidConsumerNumberError(
                f"Invalid SSGC consumer number: {consumer_number}"
            )

        async with get_client() as client:
            try:
                resp = await client.get(
                    self.BILL_URL,
                    params={"consumer_id": consumer_number},
                )
                resp.raise_for_status()
            except Exception as e:
                raise PortalUnreachableError(
                    f"SSGC portal unreachable: {e}"
                ) from e

            html = resp.text

            if "captcha" in html.lower() or "g-recaptcha" in html.lower():
                raise CaptchaDetectedError(
                    "SSGC portal requires CAPTCHA. "
                    "Falling back to manual bill entry."
                )

            if "no record" in html.lower() or "invalid" in html.lower():
                raise NoBillFoundError(
                    f"No bill found for SSGC consumer {consumer_number}"
                )

            return self._parse_bill(html, consumer_number)

    def _parse_bill(self, html: str, consumer_number: str) -> ScrapedBill:
        soup = BeautifulSoup(html, "lxml")
        bill = ScrapedBill()
        bill.raw_data = {"html_length": len(html), "consumer_no": consumer_number}

        try:
            table = soup.find("table", {"class": ["bill", "invoice"]})
            if not table:
                tables = soup.find_all("table")
                if len(tables) >= 2:
                    table = tables[1]

            if not table:
                raise ParsingFailedError(
                    "Could not locate bill table in SSGC response"
                )

            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                text = " ".join(c.get_text(strip=True) for c in cells)

                if "due date" in text.lower():
                    bill.due_date = self._extract_date(text)
                elif "payable" in text.lower() or "amount" in text.lower():
                    bill.amount_payable = self._extract_amount(text)
                elif "unit" in text.lower() or "mmbtu" in text.lower():
                    bill.units_consumed = self._extract_amount(text)
                elif "arrear" in text.lower():
                    bill.arrears = self._extract_amount(text)
                elif "tax" in text.lower():
                    bill.taxes = self._extract_amount(text)
                elif "late payment" in text.lower():
                    bill.surcharges = self._extract_amount(text)

            name_tag = soup.find(
                ["td", "span", "div"],
                string=re.compile(r"(consumer|customer|name)", re.I),
            )
            if name_tag:
                parent = name_tag.find_parent(["td", "tr", "div"])
                if parent:
                    bill.consumer_name = parent.get_text(strip=True)

        except Exception as e:
            raise ParsingFailedError(
                f"Failed to parse SSGC bill: {e}"
            ) from e

        if bill.amount_payable == 0 and bill.due_date is None:
            raise ParsingFailedError(
                "Parsed SSGC bill data appears empty"
            )

        return bill

    @staticmethod
    def _extract_date(text: str) -> str | None:
        m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        m = re.search(r"(\d+[\.,]?\d*)", text.replace(",", ""))
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None
