import asyncio

from . import server


def main() -> None:
    asyncio.run(server.main())