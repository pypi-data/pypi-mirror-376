import asyncio
from getpass import getpass
# from aiohttp import ClientSession, DigestAuthMiddleware
from httpx import AsyncClient, DigestAuth
from python_swos_lite.client import Client
from python_swos_lite.endpoints.link import LinkEndpoint
from python_swos_lite.endpoints.sys import SystemEndpoint
from python_swos_lite.endpoints.poe import PoEEndpoint
from python_swos_lite.http import createHttpClient

async def fetchAndPrint(client: Client, cls):
    response = await client.fetch(cls)
    print(response)

async def main(host, user, password):
    auth = DigestAuth(user, password)
    httpClient: AsyncClient = AsyncClient(auth=auth)
    client = Client(createHttpClient(httpClient), host)
    await fetchAndPrint(client, SystemEndpoint)
    await fetchAndPrint(client, LinkEndpoint)
    poe = await client.fetch(PoEEndpoint)
    for i in poe.test:
        print(i)

if __name__ == "__main__":
    asyncio.run(main(input("Host: "), input("User: "), getpass("Password: ")))