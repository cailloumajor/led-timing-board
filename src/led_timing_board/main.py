import asyncio
import logging
import os
import re
import signal
import sys
from itertools import cycle
from typing import Any, Optional, cast

from evdev import InputDevice, KeyEvent, ecodes

from led_timing_board.display_strategies import (
    Blinking,
    DisplayStrategy,
    Fixed,
    Initial,
)

INSTRUCTIONS = ["BOX", "FEUX"]

MATRIX_OPTIONS = [
    "--led-rows=16",
    "--led-cols=32",
    "--led-chain=2",
    "--led-parallel=2",
    # "--led-multiplexing=3",  # P10(3535)16X32-4S-M2.1
    # "--led-multiplexing=5",  # M-P10-4S-3535-3216-JA1
    "--led-multiplexing=19",  # Custom mixed
    "--led-row-addr-type=2",
    "--led-slowdown-gpio=4",
    "-f",
    "ter-u32b.bdf",
    "-C",
    "255,255,255",
]

KEY_CHARS = {
    ecodes.KEY_KPSLASH: "/",
    ecodes.KEY_KPASTERISK: "*",
    ecodes.KEY_KPMINUS: "-",
    ecodes.KEY_KPPLUS: "+",
    ecodes.KEY_KPDOT: ".",
    ecodes.KEY_KP0: "0",
    ecodes.KEY_KP1: "1",
    ecodes.KEY_KP2: "2",
    ecodes.KEY_KP3: "3",
    ecodes.KEY_KP4: "4",
    ecodes.KEY_KP5: "5",
    ecodes.KEY_KP6: "6",
    ecodes.KEY_KP7: "7",
    ecodes.KEY_KP8: "8",
    ecodes.KEY_KP9: "9",
}

RE_POSITION = re.compile(r"/(\d+)")
RE_INSTRUCTION = re.compile(r"\*(\d)")
RE_LAP_TIME = re.compile(r"[0-5]\d\.\d")

_logger = logging.getLogger(__name__)


async def shutdown(sig: Optional[signal.Signals] = None) -> None:
    """Cleanups tasks tied to the service's shutdown.
    Args:
        sig: Optional; The signal that triggered the shutdown.
    """
    if sig:
        _logger.info("Received exit signal %s", sig.name)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    _logger.info("Waiting for %s outstanding tasks to finish...", len(tasks))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if not isinstance(result, asyncio.CancelledError) and isinstance(
            result, Exception
        ):
            _logger.error("Exception occured during shutdown: %s", result)
    loop = asyncio.get_running_loop()
    await loop.shutdown_asyncgens()
    loop.stop()


def handle_exception(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
    """Exception handler for event loop."""
    # context["message"] will always be there;
    # but context["exception"] and context["future"] may not
    try:
        exc: Exception = context["exception"]
        future = context["future"]
        future_name = "unknown"
        try:
            # If future is a Task, get its name
            future_name = future.get_name()
        except AttributeError:
            pass
        _logger.error(
            "Caught exception `%s` in %s task: %s",
            exc.__class__.__name__,
            future_name,
            exc,
        )
    except KeyError:
        _logger.error("Caught exception: %s", context["message"])
    _logger.info("Shutting down...")
    loop.create_task(shutdown())


class SubProcessNotInitialized(Exception):
    pass


class TimingBoard:
    def __init__(self) -> None:
        # Protects lines array from concurrent accesses
        self._lock = asyncio.Lock()
        self._display_strategy: DisplayStrategy = Initial()

    async def _set_strategy(self, strategy: DisplayStrategy) -> None:
        async with self._lock:
            self._display_strategy = strategy

    async def handle_input(self, input: str) -> None:
        if input == "0":
            await self._set_strategy(Initial())
        if (match := RE_POSITION.fullmatch(input)) is not None:
            await self._set_strategy(Fixed("P" + match.group(1)))
        elif (match := RE_INSTRUCTION.fullmatch(input)) is not None:
            try:
                instruction = INSTRUCTIONS[int(match.group(1)) - 1]
            except IndexError:
                return
            await self._set_strategy(Blinking(instruction))
        elif RE_LAP_TIME.fullmatch(input):
            await self._set_strategy(Fixed(input))
        elif input == "*9999":
            await asyncio.create_subprocess_shell("reboot")

    async def run(self) -> None:
        proc = await asyncio.create_subprocess_exec(
            "bin/stdin-text-driver",
            *MATRIX_OPTIONS,
            stdin=asyncio.subprocess.PIPE,
        )
        stdin = cast(asyncio.StreamWriter, proc.stdin)
        try:
            while True:
                if (new_line := self._display_strategy.update()) is not None:
                    async with self._lock:
                        stdin.write((new_line + "\n").encode("ascii"))
                        await stdin.drain()
                await asyncio.sleep(0.1)
        finally:
            stdin.close()
            await stdin.wait_closed()
            await asyncio.wait_for(proc.wait(), 2.0)


async def ingest_input(board_driver: TimingBoard) -> None:
    buffer = ""
    dev = InputDevice("/dev/input/by-id/usb-HCT_USB_Keyboard-event-kbd")
    async for ev in dev.async_read_loop():
        if ev.type != ecodes.EV_KEY or ev.value != KeyEvent.key_down:
            continue
        if ev.code == ecodes.KEY_KPENTER:
            await board_driver.handle_input(buffer)
            buffer = ""
        elif (char := KEY_CHARS.get(ev.code, None)) is not None:
            buffer += char
            if len(buffer) > 20:
                buffer = ""


def run() -> None:
    if os.geteuid() != 0:
        sys.exit("Must be run as root")

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s : %(message)s",
        level=logging.INFO,
    )

    loop = asyncio.get_event_loop()

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for sig in signals:
        loop.add_signal_handler(sig, lambda sig=sig: loop.create_task(shutdown(sig)))
    loop.set_exception_handler(handle_exception)

    board_driver = TimingBoard()

    loop.create_task(board_driver.run())
    loop.create_task(ingest_input(board_driver))

    try:
        loop.run_forever()
    finally:
        loop.close()
        _logger.info("Shutdown successfull")
