import asyncio

from modules.discovery import descobrir


async def scan(base):

    return await descobrir(base)