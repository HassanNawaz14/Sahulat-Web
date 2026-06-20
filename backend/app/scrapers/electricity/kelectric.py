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


class KElectricScraper(BaseScraper):
    provider_code = "kelectric"
    utility_type = "electricity"
    consumer_number_pattern = r"^\d{10,13}$"

    BILL_URL = "https://www.ke.com.pk/bill-inquiry/"

    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        if not self.validate_consumer_number(consumer_number):
            from app.scrapers.base import InvalidConsumerNumberError
            raise InvalidConsumerNumberError(
                f"Invalid KE account number: {consumer_number}"
            )

        async with get_client() as client:
            payload = {"account_no": consumer_number}
            try:
                resp = await client.post(self.BILL_URL, data=payload)
                resp.raise_for_status()
            except Exception as e:
                raise PortalUnreachableError(
                    f"K-Electric portal unreachable: {e}"
                ) from e

            html = resp.text

            if "captcha" in html.lower() or "g-recaptcha" in html.lower():
                raise CaptchaDetectedError(
                    "K-Electric portal requires CAPTCHA. "
                    "Falling back to manual bill entry."
                )

            if "no record" in html.lower() or "invalid" in html.lower():
                raise NoBillFoundError(
                    f"No bill found for KE account {consumer_number}"
                )

            return self._parse_bill(html, consumer_number)

    def _parse_bill(
        self, html: str, consumer_number: str
    ) -> ScrapedBill:
        soup = BeautifulSoup(html, "lxml")
        bill = ScrapedBill()
        bill.raw_data = {"html_length": len(html), "account_no": consumer_number}

        try:
            table = soup.find("table", {"class": ["bill", "invoice"]})
            if not table:
                table = soup.find("div", {"class": ["bill", "invoice"]})
            if not table:
                divs = soup.find_all("div", {"class": re.compile(r"bill|invoice", re.I)})
                if divs:
                    table = divs[0]
            if not table:
                tables = soup.find_all("table")
                if len(tables) >= 2:
                    table = tables[1]

            if not table:
                raise ParsingFailedError(
                    "Could not locate bill table in KE response"
                )

            rows = table.find_all(["tr", "div"])
            for row in rows:
                text = row.get_text(strip=True)
                if "issue date" in text.lower():
                    bill.issue_date = self._extract_date(text)
                elif "due date" in text.lower():
                    bill.due_date = self._extract_date(text)
                elif "payable" in text.lower():
                    bill.amount_payable = self._extract_amount(text)
                elif "unit" in text.lower() or "kwh" in text.lower():
                    bill.units_consumed = self._extract_amount(text)
                elif "arrear" in text.lower():
                    bill.arrears = self._extract_amount(text)
                elif "fc" in text.lower() or "fuel" in text.lower():
                    bill.fc_surcharge = self._extract_amount(text)
                elif "tax" in text.lower():
                    bill.taxes = self._extract_amount(text)

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
                f"Failed to parse KE bill HTML: {e}"
            ) from e

        if bill.amount_payable == 0 and bill.due_date is None:
            raise ParsingFailedError(
                "Parsed KE bill data appears empty — layout may have changed"
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
