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


class NayatelScraper(BaseScraper):
    provider_code = "nayatel"
    utility_type = "internet"
    consumer_number_pattern = r"^[A-Z0-9]{6,12}$"

    BILL_URL = "https://nayatel.com/selfcare/bill-inquiry/"

    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        if not self.validate_consumer_number(consumer_number):
            from app.scrapers.base import InvalidConsumerNumberError
            raise InvalidConsumerNumberError(
                f"Invalid Nayatel account number: {consumer_number}"
            )

        async with get_client() as client:
            try:
                resp = await client.post(
                    self.BILL_URL,
                    data={"account_no": consumer_number},
                )
                resp.raise_for_status()
            except Exception as e:
                raise PortalUnreachableError(
                    f"Nayatel portal unreachable: {e}"
                ) from e

            html = resp.text

            if "captcha" in html.lower() or "g-recaptcha" in html.lower():
                raise CaptchaDetectedError(
                    "Nayatel portal requires CAPTCHA. "
                    "Falling back to manual bill entry."
                )

            if "no record" in html.lower() or "invalid" in html.lower():
                raise NoBillFoundError(
                    f"No bill found for Nayatel account {consumer_number}"
                )

            return self._parse_bill(html, consumer_number)

    def _parse_bill(self, html: str, consumer_number: str) -> ScrapedBill:
        soup = BeautifulSoup(html, "lxml")
        bill = ScrapedBill()
        bill.raw_data = {"html_length": len(html), "account_no": consumer_number}

        try:
            table = soup.find("table", {"class": ["bill", "invoice"]})
            if not table:
                tables = soup.find_all("table")
                if len(tables) >= 2:
                    table = tables[1]

            if not table:
                raise ParsingFailedError(
                    "Could not locate bill table in Nayatel response"
                )

            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                text = " ".join(c.get_text(strip=True) for c in cells)

                if "issue date" in text.lower():
                    bill.issue_date = self._extract_date(text)
                elif "due date" in text.lower():
                    bill.due_date = self._extract_date(text)
                elif "payable" in text.lower() or "amount" in text.lower():
                    bill.amount_payable = self._extract_amount(text)
                elif "arrear" in text.lower():
                    bill.arrears = self._extract_amount(text)
                elif "tax" in text.lower():
                    bill.taxes = self._extract_amount(text)

        except Exception as e:
            raise ParsingFailedError(
                f"Failed to parse Nayatel bill: {e}"
            ) from e

        if bill.amount_payable == 0 and bill.due_date is None:
            raise ParsingFailedError("Parsed Nayatel bill data appears empty")

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
