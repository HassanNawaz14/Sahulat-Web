"""Solar base adapter for inverter integrations."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict


class SolarAuthResult:
    """Result of solar adapter authentication."""

    def __init__(
        self,
        success: bool,
        token: str | None = None,
        expires_at: str | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.token = token
        self.expires_at = expires_at
        self.error = error


class SolarCredentials:
    """Credentials for solar inverter API."""

    def __init__(
        self,
        username: str,
        password: str,
        plant_id: str | None = None,
    ):
        self.username = username
        self.password = password
        self.plant_id = plant_id


class SolarProduction:
    """Solar production data."""

    def __init__(
        self,
        date: str,
        production_kwh: float,
        self_consumed_kwh: float,
        exported_kwh: float,
        imported_kwh: float,
        peak_power_kw: float,
    ):
        self.date = date
        self.production_kwh = production_kwh
        self.self_consumed_kwh = self_consumed_kwh
        self.exported_kwh = exported_kwh
        self.imported_kwh = imported_kwh
        self.peak_power_kw = peak_power_kw

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.date,
            "production_kwh": self.production_kwh,
            "self_consumed_kwh": self.self_consumed_kwh,
            "exported_kwh": self.exported_kwh,
            "imported_kwh": self.imported_kwh,
            "peak_power_kw": self.peak_power_kw,
        }


class BaseAdapter(ABC):
    """Abstract base class for solar inverter adapters."""

    @abstractmethod
    async def authenticate(
        self,
        credentials: SolarCredentials,
    ) -> SolarAuthResult:
        """Authenticate with solar inverter API."""
        pass

    @abstractmethod
    async def fetch_daily_production(
        self,
        installation: Dict[str, Any],
        target_date: date,
    ) -> SolarProduction:
        """Fetch production data for a specific date."""
        pass

    @abstractmethod
    async def fetch_range(
        self,
        installation: Dict[str, Any],
        start_date: date,
        end_date: date,
    ) -> list[SolarProduction]:
        """Fetch production data for a date range."""
        pass

    def normalize_production(self, raw: dict, target_date: str) -> SolarProduction:
        """Normalize raw API response to SolarProduction."""
        return SolarProduction(
            date=target_date,
            production_kwh=float(raw.get("production_kwh", 0)),
            self_consumed_kwh=float(raw.get("self_consumed_kwh", 0)),
            exported_kwh=float(raw.get("exported_kwh", 0)),
            imported_kwh=float(raw.get("imported_kwh", 0)),
            peak_power_kw=float(raw.get("peak_power_kw", 0)),
        )

    def refresh_captcha(self, client: Any) -> str:
        """Refresh captcha if required."""
        raise NotImplementedError("Adapter does not support captcha refresh")

    def prepare_captcha(self, consumer_number: str, provider_reference: str | None) -> Dict[str, Any]:
        """Prepare captcha challenge."""
        raise NotImplementedError("Adapter does not support captcha challenges")

    def complete_fetch(
        self,
        client: Any,
        consumer_number: str,
        csrf_token: str,
        captcha_solution: str,
        account_id: Any,
    ) -> Any:
        """Complete fetch with captcha solution."""
        raise NotImplementedError("Adapter does not support captcha fetch completion")


BaseSolarAdapter = BaseAdapter
