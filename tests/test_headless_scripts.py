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
             1 #>.RRRRRRLU...............S#
             2 #.........U................#
             3 #.........U................#
             4 #S........U................#
             5 #.........U................#
             6 #.........^................#
             7 ############################
            """
        ).strip()
        self.assertEqual(output, expected)

    def test_headless_split_maze_matches_expected_output(self):
        output = run_script_file("headless_split_maze.script")
        expected = textwrap.dedent(
            """
            Script complete
               012345678901234567890123456789012345678901234
             0 #############################################
             1 #v#.#.#.#.#.#URRRRRR#.#URRRRRR#.#.#.#.#.#.#v#
             2 #D#.#.#.#.#.#U#####D#.#U#####D#.#.#.#####.#.#
             3 #DRRRR#....##LLLLU#DRR#LLLLU#DRRRR#.....#..D#
             4 ###.#D###.#URR#.#U###DR##.#U###.#DRR#.#####D#
             5 #...#DRRRR#U#DRR#LLU.#DRRR#U....###DRR#LLU.D#
             6 ###.#####D#U###D###U#.###D#U###.#####D#D#U#D#
             7 #.#.#.#.#D#U#.#D#.#U#.#.#D#U#.#.#.#.#D#D#U#D#
             8 #.#.#.#.#D#U#.#D#.#U#.#.#D#U#.#.#.#.#D#D#U#D#
             9 #.....#..DRR#..DRR#U..#..DRR#.....#..DRD#LLD#
            10 #######.#########DRR#########.#########D#####
            11 #.#.#.#.#.#URR#.#####LLU#LLU#.#.#LLU#.#D#.#.#
            12 ###.#.#.###U#D#.#.#.#D#U#D#U#.#.#D#U#.#D#.#.#
            13 #URRRR#.#URR#DRRRS#..D.U.D.U..#..D.U#..D..#.#
            14 #U#.#D###U#####...###D#U#D#U###.#D#U..#D###.#
            15 #U..#DRRRR#.#.......SD#U#D#LLU..#D#U..#DRRRR#
            16 #U#.###########.#####D#U#D###U#.#D#U#.#####D#
            17 #U#.#LLU#.#LLU###LLU#D#U#D###U#.#D#U#.#LLU#D#
            18 #U#.#D#U#.#D#U#.#D#U#D#U#D#.#U#.#D#U###D#U#D#
            19 #LLLLD#LLLLD#LLLLD#LLD#LLD###LLLLD#LLLLD#LLD#
            20 #############################################
            """
        ).strip()
        self.assertEqual(output, expected)

    def test_headless_split_maze_claim_multistep(self):
        initial = run_script_file("headless_split_maze_claim_initial.script")
        expected_initial = textwrap.dedent(
            """
            Script complete
               012345678901234567890123456789012345678901234
             0 #############################################
             1 #v#.#.#.#.#.#.......#.#.......#.#.#.#.#.#.#v#
             2 #.#.#.#.#.#.#.#####.#.#.#####.#.#.#.#####.#.#
             3 #DRRRR#....##.....#...#.....#.....#.....#..D#
             4 ###.#D###.#URR#.#.###..##.#.###.#...#.#####D#
             5 #...#DRRRR#U#DRR#....#....#.....###...#LLU.D#
             6 ###.#####D#U###D###.#.###.#.###.#####.#D#U#D#
             7 #.#.#.#.#D#U#.#D#.#.#.#.#.#.#.#.#.#.#.#D#U#D#
             8 #.#.#.#.#D#U#.#D#.#.#.#.#.#.#.#.#.#.#.#D#U#D#
             9 #.....#..DRR#..DRR#...#.....#.....#....D#LLD#
            10 #######.#########D..#########.#########D#####
            11 #.#.#.#.#.#...#.#D###...#LLU#.#.#LLU#.#D#.#.#
            12 ###.#.#.###.#.#.#D#.#.#.#D#U#.#.#D#U#.#D#.#.#
            13 #.....#.#...#....S#......D.U..#..D.U#..D..#.#
            14 #.#.#.###.#####...###.#.#D#U###.#D#U..#D###.#
            15 #...#.....#.#.......S.#.#D#LLU..#D#U..#DRRRR#
            16 #.#.###########.#####.#.#D###U#.#D#U#.#####D#
            17 #.#.#...#.#...###...#.#.#.###U#.#D#U#.#LLU#D#
            18 #.#.#.#.#.#.#.#.#.#.#.#.#.#.#U#.#D#U###D#U#D#
            19 #.....#.....#.....#...#...###LLLLD#LLLLD#LLD#
            20 #############################################
            """
        ).strip()
        self.assertEqual(initial, expected_initial)

        final = run_script_file("headless_split_maze_claim_multistep.script")
        expected_final = textwrap.dedent(
            """
            Script complete
               012345678901234567890123456789012345678901234
             0 #############################################
             1 #v#.#.#.#.#.#.......#.#.......#.#.#.#.#.#.#v#
             2 #.#.#.#.#.#.#.#####.#.#.#####.#.#.#.#####.#.#
             3 #DRRRR#....##.....#...#.....#.....#.....#..D#
             4 ###.#D###.#URR#.#.###..##.#.###.#...#.#####D#
             5 #...#DRRRR#U#DRR#....#....#.....###...#LLU.D#
             6 ###.#####D#U###D###.#.###.#.###.#####.#D#U#D#
             7 #.#.#.#.#D#U#.#D#.#.#.#.#.#.#.#.#.#.#.#D#U#D#
             8 #.#.#.#.#D#U#.#D#.#.#.#.#.#.#.#.#.#.#.#D#U#D#
             9 #.....#..DRR#..DRR#...#.....#.....#....D#LLD#
            10 #######.#########D..#########.#########D#####
            11 #.#.#.#.#.#URR#.#D###LLU#LLU#.#.#LLU#.#D#.#.#
            12 ###.#.#.###U#D#.#D#.#D#U#D#U#.#.#D#U#.#D#.#.#
            13 #URRRR#.#URR#DRRRS#..D.U.D.U..#..D.U#..D..#.#
            14 #U#.#D###U#####...###D#U#D#U###.#D#U..#D###.#
            15 #U..#DRRRR#.#.......SD#U#D#LLU..#D#U..#DRRRR#
            16 #U#.###########.#####D#U#D###U#.#D#U#.#####D#
            17 #U#.#LLU#.#LLU###LLU#D#U#D###U#.#D#U#.#LLU#D#
            18 #U#.#D#U#.#D#U#.#D#U#D#U#D#.#U#.#D#U###D#U#D#
            19 #LLLLD#LLLLD#LLLLD#LLD#LLD###LLLLD#LLLLD#LLD#
            20 #############################################
            """
        ).strip()
        self.assertEqual(final, expected_final)

    def test_headless_clear_matches_expected_output(self):
        output = run_script_file("headless_clear.script")
        expected = textwrap.dedent(
            """
            Script complete
               0123456789012345678901234567
             0 ############################
             1 #>.RRRRRRRRRRRRRRRRRRRRRRRS#
             2 #..........................#
             3 #.........#................#
             4 #SLLLLLLLLU................#
             5 #..........................#
             6 #.........^................#
             7 ############################
            """
        ).strip()
        self.assertEqual(output, expected)
