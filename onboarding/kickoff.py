"""One kickoff command. Refuses to build the crew when the provider env is empty."""

import os
import sys

from onboarding.tools.read_prepared_cases import (
    FAILURE_SENTENCE,
    report_has_required_sentences,
    reset_tool_called,
    tool_was_called,
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        print(FAILURE_SENTENCE)
        return 1
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL_NAME", "").strip()
    if not key or not model:
        print(FAILURE_SENTENCE)
        return 1

    reset_tool_called()
    try:
        from onboarding.crew import run_crew

        report = run_crew(model)
    except Exception:
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
