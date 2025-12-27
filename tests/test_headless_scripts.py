import contextlib
import io
from pathlib import Path
import textwrap
import unittest

import main


ROOT = Path(__file__).resolve().parent.parent


def run_script_file(name: str) -> str:
    script_text = (ROOT / name).read_text()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main.run_script(script_text, default_level_name="turn")
    return buf.getvalue().strip()


class HeadlessScriptOutputsTest(unittest.TestCase):
    def test_headless_blocked_matches_expected_output(self):
        output = run_script_file("headless_blocked.script")
        expected = textwrap.dedent(
            """
            Script complete
               0123456789012345678901234567
             0 ############################
             1 #>.>>>>>><^...............S#
             2 #.........^................#
             3 #.........^................#
             4 #S........^................#
             5 #.........^................#
             6 #.........^................#
             7 ############################
            """
        ).strip()
        self.assertEqual(output, expected)

    def test_headless_clear_matches_expected_output(self):
        output = run_script_file("headless_clear.script")
        expected = textwrap.dedent(
            """
            Script complete
               0123456789012345678901234567
             0 ############################
             1 #>.>>>>>>>>>>>>>>>>>>>>>>>S#
             2 #..........................#
             3 #.........#................#
             4 #S<<<<<<<<^................#
             5 #..........................#
             6 #.........^................#
             7 ############################
            """
        ).strip()
        self.assertEqual(output, expected)
