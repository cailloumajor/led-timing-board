#!/usr/bin/env python3.5
import subprocess
from datetime import datetime
from typing import IO

FIRST_LINE = "#44 "
TEAM_NAME = "PG72"
COMMANDS = ["", "BOX", "FUEL"]
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
    raw_time = raw_time.zfill(7)
    raw_time += "000"
    timing = datetime.strptime(raw_time, "%M%S%f").time()
    formatted_timing = timing.strftime("%S.%f")
    formatted_timing = "{}:{}".format(timing.minute, formatted_timing)
    formatted_timing = formatted_timing[:-3]
    return formatted_timing


def handle_instructions(stream: IO[str]) -> None:
    instruction = input("1? ")
    first_line = FIRST_LINE
    if instruction.startswith("*"):
        try:
            command_index = int(instruction[1:])
            first_line += COMMANDS[command_index]
            instruction = "consumed"
        except (ValueError, IndexError):
            return
    else:
        first_line += TEAM_NAME
    if instruction == "consumed":
        instruction = input("2? ")
    try:
        second_line = parse_timing(instruction)
    except ValueError:
        return
    for l in (first_line, second_line):
        stream.write(l + "\n")
        stream.flush()


def main() -> None:
    proc = subprocess.Popen(
        ["sudo", "bin/stdin-text-driver"] + MATRIX_OPTIONS,
        stdin=subprocess.PIPE,
        universal_newlines=True,
    )
    while proc.poll() is None:
        handle_instructions(proc.stdin)


if __name__ == "__main__":
    main()
