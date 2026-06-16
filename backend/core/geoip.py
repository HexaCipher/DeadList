"""
DeadList GeoIP Resolver
Resolves IP addresses to geographic locations using ip-api.com.
Includes SQLite-based caching to stay within rate limits (45 req/min).
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.database import GeoIPCache

logger = logging.getLogger(__name__)


async def resolve_ip(
    ip_address: str,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """
    Resolve a single IP address to geographic location.
    Checks cache first, then calls ip-api.com if not cached.

    Args:
        ip_address: IP address to resolve
        db: Database session for cache operations

    Returns:
        Dict with country, city, lat, lon or None if resolution fails
    """
    # Skip private/local addresses
    if _is_private_ip(ip_address):
        return None

    # Check cache first
    cached = await _get_cached(ip_address, db)
    if cached:
        return cached

    # Call ip-api.com
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.GEOIP_API_URL}/{ip_address}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = {
                        "country": data.get("country"),
                        "city": data.get("city"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                    }
                    # Cache the result
                    await _cache_result(ip_address, result, db)
                    return result
    except Exception as e:
        logger.warning(f"GeoIP lookup failed for {ip_address}: {e}")

    return None


async def resolve_ips_batch(
    ip_addresses: List[str],
    db: AsyncSession,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Resolve multiple IP addresses, leveraging cache and batching API calls.

    Args:
        ip_addresses: List of IP addresses to resolve
        db: Database session

    Returns:
        Dict mapping IP → location data
    """
    results = {}
    uncached = []

    # Deduplicate and filter
    unique_ips = list(set(ip for ip in ip_addresses if ip and not _is_private_ip(ip)))

    # Check cache for all IPs
    for ip in unique_ips:
        cached = await _get_cached(ip, db)
        if cached:
            results[ip] = cached
        else:
            uncached.append(ip)

    # Batch resolve uncached IPs (ip-api.com supports batch endpoint)
    if uncached:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # ip-api.com batch endpoint accepts up to 100 IPs
                for i in range(0, len(uncached), 100):
                    batch = uncached[i:i + 100]
                    response = await client.post(
                        "http://ip-api.com/batch",
                        json=[{"query": ip} for ip in batch],
                    )
                    if response.status_code == 200:
                        for item in response.json():
                            ip = item.get("query")
                            if item.get("status") == "success":
                                result = {
                                    "country": item.get("country"),
                                    "city": item.get("city"),
                                    "lat": item.get("lat"),
                                    "lon": item.get("lon"),
                                }
                                results[ip] = result
                                await _cache_result(ip, result, db)
                            else:
                                results[ip] = None
        except Exception as e:
            logger.warning(f"Batch GeoIP lookup failed: {e}")
            for ip in uncached:
                if ip not in results:
                    results[ip] = None

    return results


def _is_private_ip(ip: str) -> bool:
    """Check if an IP address is private/local."""
    if not ip or ip in ("0.0.0.0", "127.0.0.1", "::", "::1", "*", ""):
        return True
    return (
        ip.startswith("10.") or
        ip.startswith("172.16.") or ip.startswith("172.17.") or
        ip.startswith("172.18.") or ip.startswith("172.19.") or
        ip.startswith("172.2") or ip.startswith("172.3") or
        ip.startswith("192.168.") or
        ip.startswith("169.254.") or
        ip.startswith("fe80:")
    )


async def _get_cached(
    ip_address: str,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """Check if IP is in the GeoIP cache."""
    result = await db.execute(
        select(GeoIPCache).where(GeoIPCache.ip_address == ip_address)
    )
    cached = result.scalar_one_or_none()
    if cached:
        return {
            "country": cached.country,
            "city": cached.city,
            "lat": cached.lat,
            "lon": cached.lon,
        }
    return None


async def _cache_result(
    ip_address: str,
    data: Dict[str, Any],
    db: AsyncSession,
) -> None:
    """Store GeoIP result in cache."""
    try:
        cache_entry = GeoIPCache(
            ip_address=ip_address,
            country=data.get("country"),
            city=data.get("city"),
            lat=data.get("lat"),
            lon=data.get("lon"),
            cached_at=datetime.utcnow(),
        )
        db.add(cache_entry)
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to cache GeoIP result for {ip_address}: {e}")
        await db.rollback()
