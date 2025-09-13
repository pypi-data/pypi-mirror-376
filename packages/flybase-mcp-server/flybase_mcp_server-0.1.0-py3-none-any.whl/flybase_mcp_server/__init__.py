import asyncio

from . import __main__


def main() -> None:
    asyncio.run(__main__.main())