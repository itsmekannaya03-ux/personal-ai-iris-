import sys
import os
from pathlib import Path
import asyncio
import asyncpg

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings

async def check():
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    db_name = await conn.fetchval("SELECT current_database()")
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    print(f"Tables in {db_name} database:")
    for r in rows:
        cols = await conn.fetch(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{r['table_name']}' ORDER BY ordinal_position")
        print(f"  TABLE {r['table_name']}")
        for c in cols:
            print(f"    {c['column_name']} ({c['data_type']})")
        print()
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
