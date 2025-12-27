import argparse

from dsl import run_script
from game import run_game
from levels import LEVELS, get_level
from simulation import run_headless


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without a window for a duration and print ASCII board state.",
    )
    parser.add_argument(
        "--level",
        default="empty",
        help="Level to load (choices: {}).".format(", ".join(sorted(LEVELS))),
    )
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=5000,
        help="Duration to simulate in headless mode.",
    )
    parser.add_argument(
        "--script",
        help="Tiny DSL: commands separated by newlines/semicolons: level NAME | wait N | wait_ms MS | add X,Y | remove X,Y",
    )
    parser.add_argument(
        "--script-file",
        help="Path to a script file using the DSL (ignored if --script is provided).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    script_text = None
    if args.script:
        script_text = args.script
    elif args.script_file:
        with open(args.script_file, "r") as fh:
            script_text = fh.read()

    if args.headless:
        if script_text:
            run_script(script_text, default_level_name=args.level)
        else:
            run_headless(args.duration_ms, get_level(args.level))
        return

    run_game(args.level)


if __name__ == "__main__":
    main()
