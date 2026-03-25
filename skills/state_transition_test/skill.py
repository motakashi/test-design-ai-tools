"""
State Transition Test Case Generator - Agent Skill

Entry point for use as an AI agent skill / tool.
"""

import json
import sys
from .generator import parse_state_machine, StateTransitionTestGenerator


# ---------------------------------------------------------------------------
# Skill definition (OpenAI / GitHub Copilot function-calling schema)
# ---------------------------------------------------------------------------

SKILL_DEFINITION = {
    "name": "generate_state_transition_test_cases",
    "description": (
        "Generate test cases for state transition testing from a given state machine. "
        "Supports All States Coverage, All Transitions Coverage, and Invalid Transitions "
        "(negative tests) as coverage criteria."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "state_machine": {
                "type": "object",
                "description": "The state machine definition.",
                "properties": {
                    "states": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of all states in the state machine.",
                    },
                    "initial_state": {
                        "type": "string",
                        "description": "The starting state of the state machine.",
                    },
                    "final_states": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of final/accepting states (optional).",
                    },
                    "transitions": {
                        "type": "array",
                        "description": "List of transitions between states.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from": {
                                    "type": "string",
                                    "description": "Source state.",
                                },
                                "event": {
                                    "type": "string",
                                    "description": "Event or input that triggers the transition.",
                                },
                                "to": {
                                    "type": "string",
                                    "description": "Destination state.",
                                },
                                "condition": {
                                    "type": "string",
                                    "description": "Guard condition (optional).",
                                },
                                "action": {
                                    "type": "string",
                                    "description": "Action performed during the transition (optional).",
                                },
                            },
                            "required": ["from", "event", "to"],
                        },
                    },
                },
                "required": ["states", "initial_state", "transitions"],
            },
            "coverage": {
                "type": "string",
                "enum": ["all_states", "all_transitions", "all_with_invalid"],
                "description": (
                    "Coverage criterion to use when generating test cases. "
                    "'all_states' covers every state at least once. "
                    "'all_transitions' covers every transition at least once (default). "
                    "'all_with_invalid' covers all transitions plus invalid/negative cases."
                ),
                "default": "all_transitions",
            },
        },
        "required": ["state_machine"],
    },
}


# ---------------------------------------------------------------------------
# Skill entry point
# ---------------------------------------------------------------------------

def run(input_data: dict) -> dict:
    """Execute the skill.

    Args:
        input_data: Dictionary matching the ``SKILL_DEFINITION`` parameter schema.

    Returns:
        Dictionary with ``metadata`` and ``test_cases`` keys.
    """
    sm_data = input_data.get("state_machine", input_data)
    coverage = input_data.get("coverage", "all_transitions")

    state_machine = parse_state_machine(sm_data)
    generator = StateTransitionTestGenerator(state_machine)
    return generator.generate(coverage)


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

def _cli():
    """Command-line interface for the skill.

    Usage:
        python -m skills.state_transition_test input.json [coverage]

    Arguments:
        input.json  Path to a JSON file containing the state machine definition.
        coverage    Optional coverage criterion (default: all_transitions).
    """
    if len(sys.argv) < 2:
        print("Usage: python -m skills.state_transition_test <input.json> [coverage]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    coverage = sys.argv[2] if len(sys.argv) > 2 else "all_transitions"

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    data["coverage"] = coverage
    result = run(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
