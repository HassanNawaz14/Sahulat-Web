"""Growatt inverter adapter."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

from app.services.solar.base import BaseSolarAdapter, SolarAuthResult, SolarCredentials, SolarProduction


class GrowattAdapter(BaseSolarAdapter):
    """Adapter for Growatt ShineMonitor inverter."""

    async def authenticate(self, credentials: SolarCredentials) -> SolarAuthResult:
        """Authenticate with Growatt API."""
        await asyncio.sleep(0.1)

        if not credentials.username or not credentials.password:
            return SolarAuthResult(success=False, error="Username and password required")

        if credentials.username == "admin" and credentials.password == "password":
            return SolarAuthResult(
                success=True,
                token="mock_token_123",
            )
        elif credentials.username and credentials.password:
            return SolarAuthResult(
                success=True,
                token=f"mock_token_{hash(credentials.username + credentials.password) % 10000}",
            )
        else:
            return SolarAuthResult(success=False, error="Invalid credentials")

    async def fetch_daily_production(self, installation: dict, target_date: date) -> SolarProduction:
        """Fetch daily production from Growatt API."""
        await asyncio.sleep(0.1)

        day_of_year = target_date.timetuple().tm_yday
        base_production = 30 + (day_of_year % 20)
        system_size = installation.get("system_size_kw", 10)

        if day_of_year % 7 == 0:
            production = base_production * 0.6
        elif day_of_year % 3 == 0:
            production = base_production
        else:
            production = base_production * 1.2

        return SolarProduction(
            date=target_date,
            production_kwh=round(production, 1),
            self_consumed_kwh=round(production * 0.6, 1),
            exported_kwh=round(production * 0.4, 1),
            imported_kwh=round(production * 0.1, 1),
            peak_power_kw=round(0.8 * system_size, 1),
        )

    async def fetch_range(self, installation: dict, start_date: date, end_date: date) -> list[SolarProduction]:
        """Fetch production data for a date range."""
        result = []
        current_date = start_date
        while current_date <= end_date:
            production = await self.fetch_daily_production(installation, current_date)
            result.append(production)
            current_date += timedelta(days=1)
        return result
