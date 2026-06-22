"""Test all scrapers: imports, validation, and (if reachable) live fetch.
Run: python -m scripts.test_scrapers
"""
import asyncio
import sys


def test_imports():
    print("=== Testing imports ===")
    from app.scrapers.base import (
        BaseScraper, ScrapedBill, ScraperError,
        InvalidConsumerNumberError, PortalUnreachableError,
        ParsingFailedError, CaptchaDetectedError, NoBillFoundError,
    )
    print("  base.py: OK")
    from app.scrapers.common.http_client import get_client, fetch_with_retry, batch_delay
    print("  http_client.py: OK")
    from app.scrapers.common.feeder_area_map import lookup_area, FEEDER_AREA_MAP
    print(f"  feeder_area_map.py: OK ({len(FEEDER_AREA_MAP)} mappings)")
    print("  All imports OK\n")


def test_validation():
    print("=== Testing consumer number validation ===")
    from app.scrapers.registry import get_scraper, SCRAPER_REGISTRY

    test_cases = [
        ("lesco", "04-12345-1234567-A", True),
        ("lesco", "123456", False),
        ("kelectric", "1234567890", True),
        ("kelectric", "1234567890123", True),
        ("kelectric", "AB123", False),
        ("sngpl", "1234567890", True),
        ("sngpl", "12345678901", True),
        ("sngpl", "123", False),
        ("ssgc", "1234567890", True),
        ("ssgc", "123456789012", True),
        ("ssgc", "short", False),
        ("wasa_lhr", "12345678", True),
        ("wasa_lhr", "123456789012", True),
        ("ptcl", "04212345678", True),
        ("ptcl", "0511234567", True),
        ("ptcl", "12345678", False),
        ("nayatel", "ABC123", True),
        ("nayatel", "A1B2C3D4E5F6", True),
        ("nayatel", "abc-123", False),
    ]

    passed = 0
    for provider_code, number, expected in test_cases:
        scraper = SCRAPER_REGISTRY.get(provider_code)
        if not scraper:
            print(f"  SKIP {provider_code}: not in registry")
            continue
        result = scraper.validate_consumer_number(number)
        status = "OK" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        print(f"  [{status}] {provider_code}: '{number}' -> {result} (expected {expected})")

    print(f"\n  Validation: {passed}/{len(test_cases)} passed\n")


def test_coming_soon():
    print("=== Testing coming-soon stubs ===")
    from app.scrapers.registry import get_scraper, COMING_SOON

    for code in COMING_SOON:
        try:
            get_scraper(code)
            print(f"  FAIL: {code} should raise NotImplementedError")
        except NotImplementedError:
            print(f"  OK: {code} -> NotImplementedError")
        except Exception as e:
            print(f"  FAIL: {code} → unexpected {type(e).__name__}: {e}")


async def test_live_fetch(provider_code: str, consumer_number: str):
    print(f"\n=== Live test: {provider_code} ({consumer_number}) ===")
    from app.scrapers.registry import get_scraper
    scraper = get_scraper(provider_code)
    try:
        bill = await scraper.fetch_bill(consumer_number)
        print(f"  SUCCESS: {bill}")
    except Exception as e:
        print(f"  {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_imports()
    test_validation()
    test_coming_soon()

    if len(sys.argv) > 2:
        asyncio.run(test_live_fetch(sys.argv[1], sys.argv[2]))
    else:
        print("\nUsage: python -m scripts.test_scrapers <provider_code> <consumer_number>")
        print("Example: python -m scripts.test_scrapers lesco 04-12345-1234567-1")
