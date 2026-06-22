"""Test if endpoints are actually accessible."""
import sys
sys.path.insert(0, '.')

from app.main import app
from httpx import AsyncClient, ASGITransport
import asyncio

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test health
        r = await ac.get("/health")
        print(f"GET /health: {r.status_code}")
        
        # Test coming-soon-signups
        r = await ac.get("/api/v1/coming-soon-signups")
        print(f"GET /api/v1/coming-soon-signups: {r.status_code} {r.text[:100]}")
        
        # Test bills/fetch (without auth - should 401/422)
        r = await ac.post("/api/v1/bills/fetch/test-id")
        print(f"POST /api/v1/bills/fetch/test-id: {r.status_code} {r.text[:100]}")

asyncio.run(test())