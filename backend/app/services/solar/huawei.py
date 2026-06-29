"""Huawei FusionSolar inverter adapter stub."""

from datetime import date

from app.services.solar.base import BaseSolarAdapter, SolarAuthResult, SolarCredentials, SolarProduction


class HuaweiAdapter(BaseSolarAdapter):
    """Adapter for Huawei FusionSolar inverter (stub — not yet implemented)."""

    async def authenticate(self, credentials: SolarCredentials) -> SolarAuthResult:
        raise NotImplementedError("Huawei adapter not yet implemented")

    async def fetch_daily_production(self, installation: dict, target_date: date) -> SolarProduction:
        raise NotImplementedError("Huawei adapter not yet implemented")

    async def fetch_range(self, installation: dict, start_date: date, end_date: date) -> list[SolarProduction]:
        raise NotImplementedError("Huawei adapter not yet implemented")
