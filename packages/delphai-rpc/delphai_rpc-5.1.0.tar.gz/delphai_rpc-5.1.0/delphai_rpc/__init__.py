import asyncio
import logging
import signal
import typing

from .client import Options, RpcClient
from .queue_client import QueueClient
from .server import RpcServer

__all__ = ["Options", "Rpc", "run_forever"]

logger = logging.getLogger(__name__)


class Rpc:
    def __init__(self, service_name: str, connection_string: str) -> None:
        self._connection_string = connection_string
        self._queue_client = QueueClient(service_name, self._connection_string)

        self.client = RpcClient(self._queue_client)
        self.server = RpcServer(self._queue_client)

        self._servers: dict[str, RpcServer] = {
            service_name: self.server,
        }

    async def run(self) -> None:
        if not self._connection_string:
            logger.warning(
                "RPC did not run because 'connection_string' is undefined."
                "Pass a non-empty 'connection_string' while initializing."
            )
            await asyncio.Future()
            return

        for server in self._servers.values():
            await server.start()

        try:
            await asyncio.Future()
        finally:
            await self._queue_client.stop()

    def get_server(self, service_name: str) -> RpcServer:
        server = self._servers.get(service_name)
        if not server:
            self._servers[service_name] = RpcServer(
                self._queue_client,
                service_name=service_name,
            )

        return self._servers[service_name]


async def run_forever(*coros: typing.Coroutine) -> None:
    loop = asyncio.get_running_loop()
    signal_event = asyncio.Event()

    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, signal_event.set)

    try:
        tasks = [asyncio.ensure_future(coro) for coro in coros]

        await asyncio.wait(
            [asyncio.ensure_future(signal_event.wait()), *tasks],
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        for signum in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(signum)

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
