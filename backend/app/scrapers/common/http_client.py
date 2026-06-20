import random
import asyncio

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_client(timeout: float = 20.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        timeout=timeout,
        follow_redirects=True,
        verify=False,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
)
async def fetch_with_retry(
    client: httpx.AsyncClient, url: str, **kwargs
) -> httpx.Response:
    resp = await client.get(url, **kwargs)
    resp.raise_for_status()
    return resp


async def batch_delay():
    await asyncio.sleep(random.uniform(2, 5))
