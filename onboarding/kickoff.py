"""One kickoff command. Refuses to build the crew when the provider env is empty."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from onboarding.tools.read_prepared_cases import (
    FAILURE_SENTENCE,
    report_has_required_sentences,
    reset_tool_called,
    tool_was_called,
)


DEFAULT_MODEL = "gemini/gemini-3.5-flash-lite"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        print(FAILURE_SENTENCE)
        return 1
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL_NAME", DEFAULT_MODEL).strip()
    if not key or not model.startswith("gemini/"):
        print("Configuration error: set GEMINI_API_KEY and a gemini/ model.", file=sys.stderr)
        print(FAILURE_SENTENCE)
        return 1

    reset_tool_called()
    try:
        from onboarding.crew import run_crew

        report = run_crew(model)
    except Exception as exc:
        # Never print provider messages: they can contain credentials or request URLs.
        print(f"Kickoff failed ({type(exc).__name__}); no verified result.", file=sys.stderr)
        print(FAILURE_SENTENCE)
        return 1

    text = str(report).strip()
    if not tool_was_called() or not report_has_required_sentences(text):
        if text:
            print(text)
        print(FAILURE_SENTENCE)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
