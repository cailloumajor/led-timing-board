import io

import pytest  # type: ignore

from timing_board import (
    COMMANDS,
    FIRST_LINE,
    TEAM_NAME,
    handle_instructions,
    parse_timing,
)

parse_timing_failing_data = ["a", "+0", "-0", "*0", "/0", ".0", "60000", "6000000"]


class TestParseTiming:

    @pytest.mark.parametrize("raw_time,formatted_timing", [
        ("", "0:00.000"),
        ("0", "0:00.000"),
        ("1234567", "12:34.567"),
        ("5959999", "59:59.999")
    ])
    def test_parse_timing_succeeds(self, raw_time, formatted_timing):
        assert parse_timing(raw_time) == formatted_timing

    @pytest.mark.parametrize("raw_time", parse_timing_failing_data)
    def test_parse_timing_fails(self, raw_time):
        with pytest.raises(ValueError):
            parse_timing(raw_time)


class TestHandleInstructions:
    # pylint: disable=attribute-defined-outside-init

    @pytest.fixture(autouse=True)
    def _teststream(self):
        self.teststream = io.StringIO()
        yield
        self.teststream.close()

    @pytest.fixture(autouse=True)
    def _patch_input(self, monkeypatch):
        def _inner(ret_vals):
            gen = iter(ret_vals)
            monkeypatch.setattr("builtins.input", lambda p=None: next(gen))
        self.patch_input = _inner

    @pytest.mark.parametrize("inputs,expected", [
        (["*1", "123456"], "{}{}\n{}\n".format(FIRST_LINE, COMMANDS[1], "1:23.456")),
        (["456789"], "{}{}\n{}\n".format(FIRST_LINE, TEAM_NAME, "4:56.789")),
        (["*a"], ""),
        (["*99"], ""),
        ([parse_timing_failing_data[0]], ""),
    ], ids=[
        "OK (two instructions)",
        "OK (timing only)",
        "NOK (bad command)",
        "NOK (nonexistent command)",
        "NOK (bad timing)",
    ])
    def test_handle_instructions(self, inputs, expected):
        self.patch_input(inputs)
        handle_instructions(self.teststream)
        assert self.teststream.getvalue() == expected
