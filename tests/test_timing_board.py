# import io

import pytest  # type: ignore

from timing_board import parse_timing  # COMMANDS,; FIRST_LINE,; TEAM_NAME,


class TestParseTiming:
    @pytest.mark.parametrize(
        "raw_time,formatted_timing",
        [("0", "0:00.000"), ("1234567", "12:34.567"), ("5959999", "59:59.999")],
    )
    def test_parse_timing_succeeds(self, raw_time, formatted_timing):
        assert parse_timing(raw_time) == formatted_timing

    @pytest.mark.parametrize(
        "raw_time", ["", "a", "+0", "-0", "*0", "/0", ".0", "60000", "6000000"]
    )
    def test_parse_timing_fails(self, raw_time):
        with pytest.raises(ValueError):
            parse_timing(raw_time)


# TODO: update according to last modifications
# class TestHandleInstruction:
#     # pylint: disable=attribute-defined-outside-init

#     @pytest.fixture(autouse=True)
#     def _teststream(self):
#         self.teststream = io.StringIO()
#         yield
#         self.teststream.close()

#     @pytest.fixture(autouse=True)
#     def _patch_input(self, monkeypatch):
#         def _inner(value_from_input):
#             monkeypatch.setattr("builtins.input", lambda p=None: value_from_input)

#         self.patch_input = _inner

#     @pytest.mark.parametrize(
#         "inval,l1,l2",
#         [
#             ("*0", FIRST_LINE + TEAM_NAME, "line2"),
#             ("*1", FIRST_LINE + COMMANDS[1], "line2"),
#             ("0", "line1", "0:00.000"),
#             ("456789", "line1", "4:56.789"),
#         ],
#         ids=["reset command", "good command", "zero timing", "good timing"],
#     )
#     def test_writes(self, inval, l1, l2):
#         lines = ["line1", "line2"]
#         self.patch_input(inval)
#         handle_instructions(self.teststream, lines)
#         assert lines == [l1, l2]
#         assert self.teststream.getvalue() == l1 + "\n" + l2 + "\n"

#     @pytest.mark.parametrize(
#         "inval",
#         ["*a", "*99", "", "60000"],
#         ids=[
#             "non numeric command",
#             "nonexistent command",
#             "empty string",
#             "bad timing",
#         ],
#     )
#     def test_returns_without_writing(self, inval):
#         lines = ["line1", "line2"]
#         self.patch_input(inval)
#         handle_instructions(self.teststream, lines)
#         assert lines == ["line1", "line2"]
#         assert self.teststream.getvalue() == ""

#     def test_end_command(self):
#         lines = ["line1", "line2"]
#         self.patch_input("*9999")
#         handle_instructions(self.teststream, lines)
#         assert lines == ["line1", "line2"]
#         assert self.teststream.closed

#     def test_input_eof(self, monkeypatch):
#         def _raising_input(_):
#             raise EOFError
#         monkeypatch.setattr("builtins.input", _raising_input)
#         lines = ["line1", "line2"]
#         handle_instructions(self.teststream, lines)
#         assert lines == ["line1", "line2"]
#         assert self.teststream.closed
