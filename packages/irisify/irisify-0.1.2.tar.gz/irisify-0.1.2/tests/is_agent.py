import asyncio

from irisify.async_api import IrisifyAsync

async def main():
    async with IrisifyAsync(bot_id = 8132242691, iris_token = "irisism") as api:
        is_agent = await api.active_agent(661079614)
        print(is_agent) # true

asyncio.run(main())