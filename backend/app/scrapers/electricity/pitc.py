"""PITC-hosted bill scraper for all Punjab DISCOs.

PITC (Punjab IT Board) hosts bill portals for all 9 Punjab DISCOs
on the same ASP.NET backend at bill.pitc.com.pk/{disco}bill.

This scraper handles all of them with identical form POST logic.
"""
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

        async with get_client() as client:
            try:
                form_resp = await client.get(self._base_url)
                form_resp.raise_for_status()
            except Exception as e:
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

            tables = soup.find_all("table")

            self._parse_meter_table(tables, bill)
            self._parse_header_table(tables, bill)
            self._parse_consumer_table(tables, bill)
            self._parse_charges_table(tables, bill)
            self._parse_summary_table(tables, bill)

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

    def _parse_header_table(self, tables: list, bill: ScrapedBill) -> None:
        if len(tables) < 1:
            return
        rows = tables[0].find_all("tr")
        if len(rows) < 2:
            return
        cells = rows[1].find_all(["td", "th"])
        texts = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]

        issue_date = None
        due_date = None
        for i, cell_text in enumerate(texts):
            if "issue date" in cell_text.lower() or ("issue" in cell_text.lower() and "date" not in cell_text.lower()):
                if i + 1 < len(texts):
                    issue_date = texts[i + 1]
            if "due date" in cell_text.lower() or ("due" in cell_text.lower() and "date" not in cell_text.lower()):
                if i + 1 < len(texts):
                    due_date = texts[i + 1]

        header_row_1 = tables[0].find_all("tr")[0]
        header_cells = [c.get_text(strip=True) for c in header_row_1.find_all(["td", "th"])]
        value_row_1 = texts

        for i, hdr in enumerate(header_cells):
            hl = hdr.lower()
            if i < len(value_row_1):
                v = value_row_1[i]
                if "issue date" in hl:
                    bill.issue_date = v
                elif "due date" in hl:
                    bill.due_date = v

        if not bill.issue_date and issue_date:
            bill.issue_date = issue_date
        if not bill.due_date and due_date:
            bill.due_date = due_date

    def _parse_consumer_table(self, tables: list, bill: ScrapedBill) -> None:
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                for cell in cells:
                    spans = cell.find_all("span")
                    for span in spans:
                        text = span.get_text(strip=True)
                        if re.search(r"\bS/O\b", text, re.IGNORECASE):
                            bill.consumer_name = text[:150]
                            return

    def _parse_charges_table(self, tables: list, bill: ScrapedBill) -> None:
        for table in tables:
            rows = table.find_all("tr")
            text_blocks = []
            for row in rows:
                cells = row.find_all(["td", "th"])
                texts = [c.get_text(strip=True) for c in cells]
                text_blocks.append(texts)

            full_text = " ".join(" ".join(t for t in row if t) for row in text_blocks).lower()

            if "units consumed" not in full_text and "cost of electricity" not in full_text:
                continue

            for texts in text_blocks:
                line = " ".join(texts).lower()

                if "units consumed" in line:
                    for possible in texts:
                        val = possible.replace(",", "")
                        if val.replace(".", "").isdigit() and len(val) < 8:
                            bill.units_consumed = float(val)
                            break

                if "arrear" in line and bill.arrears == 0:
                    for possible in texts:
                        val = possible.replace(",", "").replace(" ", "")
                        if val.replace(".", "").isdigit() and len(val) < 10:
                            bill.arrears = float(val)
                            break

                if "meter rent" in line:
                    for possible in texts:
                        val = possible.replace(",", "")
                        if val.replace(".", "").isdigit() and float(val) < 1000:
                            bill.meter_rent = float(val)
                            break

                if ("f.c" in line or "fc" in line or "fuel" in line) and "surcharge" in line:
                    for possible in texts:
                        val = possible.replace(",", "")
                        if val.replace(".", "").lstrip("-").isdigit():
                            bill.fc_surcharge = abs(float(val))
                            break

            break

    def _parse_summary_table(self, tables: list, bill: ScrapedBill) -> None:
        for table in tables:
            rows = table.find_all("tr")
            text_blocks = []
            for row in rows:
                cells = row.find_all(["td", "th"])
                texts = [c.get_text(strip=True) for c in cells]
                text_blocks.append(texts)

            full_text = " ".join(" ".join(t for t in row if t) for row in text_blocks).lower()

            if "payable within" not in full_text and "current bill" not in full_text:
                continue

            for texts in text_blocks:
                line = " ".join(texts).lower()

                if "payable within" in line or "payable with in" in line:
                    for possible in texts:
                        val = possible.replace(",", "")
                        if val.replace(".", "").isdigit() and len(val) < 12:
                            bill.amount_payable = round(float(val))
                            break

                if "current bill" in line:
                    for possible in texts:
                        val = possible.replace(",", "")
                        if val.replace(".", "").isdigit() and len(val) < 12:
                            if bill.amount_payable == 0:
                                bill.amount_payable = round(float(val))
                            break

            break

    def _parse_meter_table(self, tables: list, bill: ScrapedBill) -> None:
        for table in tables:
            rows = table.find_all("tr")
            for ri, row in enumerate(rows):
                cells = row.find_all(["td", "th"])
                cell_texts = [c.get_text(strip=True) for c in cells]
                # Filter out empty and merged-cell duplicates
                seen = set()
                unique_texts = []
                for t in cell_texts:
                    t = t.strip().lower()
                    if t and t not in seen:
                        seen.add(t)
                        unique_texts.append(t)

                if 4 <= len(unique_texts) <= 8:
                    has_prev = any("previous" in t and "reading" in t for t in unique_texts)
                    has_present = any("present" in t and "reading" in t for t in unique_texts)

                    if has_prev and has_present:
                        if ri + 1 < len(rows):
                            next_cells = rows[ri + 1].find_all(["td", "th"])
                            next_texts = [c.get_text(strip=True) for c in next_cells]
                            for ct in next_texts:
                                try:
                                    val = float(ct.replace(",", ""))
                                    if 0 < val < 1000000:
                                        if bill.previous_reading is None:
                                            bill.previous_reading = val
                                        elif bill.current_reading is None:
                                            bill.current_reading = val
                                except ValueError:
                                    pass
                        return

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
