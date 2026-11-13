import ssl
import socket
import logging
from urllib.parse import urlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from ..config import settings

logger = logging.getLogger("backend.database")

_dns_cache = {}


def _setup_dns_fallback():
    """Install a resilient DNS resolver for cloud databases (Neon/AWS)

    bypassing local ISP router failures (e.g. RCODE_REFUSED / Errno 11001).
    """
    orig_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        # 1. Fast cache hit
        if host in _dns_cache:
            return orig_getaddrinfo(_dns_cache[host], port, socket.AF_INET, type, proto, flags)

        # 2. Fast resolution for Neon cloud endpoints using reliable public DNS (Google/Cloudflare)
        if host and isinstance(host, str) and ("neon.tech" in host or "aws" in host):
            try:
                import dns.resolver
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
                resolver.timeout = 2.0
                resolver.lifetime = 2.0
                answers = resolver.resolve(host, "A")
                for rdata in answers:
                    ip = rdata.address
                    _dns_cache[host] = ip
                    return orig_getaddrinfo(ip, port, socket.AF_INET, type, proto, flags)
            except Exception:
                pass

        # 3. Standard system resolver
        try:
            return orig_getaddrinfo(host, port, family, type, proto, flags)
        except socket.gaierror as err:
            # Fallback for any other domains
            if host and isinstance(host, str):
                try:
                    import dns.resolver
                    resolver = dns.resolver.Resolver(configure=False)
                    resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
                    resolver.timeout = 2.0
                    resolver.lifetime = 2.0
                    answers = resolver.resolve(host, "A")
                    for rdata in answers:
                        ip = rdata.address
                        _dns_cache[host] = ip
                        return orig_getaddrinfo(ip, port, socket.AF_INET, type, proto, flags)
                except Exception:
                    pass
            raise err

    socket.getaddrinfo = patched_getaddrinfo


_setup_dns_fallback()

# Determine SSL requirements based on database host
_parsed_url = urlparse(settings.DATABASE_URL)
_connect_args = {}

if _parsed_url.hostname and _parsed_url.hostname not in ("localhost", "127.0.0.1"):
    # Neon and remote cloud PostgreSQL require SSL
    _ssl_context = ssl.create_default_context()
    _connect_args["ssl"] = _ssl_context

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> dict:
    """Verifies live database connectivity using a SELECT 1 query and returns diagnostics."""
    host = _parsed_url.hostname or "unknown"
    db_name = _parsed_url.path.lstrip("/") or "unknown"

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1, current_database(), current_user"))
            row = result.fetchone()
            return {
                "connected": True,
                "host": host,
                "database": row[1] if row else db_name,
                "user": row[2] if row else "unknown",
            }
    except Exception as e:
        logger.error(f"[DATABASE ERROR] Connection check failed for host '{host}': {e}")
        return {
            "connected": False,
            "host": host,
            "database": db_name,
            "error": str(e),
        }


async def create_tables():
    """Safely create tables if they do not exist. Preserves existing tables and data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
