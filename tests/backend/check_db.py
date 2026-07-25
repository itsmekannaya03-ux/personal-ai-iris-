import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:2511@localhost:5432/igris')
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    print("Tables in igris database:")
    for r in rows:
        cols = await conn.fetch(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{r['table_name']}' ORDER BY ordinal_position")
        print(f"  TABLE {r['table_name']}")
        for c in cols:
            print(f"    {c['column_name']} ({c['data_type']})")
        print()
    await conn.close()

asyncio.run(check())
