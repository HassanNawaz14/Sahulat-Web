from app.scrapers.base import BaseScraper
from app.scrapers.electricity.lesco import LescoScraper
from app.scrapers.electricity.kelectric import KElectricScraper
from app.scrapers.electricity.iesco import IescoScraper
from app.scrapers.electricity.gepco import GepcoScraper
from app.scrapers.electricity.fesco import FescoScraper
from app.scrapers.electricity.mepco import MepcoScraper
from app.scrapers.electricity.pesco import PescoScraper
from app.scrapers.electricity.qesco import QescoScraper
from app.scrapers.electricity.hesco import HescoScraper
from app.scrapers.electricity.sepco import SepcoScraper
from app.scrapers.gas.sngpl import SngplScraper
from app.scrapers.gas.ssgc import SsgcScraper
from app.scrapers.water.wasa_lhr import WasaLahoreScraper
from app.scrapers.water.kwsb import KwsbScraper
from app.scrapers.internet.ptcl import PtclScraper
from app.scrapers.internet.nayatel import NayatelScraper

SCRAPER_REGISTRY: dict[str, BaseScraper] = {
    "lesco": LescoScraper(),
    "kelectric": KElectricScraper(),
    "iesco": IescoScraper(),
    "gepco": GepcoScraper(),
    "fesco": FescoScraper(),
    "mepco": MepcoScraper(),
    "pesco": PescoScraper(),
    "qesco": QescoScraper(),
    "hesco": HescoScraper(),
    "sepco": SepcoScraper(),
    "sngpl": SngplScraper(),
    "ssgc": SsgcScraper(),
    "wasa_lhr": WasaLahoreScraper(),
    "kwsb": KwsbScraper(),
    "ptcl": PtclScraper(),
    "nayatel": NayatelScraper(),
}

COMING_SOON: set[str] = {
    "wasa_rwp",
    "stormfiber",
    "jazz_home",
    "zong_home",
}


def get_scraper(provider_code: str):
    if provider_code in COMING_SOON:
        raise NotImplementedError(
            f"{provider_code} support coming soon"
        )
    scraper = SCRAPER_REGISTRY.get(provider_code)
    if not scraper:
        raise ValueError(f"Unknown provider_code: {provider_code}")
    return scraper
