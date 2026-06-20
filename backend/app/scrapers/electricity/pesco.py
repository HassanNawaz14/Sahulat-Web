"""PESCO bill scraper — delegates to PITC-hosted portal."""
from app.scrapers.electricity.pitc import PitcBillScraper


class PescoScraper(PitcBillScraper):
    provider_code = "pesco"
    utility_type = "electricity"
    consumer_number_pattern = r"^\d{8,14}$"

    def __init__(self):
        super().__init__("pesco")
