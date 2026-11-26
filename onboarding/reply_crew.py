"""One tool-free reply_reader task. The prepared-example crew is a different module."""

import json
import os
from pathlib import Path

import yaml
from crewai import LLM, Agent, Crew, Process, Task

from onboarding.equipment import ProviderFailure


CONFIG_DIR = Path(__file__).resolve().parent / "config"
DEFAULT_MODEL = "gemini/gemini-3.5-flash-lite"
RETRY_LIMITS = {
    "max_iter": 2,
    "max_retry_limit": 0,
    "llm_max_retries": 0,
    "application_attempts": 1,
}
application_calls = 0


def read_equipment_reply(event: dict, case: dict) -> dict:
    """Call the provider once. The application does not retry this function."""
    global application_calls
    application_calls += 1
    agents_config = _load_yaml("reply_agents.yaml")
    tasks_config = _load_yaml("reply_tasks.yaml")
    _validate(agents_config, tasks_config)
    model = os.environ.get("GEMINI_MODEL_NAME", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if not os.environ.get("GEMINI_API_KEY", "").strip() or not model.startswith("gemini/"):
        raise ProviderFailure("config")
    llm = LLM(
        model=model,
        api_key=os.environ["GEMINI_API_KEY"],
        temperature=0,
        timeout=45,
        max_retries=RETRY_LIMITS["llm_max_retries"],
    )
    config = agents_config["reply_reader"]
    agent = Agent(
        role=str(config["role"]).strip(),
        goal=str(config["goal"]).strip(),
        backstory=str(config["backstory"]).strip(),
        allow_delegation=False,
        max_iter=RETRY_LIMITS["max_iter"],
        max_execution_time=60,
        max_retry_limit=RETRY_LIMITS["max_retry_limit"],
        tools=[],
        llm=llm,
        verbose=False,
    )
    description, expected_output = reply_task_text(event, case)
    task = Task(
        name="read_equipment_reply",
        description=description,
        expected_output=expected_output,
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        memory=False,
        verbose=False,
    )
    try:
        raw = str(crew.kickoff())
    except Exception as exc:
        raise ProviderFailure(type(exc).__name__) from None
    return _parse_json(raw)


def reply_task_text(event: dict, case: dict) -> tuple[str, str]:
    """Return the filled description and the expected output from the task file."""
    loaded = _load_yaml("reply_tasks.yaml")["read_equipment_reply"]
    return render_description(event, case), str(loaded["expected_output"]).strip()


def render_description(event: dict, case: dict) -> str:
    """Fill the reply task. The message is substituted last, so it is not rewritten."""
    template = str(_load_yaml("reply_tasks.yaml")["read_equipment_reply"]["description"])
    rendered = (
        template.replace("{start_date}", str(case["start_date"]))
        .replace("{occurred_at}", str(event["occurred_at"]))
        .replace("{actor_role}", str(event["actor_role"]))
    )
    return rendered.replace("{message}", str(event["body"]))


def _parse_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ProviderFailure("invalid-json")
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        raise ProviderFailure("invalid-json") from None
    if not isinstance(parsed, dict):
        raise ProviderFailure("invalid-json")
    return parsed


def _load_yaml(name: str) -> dict:
    loaded = yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ProviderFailure("config")
    return loaded


def _validate(agents_config: dict, tasks_config: dict) -> None:
    if set(agents_config) != {"reply_reader"}:
        raise ProviderFailure("config")
    agent = agents_config["reply_reader"]
    if agent.get("allow_delegation") is not False:
        raise ProviderFailure("config")
    if int(agent.get("max_iter", 0)) != RETRY_LIMITS["max_iter"]:
        raise ProviderFailure("config")
    if list(agent.get("tools") or []) != []:
        raise ProviderFailure("config")
    if set(tasks_config) != {"read_equipment_reply"}:
        raise ProviderFailure("config")
    if tasks_config["read_equipment_reply"].get("agent") != "reply_reader":
        raise ProviderFailure("config")
