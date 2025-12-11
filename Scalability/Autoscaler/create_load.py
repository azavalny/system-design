# save as load_gen.py
import asyncio
import time
import httpx

URL = "http://127.0.0.1:8000/work"

async def hit_server(client, n):
    resp = await client.get(URL, params={"delay_ms": 200})
    return resp.json()

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            # 20 concurrent requests per burst
            tasks = [hit_server(client, i) for i in range(20)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
