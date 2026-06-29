"""PITC-hosted bill scraper for all Punjab DISCOs.

PITC (Punjab IT Board) hosts bill portals for all 9 Punjab DISCOs
on the same ASP.NET backend at bill.pitc.com.pk/{disco}bill.

This scraper handles all of them with identical form POST logic.
"""
import logging
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

logger = logging.getLogger(__name__)

DISCO_CODES = {
    "lesco": "lesco",
    "gepco": "gepco",
    "fesco": "fesco",
    "mepco": "mepco",
    "iesco": "iesco",
    "pesco": "pesco",
    "qesco": "qesco",
    "hesco": "hesco",
    "sepco": "sepco",
}

REF_NO_PATTERN = r"^\d{8,14}$"


class PitcBillScraper(BaseScraper):
    """Generic scraper for any PITC-hosted DISCO bill portal."""

    def __init__(self, provider_code: str):
        if provider_code not in DISCO_CODES:
            raise ValueError(f"Unknown PITC DISCO: {provider_code}")
        self.provider_code = provider_code
        self.utility_type = "electricity"
        self.consumer_number_pattern = REF_NO_PATTERN

    def validate_consumer_number(self, consumer_number: str) -> bool:
        normalized = re.sub(r"[^0-9]", "", consumer_number.strip())
        return super().validate_consumer_number(normalized)

    @property
    def _base_url(self) -> str:
        return f"https://bill.pitc.com.pk/{self.provider_code}bill"

    async def fetch_bill(self, consumer_number: str) -> ScrapedBill:
        raw = consumer_number.strip()
        normalized = re.sub(r"[^0-9]", "", raw)

        if not self.validate_consumer_number(raw):
            from app.scrapers.base import InvalidConsumerNumberError
            raise InvalidConsumerNumberError(
                f"Invalid {self.provider_code.upper()} reference: {raw}"
            )

        async with get_client(timeout=90) as client:
            try:
                form_resp = await client.get(self._base_url)
                form_resp.raise_for_status()
            except Exception as e:
                logger.exception("GET %s failed: %s: %s", self._base_url, type(e).__name__, e)
                raise PortalUnreachableError(
                    f"{self.provider_code.upper()} PITC portal unreachable: {e}"
                ) from e

            form_html = form_resp.text
            
            if "g-recaptcha" in form_html or "recaptcha/api" in form_html:
                raise CaptchaDetectedError(
                    f"{self.provider_code.upper()} portal requires reCAPTCHA. "
                    "Falling back to manual bill entry."
                )

            viewstate = self._extract_field(form_html, "__VIEWSTATE")
            eventvalidation = self._extract_field(form_html, "__EVENTVALIDATION")
            token = self._extract_field(form_html, "__RequestVerificationToken")

            payload = {
                "__VIEWSTATE": viewstate,
                "__EVENTVALIDATION": eventvalidation,
                "__RequestVerificationToken": token,
                "rbSearchByList": "refno",
                "searchTextBox": normalized,
                "btnSearch": "Search",
            }

            try:
                bill_resp = await client.post(self._base_url, data=payload)
                bill_resp.raise_for_status()
            except Exception as e:
                logger.exception("POST %s failed: %s: %s", self._base_url, type(e).__name__, e)
                raise PortalUnreachableError(
                    f"{self.provider_code.upper()} bill fetch failed: {e}"
                ) from e

            bill_html = bill_resp.text

            if "searchTextBox" in bill_html:
                raise NoBillFoundError(
                    f"No bill found for {self.provider_code.upper()} ref {normalized}. "
                    "Portal returned the search form instead of bill data."
                )

            if "g-recaptcha" in bill_html or "recaptcha/api" in bill_html:
                raise CaptchaDetectedError(
                    f"{self.provider_code.upper()} portal requires reCAPTCHA"
                )

            return self._parse_bill(bill_html, normalized)

    def _parse_bill(self, html: str, consumer_number: str) -> ScrapedBill:
        soup = BeautifulSoup(html, "lxml")
        bill = ScrapedBill()
        bill.raw_data = {
            "html_length": len(html),
            "ref_no": consumer_number,
            "provider": self.provider_code,
        }

        try:
            for tag in soup.find_all(["script", "style"]):
                tag.decompose()

            self._parse_consumer_name(soup, bill)
            self._parse_meter_readings(soup, bill)
            self._parse_charges(soup, bill)
            self._parse_payable_amount(soup, bill)
            self._parse_dates(soup, bill)

            if bill.amount_payable == 0 and bill.due_date is None:
                raise ParsingFailedError(
                    f"Parsed {self.provider_code.upper()} bill data appears empty. "
                    f"No amount_payable or due_date found."
                )

        except ParsingFailedError:
            raise
        except Exception as e:
            raise ParsingFailedError(
                f"Failed to parse {self.provider_code.upper()} bill: {e}"
            ) from e

        return bill

    def _parse_consumer_name(self, soup: BeautifulSoup, bill: ScrapedBill) -> None:
        for span in soup.select(".en-lbl"):
            if "NAME & ADDRESS" in span.get_text():
                label_row = span.find_parent("div")
                if label_row:
                    val_div = label_row.find_next_sibling("div")
                    if val_div:
                        bill.consumer_name = val_div.get_text(strip=True)[:150]
                return

    def _parse_meter_readings(self, soup: BeautifulSoup, bill: ScrapedBill) -> None:
        labels = {"PREVIOUS READING": "previous_reading", "PRESENT READING": "current_reading", "UNITS": "units_consumed"}
        for span in soup.select(".en-lbl"):
            text = span.get_text(strip=True)
            if text not in labels:
                continue
            attr = labels[text]
            cell = span.find_parent("div", class_="grid-col-cell")
            if not cell:
                continue
            val_div = cell.find("div", class_="val-space")
            if not val_div:
                continue
            val_str = re.sub(r"[^0-9.]", "", val_div.get_text())
            if val_str:
                try:
                    setattr(bill, attr, float(val_str))
                except ValueError:
                    pass

    def _parse_charges(self, soup: BeautifulSoup, bill: ScrapedBill) -> None:
        for row in soup.select(".charges-bd-row"):
            label_el = row.select_one(".charges-bd-en")
            val_el = row.select_one(".charges-bd-val")
            if not label_el or not val_el:
                continue
            text = label_el.get_text(strip=True).lower()
            val_str = re.sub(r"[^0-9.-]", "", val_el.get_text(strip=True))
            try:
                val = float(val_str)
            except ValueError:
                continue
            if "taxes" in text:
                bill.taxes = val
            elif "arrears" in text:
                bill.arrears = val
            elif "total fpa" in text or ("fpa" in text and "total" in text):
                bill.fc_surcharge = abs(val)
            elif "meter rent" in text:
                bill.meter_rent = val

    def _parse_payable_amount(self, soup: BeautifulSoup, bill: ScrapedBill) -> None:
        grid = soup.select_one(".slip-matrix-grid")
        if not grid:
            return
        values = grid.select(".slip-matrix-value")
        if len(values) >= 3:
            val_str = re.sub(r"[^0-9.]", "", values[0].get_text(strip=True))
            if val_str:
                try:
                    bill.amount_payable = round(float(val_str))
                except ValueError:
                    pass
            due_raw = values[2].get_text(strip=True)
            if due_raw and not bill.due_date:
                bill.due_date = due_raw.strip()

    def _parse_dates(self, soup: BeautifulSoup, bill: ScrapedBill) -> None:
        if bill.issue_date and bill.due_date:
            return
        labels = {"ISSUE DATE": "issue_date", "DUE DATE": "due_date"}
        for span in soup.select("span"):
            text = span.get_text(strip=True)
            if text not in labels:
                continue
            attr = labels[text]
            cell = span.find_parent("div", class_="right-grid-cell")
            if not cell:
                continue
            for el in cell.find_all(["div", "span"]):
                txt = el.get_text(strip=True)
                if re.search(r"\d{1,2}\s+[A-Z]{3}\s+\d{2,4}", txt):
                    setattr(bill, attr, txt)
                    break

    @staticmethod
    def _extract_field(html: str, field_name: str) -> str:
        m = re.search(
            rf'{field_name}"[^>]*value="([^"]*)"',
            html,
        )
        return m.group(1) if m else ""

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
