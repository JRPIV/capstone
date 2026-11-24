"""Sequential two-task crew. The page does not import this module."""

from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

from onboarding.tools.read_prepared_cases import prepared_cases_json

CONFIG_DIR = Path(__file__).resolve().parent / "config"
EXPECTED_TOOLS = {
    "fixture_reader": ["read_prepared_cases"],
    "case_reporter": [],
}
TASK_ORDER = ("load_prepared_cases", "report_prepared_cases")
TASK_AGENTS = {
    "load_prepared_cases": "fixture_reader",
    "report_prepared_cases": "case_reporter",
}


class ToolBindingError(RuntimeError):
    """YAML names a tool this package does not bind. No provider call follows."""


@tool("read_prepared_cases", max_usage_count=1)
def read_prepared_cases() -> str:
    """Return the four prepared Sprint 3 cases as JSON. Takes no arguments."""
    return prepared_cases_json()


BOUND_TOOLS = {"read_prepared_cases": read_prepared_cases}


def run_crew(model: str) -> str:
    agents_config = _load_yaml("agents.yaml")
    tasks_config = _load_yaml("tasks.yaml")
    _validate_tools(agents_config)
    _validate_tasks(tasks_config)
    reader = _build_agent("fixture_reader", agents_config["fixture_reader"], model)
    reporter = _build_agent("case_reporter", agents_config["case_reporter"], model)
    agents = {"fixture_reader": reader, "case_reporter": reporter}
    load_task = _build_task("load_prepared_cases", tasks_config["load_prepared_cases"], agents, None)
    report_task = _build_task(
        "report_prepared_cases",
        tasks_config["report_prepared_cases"],
        agents,
        [load_task],
    )
    crew = Crew(
        agents=[reader, reporter],
        tasks=[load_task, report_task],
        process=Process.sequential,
        memory=False,
        verbose=False,
    )
    return str(crew.kickoff())


def _load_yaml(name: str) -> dict:
    path = CONFIG_DIR / name
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ToolBindingError(f"{name} is not a mapping")
    return loaded


def _validate_tools(agents_config: dict) -> None:
    if set(agents_config) != set(EXPECTED_TOOLS):
        raise ToolBindingError("agent names do not match the Sprint 3 pair")
    for name, expected in EXPECTED_TOOLS.items():
        configured = list(agents_config[name].get("tools") or [])
        if configured != expected:
            raise ToolBindingError(f"{name} tools do not match {expected}")
        for tool_name in configured:
            if tool_name not in BOUND_TOOLS:
                raise ToolBindingError(f"unbound tool {tool_name}")


def _validate_tasks(tasks_config: dict) -> None:
    if tuple(tasks_config) != TASK_ORDER:
        raise ToolBindingError("task order is not load_prepared_cases then report_prepared_cases")
    for name, agent_name in TASK_AGENTS.items():
        if tasks_config[name].get("agent") != agent_name:
            raise ToolBindingError(f"{name} is not assigned to {agent_name}")
    context = list(tasks_config["report_prepared_cases"].get("context") or [])
    if context != ["load_prepared_cases"]:
        raise ToolBindingError("report_prepared_cases context is not load_prepared_cases")


def _build_agent(name: str, config: dict, model: str) -> Agent:
    if config.get("allow_delegation") is not False:
        raise ToolBindingError(f"{name} must set allow_delegation false")
    if int(config.get("max_iter", 0)) != 2:
        raise ToolBindingError(f"{name} must set max_iter 2")
    tools = [BOUND_TOOLS[tool_name] for tool_name in EXPECTED_TOOLS[name]]
    return Agent(
        role=str(config["role"]).strip(),
        goal=str(config["goal"]).strip(),
        backstory=str(config["backstory"]).strip(),
        allow_delegation=False,
        max_iter=2,
        max_execution_time=60,
        max_retry_limit=2,
        tools=tools,
        llm=model,
        verbose=False,
    )


def _build_task(name: str, config: dict, agents: dict, context: list | None) -> Task:
    return Task(
        name=name,
        description=str(config["description"]).strip(),
        expected_output=str(config["expected_output"]).strip(),
        agent=agents[TASK_AGENTS[name]],
        context=context,
    )
