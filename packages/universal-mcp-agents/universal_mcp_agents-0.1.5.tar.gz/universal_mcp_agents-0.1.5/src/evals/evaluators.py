
from agentevals.trajectory.llm import (
    TRAJECTORY_ACCURACY_PROMPT,
    create_trajectory_llm_as_judge,
)
from langsmith.evaluation import EvaluationResult, run_evaluator
from langsmith.schemas import Example, Run
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT


@run_evaluator
def exact_match_evaluator(run: Run, example: Example | None = None) -> EvaluationResult:
    """
    A simple evaluator that checks for exact match between the agent's output
    and the expected output from the dataset.
    """
    if example is None or "expected_output" not in example.outputs:
        return EvaluationResult(
            key="exact_match", score=0, comment="No expected output provided. Example: " + str(example)
        )

    # The agent's response might be in a list of messages
    agent_response_raw = run.outputs.get("output", "")
    if isinstance(agent_response_raw, list):
        # Extract text from the last dictionary in the list
        agent_response_raw = agent_response_raw[-1]


    final_answer = agent_response_raw.get("content", "").strip().lower()

    expected_output = example.outputs["expected_output"].strip().lower()
    if final_answer == expected_output:
        score = 1
        comment = "Exact match."
    else:
        score = 0
        comment = f"Mismatch: Expected '{expected_output}', but got '{final_answer}'."

    return EvaluationResult(key="exact_match", score=score, comment=comment)


correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    model="anthropic:claude-4-sonnet-20250514",
)


trajectory_evaluator = create_trajectory_llm_as_judge(
    prompt=TRAJECTORY_ACCURACY_PROMPT,
    model="anthropic:claude-4-sonnet-20250514",
)
