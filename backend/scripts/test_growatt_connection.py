"""Script to manually test Growatt API connection."""

import asyncio
import argparse
from datetime import date, timedelta

from app.services.solar.growatt import GrowattAdapter


async def test_growatt_connection(username: str, password: str, plant_id: str | None = None):
    """Test Growatt API connection."""
    print("Testing Growatt API connection...")

    adapter = GrowattAdapter(username, password, plant_id)

    try:
        auth_result = await adapter.authenticate(username, password, plant_id)

        if auth_result.success:
            print(f"✅ Authentication successful")
            print(f"   Token: {auth_result.token[:20]}...")
            print(f"   Expires at: {auth_result.expires_at}")

            # Test fetching a few days of data
            installation = {
                "id": "test_installation",
                "system_size_kw": 10,
                "inverter_brand": "growatt",
            }

            start_date = date.today() - timedelta(days=7)
            end_date = date.today()

            production = await adapter.fetch_range(
                installation,
                start_date,
                end_date,
            )

            print(f"\n✅ Fetched {len(production)} days of production data")
            print("Sample data:")
            for i, day in enumerate(production[-3:]):  # Show last 3 days
                print(f"   {day.date}: {day.production_kwh} kWh")

            return True
        else:
            print(f"❌ Authentication failed: {auth_result.error}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test Growatt API connection")
    parser.add_argument("--username", required=True, help="Growatt username")
    parser.add_argument("--password", required=True, help="Growatt password")
    parser.add_argument("--plant-id", help="Plant ID (if applicable)")

    args = parser.parse_args()

    success = await test_growatt_connection(args.username, args.password, args.plant_id)

    if not success:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
