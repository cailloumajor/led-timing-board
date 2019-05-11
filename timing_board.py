#!/usr/bin/env python3.5
import subprocess
from datetime import datetime
from typing import Optional

FIRST_LINE = "#44 "
TEAM_NAME = "PG72"
COMMANDS = [TEAM_NAME, "BOX", "FUEL"]
MATRIX_OPTIONS = [
    "--led-rows=16",
    "--led-chain=2",
    "--led-row-addr-type=2",
    "--led-multiplexing=3",  # P10(3535)16X32-4S-M2.1
    # "--led-multiplexing=5",  # M-P10-4S-3535-3216-JA1
    "--led-slowdown-gpio=2",
    "-f", "6x8_custom.bdf",
    "-C", "255,0,0",
    "-C", "255,255,0",
]


def parse_timing(raw_time: str) -> str:
    if not raw_time:
        raise ValueError("Invalid empty string")
    raw_time = raw_time.zfill(7)
    raw_time += "000"
    timing = datetime.strptime(raw_time, "%M%S%f").time()
    formatted_timing = timing.strftime("%S.%f")
    formatted_timing = "{}:{}".format(timing.minute, formatted_timing)
    formatted_timing = formatted_timing[:-3]
    return formatted_timing


class SubProcessNotInitialized(Exception):
    pass


class TimingBoard:

    def __init__(self) -> None:
        self._lines = ["READY...", "-:--.---"]
        self._proc = None  # type: Optional[subprocess.Popen]

    def _handle_instruction(self) -> bool:
        eoferror = False
        try:
            instruction = input("? ")
        except EOFError:
            eoferror = True
        if eoferror or instruction == "*9999":
            return False
        elif instruction.startswith("*"):
            try:
                command_index = int(instruction[1:])
                self._lines[0] = FIRST_LINE + COMMANDS[command_index]
            except (ValueError, IndexError):
                return True
        else:
            try:
                self._lines[1] = parse_timing(instruction)
            except ValueError:
                return True
        return True

    def _write(self) -> None:
        if self._proc is None:
            raise SubProcessNotInitialized
        for l in self._lines:
            self._proc.stdin.write(l + "\n")
            self._proc.stdin.flush()

    def run(self) -> None:
        self._proc = subprocess.Popen(
            ["sudo", "bin/stdin-text-driver"] + MATRIX_OPTIONS,
            stdin=subprocess.PIPE,
            universal_newlines=True,
        )
        self._write()
        while self._proc.poll() is None:
            if self._handle_instruction():
                self._write()
            else:
                self._proc.stdin.close()


if __name__ == "__main__":
    timing_board = TimingBoard()
    timing_board.run()
