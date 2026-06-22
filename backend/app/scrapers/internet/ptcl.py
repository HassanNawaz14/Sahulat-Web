import base64
import json
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


class PtclScraper(BaseScraper):
    provider_code = "ptcl"
    utility_type = "internet"
    consumer_number_pattern = r"^\d{10,11}$"
    requires_captcha = True

    FORM_URL = "https://ptcl.com.pk/customer/publicbill_payment"
    INQUIRE_URL = "https://ptcl.com.pk/Customer/PublicInquireBill"
    CAPTCHA_URL = "https://ptcl.com.pk/Customer/GenerateCaptcha"

    # Static list of PTCL area codes from the portal, sorted by length descending
    AREA_CODES = [
        "04443", "04947", "04949", "05811", "05815", "05822", "05823", "05824", "05825", "05826", "05827", "05828",
        "0232", "0233", "0235", "0238", "0242", "0243", "0244", "0297", "0298", "0447", "0453", "0454", "0457", "0459",
        "0542", "0543", "0544", "0546", "0547", "0586", "0604", "0606", "0608", "0722", "0723", "0726", "0822", "0823",
        "0824", "0825", "0826", "0828", "0829", "0832", "0833", "0835", "0837", "0838", "0843", "0844", "0847", "0848",
        "0852", "0853", "0855", "0856", "0922", "0923", "0924", "0925", "0926", "0927", "0928", "0932", "0937", "0938",
        "0939", "0942", "0943", "0944", "0945", "0946", "0963", "0965", "0966", "0969", "0992", "0995", "0996", "0997",
        "0998",
        "021", "022", "025", "040", "041", "042", "044", "046", "047", "048", "049", "051", "052", "053", "055", "056",
        "057", "061", "062", "063", "064", "065", "066", "067", "068", "071", "074", "081", "086", "091", "095"
    ]

    def _split_number(self, consumer_number: str) -> tuple[str, str]:
        raw = consumer_number.strip()
        for code in self.AREA_CODES:
            if raw.startswith(code):
                return code, raw[len(code):]
        # Fallback to splitting by first 3 digits
        return raw[:3], raw[3:]

    async def fetch_bill(self, consumer_number: str, account_id: str | None = None) -> ScrapedBill:
        raw = consumer_number.strip()
        if not self.validate_consumer_number(raw):
            from app.scrapers.base import InvalidConsumerNumberError
            raise InvalidConsumerNumberError(
                f"Invalid PTCL account number: {raw}"
            )

        area_code, local_no = self._split_number(raw)

        async with get_client() as client:
            form_resp = await self._get_form(client)
            form_html = form_resp.text

            token = self._extract_csrf_token(form_html)
            if not token:
                raise ParsingFailedError(
                    "Could not extract __RequestVerificationToken from PTCL page"
                )

            base_payload = {
                "__RequestVerificationToken": token,
                "ISEVO_PTCL": "PTCL",
                "IS_FriendBill": "false",
                "Evo_Type_ID": "0",
                "DeptID": "1",
                "Areacode": area_code,
                "Telephone": local_no,
                "InvoiceNo": "",
                "AccID": account_id or "",
                "UFoneNo": "",
            }

            # PTCL always requires captcha; skip OCR since it never works.
            # Try one POST to trigger CaptchaDetectedError, then bail immediately.
            logger.info(
                f"PTCL posting to {self.INQUIRE_URL}, "
                f"area={area_code}, phone={local_no}"
            )
            bill_resp = await self._post_inquiry(client, base_payload)
            try:
                return self._parse_response(bill_resp, raw)
            except CaptchaDetectedError:
                raise
            except ParsingFailedError:
                raise

    async def prepare_captcha(self, consumer_number: str, account_id: str | None = None) -> dict:
        raw = consumer_number.strip()
        area_code, local_no = self._split_number(raw)
        client = get_client()
        try:
            form_resp = await self._get_form(client)
            form_html = form_resp.text
            csrf_token = self._extract_csrf_token(form_html)
            if not csrf_token:
                await client.aclose()
                raise ParsingFailedError("Could not extract CSRF token from PTCL page")
            # Fetch captcha FIRST so PTCL stores captcha code in this session
            img_resp = await client.get(self.CAPTCHA_URL)
            img_resp.raise_for_status()
            captcha_image = base64.b64encode(img_resp.content).decode()
            logger.info(f"PTCL prepare_captcha returning live httpx client (session preserved)")
            return {
                "client": client,
                "csrf_token": csrf_token,
                "captcha_image": captcha_image,
                "area_code": area_code,
                "local_no": local_no,
                "consumer_number": raw,
                "account_id": account_id or "",
            }
        except Exception:
            await client.aclose()
            raise

    async def complete_fetch(self, client, consumer_number: str, csrf_token: str, captcha_solution: str, account_id: str | None = None) -> ScrapedBill:
        raw = consumer_number.strip()
        area_code, local_no = self._split_number(raw)
        payload = {
            "__RequestVerificationToken": csrf_token,
            "ISEVO_PTCL": "PTCL",
            "IS_FriendBill": "false",
            "Evo_Type_ID": "0",
            "DeptID": "1",
            "Areacode": area_code,
            "Telephone": local_no,
            "InvoiceNo": "",
            "AccID": account_id or "",
            "UFoneNo": "",
            "CaptchaInputText": captcha_solution,
        }
        logger.info(
            f"PTCL complete_fetch: reusing live httpx client, "
            f"csrf_token={'set' if csrf_token else 'MISSING'}, "
            f"captcha_digits={len(captcha_solution)}"
        )
        bill_resp = await self._post_inquiry(client, payload)
        body = bill_resp.text
        logger.info(
            f"PTCL complete_fetch: status={bill_resp.status_code}, "
            f"length={len(body)}, type={bill_resp.headers.get('content-type', '')}"
        )
        if len(body) < 500:
            logger.info(f"PTCL complete_fetch response body: {body}")
        return self._parse_response(bill_resp, raw)

    async def refresh_captcha(self, client) -> str:
        img_resp = await client.get(self.CAPTCHA_URL)
        img_resp.raise_for_status()
        return base64.b64encode(img_resp.content).decode()

    async def _get_form(self, client):
        try:
            resp = await client.get(self.FORM_URL)
            resp.raise_for_status()
            return resp
        except Exception as e:
            raise PortalUnreachableError(f"PTCL portal unreachable: {e}") from e

    async def _solve_captcha(self, client) -> str:
        try:
            img_resp = await client.get(self.CAPTCHA_URL)
            img_resp.raise_for_status()
            img_bytes = img_resp.content
        except Exception as e:
            logger.warning(f"Failed to fetch PTCL captcha image: {e}")
            return ""

        try:
            from PIL import Image, ImageFilter
            import io

            img = Image.open(io.BytesIO(img_bytes))
            img = img.convert("L")
            img = img.point(lambda x: 0 if x < 140 else 255)
            img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
            img = img.filter(ImageFilter.SHARPEN)

            try:
                import pytesseract
                text = pytesseract.image_to_string(
                    img, config="--psm 7 -c tessedit_char_whitelist=0123456789"
                )
                digits = re.sub(r"[^0-9]", "", text)
                if len(digits) >= 4 and len(digits) <= 6:
                    logger.info(f"PTCL captcha solved via pytesseract: {digits}")
                    return digits
            except (ImportError, Exception) as e:
                logger.debug(f"pytesseract not available: {e}")

            try:
                from PIL import ImageDraw
                w, h = img.size
                left = w // 5
                top = h // 3
                right = w - left
                bottom = h - top
                digits_found = []
                for i in range(5):
                    x1 = left + (right - left) * i // 5
                    x2 = left + (right - left) * (i + 1) // 5
                    crop = img.crop((x1, top, x2, bottom))
                    pixels = list(crop.getdata())
                    white_pct = sum(1 for p in pixels if p > 200) / len(pixels)
                    if white_pct < 0.5:
                        return ""
                    bbox = crop.getbbox()
                    if bbox:
                        char_img = crop.crop(bbox)
                        cw, ch = char_img.size
                        if cw > 2 and ch > 5:
                            aspect = cw / max(ch, 1)
                            if 0.3 < aspect < 1.0:
                                digits_found.append(str(i))
                if digits_found:
                    return "".join(digits_found)
            except Exception:
                pass

            logger.warning(
                f"PTCL captcha OCR failed: size={img.size}"
            )
        except ImportError:
            logger.warning("Pillow not available, cannot OCR PTCL captcha")

        return ""

    def _extract_csrf_token(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")
        inp = soup.find("input", {"name": "__RequestVerificationToken"})
        return inp.get("value", "") if inp is not None else None

    async def _post_inquiry(self, client, payload):
        try:
            resp = await client.post(self.INQUIRE_URL, data=payload)
            resp.raise_for_status()
            return resp
        except Exception as e:
            raise PortalUnreachableError(f"PTCL bill fetch failed: {e}") from e

    def _parse_response(self, bill_resp, consumer_number: str) -> ScrapedBill:
        body = bill_resp.text
        parsed_payload = body
        ct = (bill_resp.headers.get("content-type", "") or "").lower()

        logger.info(
            f"PTCL response status={bill_resp.status_code} "
            f"length={len(body)} type={ct}"
        )

        if "application/pdf" in ct:
            return self._parse_pdf(bill_resp.content, consumer_number)

        try:
            data = json.loads(body)
            if isinstance(data, dict):
                msg = data.get("message", "") or ""
                success_val = data.get("success", 0)
                logger.info(f"PTCL JSON response: success={success_val} message={msg!r}")
                if success_val > 0:
                    captcha_keywords = ["captcha", "verification", "invalid", "wrong"]
                    if any(kw in msg.lower() for kw in captcha_keywords):
                        raise CaptchaDetectedError(
                            f"PTCL portal requires CAPTCHA: {msg}"
                        )
                    raise NoBillFoundError(f"PTCL: {msg}" if msg else "No bill found")
                if msg:
                    parsed_payload = msg
        except (json.JSONDecodeError, ValueError):
            pass

        soup = BeautifulSoup(parsed_payload, "lxml")

        for tag in soup.find_all(["script", "style"]):
            tag.decompose()

        error_msg = self._extract_error(soup)
        if error_msg:
            lower = error_msg.lower()
            if "captcha" in lower or "verification" in lower:
                raise CaptchaDetectedError(f"PTCL: {error_msg}")
            if any(
                marker in lower
                for marker in ("no record", "not found", "no bill", "no data", "invalid")
            ):
                raise NoBillFoundError(error_msg)

        try:
            bill = self._parse_bill_html(parsed_payload, consumer_number)
        except NoBillFoundError:
            bill = None

        if bill is not None:
            return bill

        if self._is_search_form(soup):
            raise NoBillFoundError(
                error_msg or f"No bill found for PTCL {consumer_number}"
            )

        raise ParsingFailedError(
            f"PTCL response did not contain bill data for {consumer_number}"
        )

    @staticmethod
    def _is_search_form(soup) -> bool:
        text = soup.get_text(separator=" ", strip=True).lower()
        bill_indicators = [
            "amount payable",
            "total payable",
            "bill amount",
            "issue date",
            "due date",
            "invoice no",
            "consumer name",
            "billing month",
            "payable",
        ]
        if any(ind in text for ind in bill_indicators):
            return False

        form_indicators = (
            "phone",
            "mobile",
            "areacode",
            "area code",
            "account",
            "invoice",
            "captcha",
            "search bill",
            "inquire bill",
        )
        for form in soup.find_all("form"):
            form_text = form.get_text(separator=" ", strip=True).lower()
            if any(ind in form_text for ind in form_indicators):
                return True
            field_values = []
            for field in form.find_all(["input", "select", "textarea"]):
                field_values.extend(
                    [
                        field.get("name", ""),
                        field.get("id", ""),
                        field.get("placeholder", ""),
                        field.get("aria-label", ""),
                    ]
                )
            field_blob = " ".join(filter(None, field_values)).lower()
            if any(ind in field_blob for ind in form_indicators):
                return True
        return False

    @staticmethod
    def _extract_error(soup) -> str | None:
        for tag in soup.find_all(["span", "div", "label", "font"]):
            txt = tag.get_text(strip=True)
            if txt and (
                "no record" in txt.lower()
                or "invalid" in txt.lower()
                or "not found" in txt.lower()
                or "error" in txt.lower()
            ):
                return txt
        return None

    def _parse_bill_html(self, html: str, consumer_number: str) -> ScrapedBill:
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator="\n")
        bill = ScrapedBill()
        bill.raw_data = {"html_length": len(html), "text_length": len(text), "phone_no": consumer_number}

        for tag in soup.find_all(["script", "style"]):
            tag.decompose()

        bill.amount_payable = self._find_amount(soup, text)
        bill.due_date = self._find_date(soup, text, "due")
        bill.issue_date = self._find_date(soup, text, "issue")
        bill.status = self._find_status(soup, text)
        bill.arrears = self._find_numeric(soup, text, "arrear")
        bill.taxes = self._find_numeric(soup, text, "tax")

        if not self._has_bill_content(bill):
            raise NoBillFoundError(
                f"No bill found for PTCL {consumer_number}"
            )

        return bill

    @staticmethod
    def _find_status(soup: BeautifulSoup, text: str | None = None) -> str | None:
        text = text or soup.get_text(separator="\n")
        lower_text = re.sub(r"\s+", " ", text.lower())
        m = re.search(r"\bstatus\b[^a-z0-9]{0,40}\b(paid|unpaid|overdue)\b", lower_text)
        if m:
            return m.group(1)
        m = re.search(r"\b(paid|unpaid|overdue)\b[^a-z0-9]{0,40}\bstatus\b", lower_text)
        if m:
            return m.group(1)
        for line in text.split("\n"):
            lower = line.lower().strip()
            if "status" not in lower:
                continue
            if "paid" in lower:
                return "paid"
            if "unpaid" in lower:
                return "unpaid"
            if "overdue" in lower:
                return "overdue"
        return None

    @staticmethod
    def _has_bill_content(bill: ScrapedBill) -> bool:
        return any(
            [
                bill.amount_payable,
                bill.due_date,
                bill.issue_date,
                bill.status,
                bill.units_consumed,
                bill.previous_reading,
                bill.current_reading,
                bill.arrears,
                bill.taxes,
                bill.surcharges,
                bill.meter_rent,
                bill.fc_surcharge,
                bill.tariff_slab,
            ]
        )

    def _parse_pdf(self, content: bytes, consumer_number: str) -> ScrapedBill:
        import io as _io
        import pdfplumber

        bill = ScrapedBill()
        bill.raw_data = {"source": "pdf", "phone_no": consumer_number}
        try:
            with pdfplumber.open(_io.BytesIO(content)) as pdf:
                text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
            bill.raw_data["pdf_text_length"] = len(text)
            for line in text.split("\n"):
                lower = line.lower()
                if "issue date" in lower or "bill date" in lower or "invoice date" in lower:
                    bill.issue_date = self._extract_date(line)
                if "due date" in lower or "due on" in lower:
                    bill.due_date = self._extract_date(line)
                if (
                    "total due" in lower
                    or "amount due" in lower
                    or "payable" in lower
                    or "total" in lower
                ):
                    amt = self._extract_amount(line)
                    if amt and amt > bill.amount_payable:
                        bill.amount_payable = amt
                if "arrear" in lower:
                    bill.arrears = self._extract_amount(line) or 0
            if bill.amount_payable == 0 and bill.due_date is None:
                raise ParsingFailedError("Parsed PTCL PDF bill data appears empty")
            return bill
        except ParsingFailedError:
            raise
        except Exception as e:
            raise ParsingFailedError(f"Failed to parse PTCL PDF bill: {e}") from e

    @staticmethod
    def _find_amount(soup: BeautifulSoup, text: str | None = None) -> float:
        text = text or soup.get_text(separator="\n")
        flat_text = re.sub(r"\s+", " ", text.lower())
        patterns = [
            r"\b(?:total due amount|amount payable|bill amount|total payable|payable|due amount)\b[^0-9]{0,40}([0-9][0-9,]*(?:\.[0-9]+)?)",
            r"([0-9][0-9,]*(?:\.[0-9]+)?)\b[^0-9]{0,40}\b(?:total due amount|amount payable|bill amount|total payable|payable|due amount)\b",
        ]
        for pattern in patterns:
            m = re.search(pattern, flat_text)
            if m:
                try:
                    return float(m.group(1).replace(",", ""))
                except ValueError:
                    pass
        keywords = ["rs.", "pkr", "amount", "total", "payable", "due"]
        best = 0.0
        lines = text.split("\n")
        for i, line in enumerate(lines):
            lower = line.lower().strip()
            if any(k in lower for k in keywords):
                # Clean dates from line
                cleaned = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "", line)
                m = re.search(r"([\d,]+\.?\d*)", cleaned.replace(",", ""))
                if m:
                    try:
                        val = float(m.group(1).replace(",", ""))
                        # Filter out phone numbers / account IDs
                        if val < 500000 and not (m.group(1).replace(",", "").isdigit() and len(m.group(1).replace(",", "")) >= 9):
                            if val > best:
                                best = val
                    except ValueError:
                        continue
                if i + 1 < len(lines):
                    next_cleaned = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "", lines[i + 1])
                    m = re.search(r"([\d,]+\.?\d*)", next_cleaned.replace(",", ""))
                    if m:
                        try:
                            val = float(m.group(1).replace(",", ""))
                            if val < 500000 and not (m.group(1).replace(",", "").isdigit() and len(m.group(1).replace(",", "")) >= 9):
                                if val > best:
                                    best = val
                        except ValueError:
                            continue
        return best

    @staticmethod
    def _find_date(soup: BeautifulSoup, text: str | None, keyword: str) -> str | None:
        text = text or soup.get_text(separator="\n")
        flat_text = re.sub(r"\s+", " ", text.lower())
        m = re.search(
            rf"\b{re.escape(keyword)}\b[^0-9]{{0,40}}(\d{{1,2}}[-/]\d{{1,2}}[-/]\d{{2,4}})",
            flat_text,
        )
        if m:
            return m.group(1)
        m = re.search(
            rf"(\d{{1,2}}[-/]\d{{1,2}}[-/]\d{{2,4}})[^0-9]{{0,40}}\b{re.escape(keyword)}\b",
            flat_text,
        )
        if m:
            return m.group(1)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if keyword in line.lower():
                m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", line)
                if m:
                    return m.group(1)
                if i + 1 < len(lines):
                    m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", lines[i + 1])
                    if m:
                        return m.group(1)
        return None

    @staticmethod
    def _find_numeric(soup: BeautifulSoup, text: str | None, keyword: str) -> float:
        text = text or soup.get_text(separator="\n")
        flat_text = re.sub(r"\s+", " ", text.lower())
        m = re.search(
            rf"\b{re.escape(keyword)}\b[^0-9]{{0,40}}([0-9][0-9,]*(?:\.[0-9]+)?)",
            flat_text,
        )
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
        m = re.search(
            rf"([0-9][0-9,]*(?:\.[0-9]+)?)\b[^0-9]{{0,40}}\b{re.escape(keyword)}\b",
            flat_text,
        )
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if keyword in line.lower():
                cleaned = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "", line)
                m = re.search(r"([\d,]+\.?\d*)", cleaned.replace(",", ""))
                if m:
                    try:
                        val = float(m.group(1).replace(",", ""))
                        if val < 500000 and not (m.group(1).replace(",", "").isdigit() and len(m.group(1).replace(",", "")) >= 9):
                            return val
                    except ValueError:
                        continue
                if i + 1 < len(lines):
                    next_cleaned = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "", lines[i + 1])
                    m = re.search(r"([\d,]+\.?\d*)", next_cleaned.replace(",", ""))
                    if m:
                        try:
                            val = float(m.group(1).replace(",", ""))
                            if val < 500000 and not (m.group(1).replace(",", "").isdigit() and len(m.group(1).replace(",", "")) >= 9):
                                return val
                        except ValueError:
                            continue
        return 0.0

    @staticmethod
    def _extract_date(text: str) -> str | None:
        m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        cleaned = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "", text)
        m = re.search(r"([\d,]+\.?\d*)", cleaned.replace(",", ""))
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                if val < 500000 and not (m.group(1).replace(",", "").isdigit() and len(m.group(1).replace(",", "")) >= 9):
                    return val
                return None
            except ValueError:
                return None
        return None
