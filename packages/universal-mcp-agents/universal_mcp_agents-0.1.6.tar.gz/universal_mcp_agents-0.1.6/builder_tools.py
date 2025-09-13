from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.agents.builder import BuilderAgent
import json


def load_tasks():
    with open("src/evals/datasets/tasks.jsonl", "r") as f:
        for line in f:
            yield json.loads(line)


async def main():
    registry = AgentrRegistry()
    builder = BuilderAgent(
        name="Builder Agent",
        instructions="You are a builder agent that creates other agents.",
        model="gemini/gemini-1.5-pro",
        registry=registry,
    )
    updated_tasks = []
    tasks = load_tasks()
    for task in tasks:
        print(task["user_input"])
        result = await builder.invoke(task["user_input"])
        tools = result["tool_config"] or {}
        updated_tasks.append({**task, "required_tools": tools})
    with open("src/evals/datasets/tasks_with_tools.jsonl", "w") as f:
        for task in updated_tasks:
            f.write(json.dumps(task) + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())