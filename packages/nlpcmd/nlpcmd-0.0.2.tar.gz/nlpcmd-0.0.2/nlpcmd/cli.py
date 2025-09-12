"""Entry point CLI for nlpcmd."""
import argparse
import sys
from .engine import parse
from . import actions

INTENT_MAP = {
    "show_ip": actions.show_ip,
    "whoami": actions.whoami,
    "greet": actions.greet,
    "datetime": actions.datetime_action,
    "ping_host": actions.ping_host,
    "unknown": actions.unknown,
}


def repl():
    print("nlpcmd — natural-language command helper. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit"):
            break
        intent, params = parse(text)
        handler = INTENT_MAP.get(intent, actions.unknown)
        try:
            result = handler(params)
        except Exception as e:
            result = f"Error while executing action: {e}"
        print(result)


def run_once(args=None):
    """Run a single command from command-line args or enter REPL if none."""
    parser = argparse.ArgumentParser(prog="nlpcmd", description="NL-like Windows helper CLI")
    parser.add_argument("text", nargs="*", help="Natural language command to run (if omitted, enters interactive mode)")
    parsed = parser.parse_args(args=args)
    if parsed.text:
        text = " ".join(parsed.text)
        intent, params = parse(text)
        handler = INTENT_MAP.get(intent, actions.unknown)
        try:
            out = handler(params)
        except Exception as e:
            out = f"Error while executing action: {e}"
        print(out)
    else:
        repl()


def main():
    run_once(sys.argv[1:])


if __name__ == "__main__":
    main()
