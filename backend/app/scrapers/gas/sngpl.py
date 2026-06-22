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


class SngplScraper(BaseScraper):
    provider_code = "sngpl"
    utility_type = "gas"
    consumer_number_pattern = r"^\d{10,11}$"

    BILL_URL = "https://www.sngpl.com.pk/web/billing-system/"

    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        if not self.validate_consumer_number(consumer_number):
            from app.scrapers.base import InvalidConsumerNumberError
            raise InvalidConsumerNumberError(
                f"Invalid SNGPL consumer number: {consumer_number}"
            )

        async with get_client() as client:
            try:
                resp = await client.get(self.BILL_URL)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                form = soup.find("form")
                action = form.get("action") if form else self.BILL_URL
                if action and not action.startswith("http"):
                    action = self.BILL_URL.rstrip("/") + "/" + action.lstrip("/")

                post_url = action or self.BILL_URL
                payload = {"consumer_no": consumer_number}
                resp2 = await client.post(post_url, data=payload)
                resp2.raise_for_status()
            except Exception as e:
                raise PortalUnreachableError(
                    f"SNGPL portal unreachable: {e}"
                ) from e

            html = resp2.text

            if "captcha" in html.lower() or "g-recaptcha" in html.lower():
                raise CaptchaDetectedError(
                    "SNGPL portal requires CAPTCHA. "
                    "Falling back to manual bill entry."
                )

            if "no record" in html.lower() or "invalid" in html.lower():
                raise NoBillFoundError(
                    f"No bill found for SNGPL consumer {consumer_number}"
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
                    "Could not locate bill table in SNGPL response"
                )

            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                text = " ".join(c.get_text(strip=True) for c in cells)

                if "issue date" in text.lower():
                    dt = self._extract_date(text)
                    if dt:
                        bill.issue_date = dt
                if "due date" in text.lower():
                    dt = self._extract_date(text)
                    if dt:
                        bill.due_date = dt
                if "payable" in text.lower() or "amount" in text.lower():
                    amt = self._extract_amount(text)
                    if amt:
                        bill.amount_payable = amt
                if "unit" in text.lower() or "mmbtu" in text.lower():
                    units = self._extract_amount(text)
                    if units:
                        bill.units_consumed = units
                if "arrear" in text.lower():
                    arr = self._extract_amount(text)
                    if arr:
                        bill.arrears = arr
                if "tax" in text.lower():
                    tax = self._extract_amount(text)
                    if tax:
                        bill.taxes = tax

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
                f"Failed to parse SNGPL bill: {e}"
            ) from e

        if bill.amount_payable == 0 and bill.due_date is None:
            raise ParsingFailedError(
                "Parsed SNGPL bill data appears empty"
            )

        return bill

    @staticmethod
    def _extract_date(text: str) -> str | None:
        m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        cleaned = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "", text)
        m = re.search(r"(\d+[\.,]?\d*)", cleaned.replace(",", ""))
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                if val < 500000 and not (m.group(1).replace(",", "").isdigit() and len(m.group(1).replace(",", "")) >= 9):
                    return val
                return None
            except ValueError:
                return None
        return None
