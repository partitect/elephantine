import asyncio
from elephantine.client import AsyncElephantineClient

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        await client.remember("User prefers Python 3.12", category="preference")
        res = await client.recall("Python preference")
        print(res)

if __name__ == "__main__":
    asyncio.run(main())
