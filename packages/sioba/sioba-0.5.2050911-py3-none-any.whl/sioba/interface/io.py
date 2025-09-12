import asyncio
import threading
import janus
from typing import Any, Optional, TypedDict, Callable
from .base import Interface, InterfaceState, InterfaceContext, register_scheme
from loguru import logger
from dataclasses import dataclass

from ..errors import InterfaceNotStarted, InterfaceShutdown

@dataclass
class IOContext(InterfaceContext):
    """Base context for IO interfaces"""
    pass

class ThreadedIOInterface(Interface):
    """ Provides a way to file-like IO interfaces in a threaded manner.
    """

    context_class: Optional[type[InterfaceContext]] = IOContext

    # file-like IO interface
    handle: Optional[Any] = None

    def __init__(self, *args, **kwargs):
        # Send to frontend queue
        self.send_queue: janus.Queue[bytes] = janus.Queue()

        # Incoming input from frontend queue
        self.input_queue: janus.Queue[bytes] = janus.Queue()

        # Read loop thread
        self.read_thread: threading.Thread|None = None

        super().__init__(*args, **kwargs)

    def create_filehandle(self) -> Any:
        """ Subclassable method to create the file-like handle.
            This is called during start_interface.
        """
        raise NotImplementedError("create_filehandle must be implemented by subclasses")

    async def start_interface(self) -> bool:
        """Launch the IO interface"""

        # Store the main event loop for later use
        self.main_loop = main_loop = asyncio.get_running_loop()

        # Create the file-like handle
        self.handle = self.create_filehandle()
        if not self.handle:
            raise InterfaceNotStarted("Failed to create file-like handle")

        # Set the state to STARTED immediately so start() won't wait infinitely
        self.state = InterfaceState.STARTED

        # Create the send queue loop
        logger.debug("Starting send_to_frontend_loop")
        asyncio.create_task(self.send_to_frontend_loop())

        # Launch the function
        def _read_loop():
            logger.debug(f"Running read loop in thread {threading.current_thread().name}")
            try:

                # Start the read loop
                shutdown_future = asyncio.run_coroutine_threadsafe(
                    coro = self.read_loop(),
                    loop = main_loop,
                )
                shutdown_future.result()  # Wait for the shutdown to complete

            except (InterfaceShutdown, ):
                # This is just a notification that we're shutdown
                # let's just pass through to the end
                pass

            # With any exception, we want to shutdown the interface
            # and clean up the queues
            except Exception as e:
                try:
                    shutdown_future = asyncio.run_coroutine_threadsafe(
                        coro = self.shutdown(),
                        loop = main_loop,
                    )
                    shutdown_future.result()  # Wait for the shutdown to complete
                except RuntimeError as e:
                    pass
                else:
                    logger.debug("Shutdown coroutine scheduled")
            logger.debug("Threaded IO wrapper finished")

        self.read_thread = threading.Thread(target=_read_loop, daemon=True)
        self.read_thread.start()

        return True

    async def read_loop(self):
        """Continuously receive data from the socket"""
        while self.state == InterfaceState.STARTED:
            try:
                if not ( file_handle := self.handle ):
                    logger.error("Socket reader is not initialized")
                    return

                if not ( data := await file_handle.read(4096) ):
                    break

                # Process received data
                await self.send_to_frontend(data)

            except Exception as e:
                logger.error(f"Error in read loop: {e=} {type(e)}")
                return


    async def shutdown_handle(self) -> None:
        """Shutdown the interface"""
        if self.send_queue:
            await self.send_queue.aclose()

    async def send_to_frontend_loop(self) -> None:
        while self.state == InterfaceState.STARTED:
            try:
                # Get data from the queue with a timeout to allow checking the state
                data = await self.send_queue.async_q.get()

                # Send data to the terminal using the main event loop
                await self.send_to_frontend(data)

            except janus.QueueShutDown:
                break

            except asyncio.CancelledError:
                break

            except InterfaceShutdown:
                break
