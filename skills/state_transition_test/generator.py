"""
State Transition Test Case Generator

This module provides logic to generate test cases for state transition testing
from a given state machine definition.

Supported coverage criteria:
- all_states      : All States Coverage (N-switch 0) - visit every state at least once
- all_transitions : All Transitions Coverage (N-switch 1) - exercise every transition at least once
- all_with_invalid: All Transitions + Invalid Transitions (negative tests)
"""

from dataclasses import dataclass, field
from collections import deque
from typing import Optional


@dataclass
class Transition:
    """Represents a single state transition."""
    from_state: str
    event: str
    to_state: str
    condition: Optional[str] = None
    action: Optional[str] = None


@dataclass
class StateMachine:
    """Represents a finite state machine."""
    states: list
    initial_state: str
    final_states: list
    transitions: list
    events: list = field(default_factory=list)


@dataclass
class TestStep:
    """A single step within a test case."""
    current_state: str
    event: str
    next_state: Optional[str]
    expected_result: str = "transition succeeds"


@dataclass
class TestCase:
    """A generated test case."""
    id: str
    description: str
    precondition: str
    steps: list
    expected_final_state: str
    coverage_criterion: str


class StateTransitionTestGenerator:
    """Generates test cases from a state machine definition."""

    def __init__(self, state_machine: StateMachine):
        self.sm = state_machine
        self._build_maps()

    def _build_maps(self):
        """Build lookup maps for efficient transition access."""
        self.trans_from = {}   # state -> list[Transition]
        self.trans_key = {}    # (from_state, event) -> Transition

        for t in self.sm.transitions:
            self.trans_from.setdefault(t.from_state, []).append(t)
            self.trans_key[(t.from_state, t.event)] = t

    # ------------------------------------------------------------------
    # Path-finding helpers
    # ------------------------------------------------------------------

    def _find_path(self, start: str, end: str) -> list:
        """BFS to find the shortest path from start to end state.

        Returns a list of TestStep, or an empty list if no path exists.
        """
        if start == end:
            return []

        queue = deque([(start, [])])
        visited = {start}

        while queue:
            current, path = queue.popleft()
            for trans in self.trans_from.get(current, []):
                if trans.to_state not in visited:
                    new_path = path + [TestStep(
                        current_state=trans.from_state,
                        event=trans.event,
                        next_state=trans.to_state,
                    )]
                    if trans.to_state == end:
                        return new_path
                    visited.add(trans.to_state)
                    queue.append((trans.to_state, new_path))

        return []  # no path found

    def _find_path_via_transition(self, target: Transition) -> list:
        """Return a path that includes the given transition.

        The path begins from the initial state and ends at the transition's
        destination state.
        """
        prefix = self._find_path(self.sm.initial_state, target.from_state)
        step = TestStep(
            current_state=target.from_state,
            event=target.event,
            next_state=target.to_state,
        )
        return prefix + [step]

    # ------------------------------------------------------------------
    # Coverage strategies
    # ------------------------------------------------------------------

    def generate_all_states_coverage(self) -> list:
        """Generate minimal test cases that visit every state at least once."""
        covered = set()
        test_cases = []
        tc_id = 1

        # Always start from initial state
        covered.add(self.sm.initial_state)

        for state in self.sm.states:
            if state in covered:
                continue
            path = self._find_path(self.sm.initial_state, state)
            if not path:
                continue

            for step in path:
                covered.add(step.current_state)
                covered.add(step.next_state)

            final_state = path[-1].next_state if path else self.sm.initial_state
            test_cases.append(TestCase(
                id=f"TC-{tc_id:03d}",
                description=f"Reach state [{state}]",
                precondition=f"System is in initial state [{self.sm.initial_state}]",
                steps=path,
                expected_final_state=final_state,
                coverage_criterion="All States Coverage",
            ))
            tc_id += 1

        # If the initial state itself was the only state, add a no-op test
        if not test_cases and self.sm.states:
            test_cases.append(TestCase(
                id="TC-001",
                description=f"System starts in initial state [{self.sm.initial_state}]",
                precondition=f"System is in initial state [{self.sm.initial_state}]",
                steps=[],
                expected_final_state=self.sm.initial_state,
                coverage_criterion="All States Coverage",
            ))

        return test_cases

    def generate_all_transitions_coverage(self) -> list:
        """Generate minimal test cases that exercise every transition at least once."""
        covered = set()
        test_cases = []
        tc_id = 1

        for trans in self.sm.transitions:
            key = (trans.from_state, trans.event, trans.to_state)
            if key in covered:
                continue

            path = self._find_path_via_transition(trans)
            for step in path:
                covered.add((step.current_state, step.event, step.next_state))

            final_state = path[-1].next_state if path else self.sm.initial_state
            test_cases.append(TestCase(
                id=f"TC-{tc_id:03d}",
                description=(
                    f"Transition [{trans.from_state}] --[{trans.event}]--> [{trans.to_state}]"
                ),
                precondition=f"System is in initial state [{self.sm.initial_state}]",
                steps=path,
                expected_final_state=final_state,
                coverage_criterion="All Transitions Coverage",
            ))
            tc_id += 1

        return test_cases

    def generate_invalid_transitions(self) -> list:
        """Generate negative test cases for invalid (undefined) transitions."""
        all_events = {t.event for t in self.sm.transitions}
        test_cases = []
        tc_id = 1

        for state in self.sm.states:
            valid_events = {t.event for t in self.trans_from.get(state, [])}
            invalid_events = sorted(all_events - valid_events)

            for event in invalid_events:
                prefix = (
                    self._find_path(self.sm.initial_state, state)
                    if state != self.sm.initial_state
                    else []
                )
                invalid_step = TestStep(
                    current_state=state,
                    event=event,
                    next_state=None,
                    expected_result="transition rejected / state unchanged",
                )
                test_cases.append(TestCase(
                    id=f"TC-NEG-{tc_id:03d}",
                    description=(
                        f"Invalid event [{event}] in state [{state}] should be rejected"
                    ),
                    precondition=f"System is in initial state [{self.sm.initial_state}]",
                    steps=prefix + [invalid_step],
                    expected_final_state=state,
                    coverage_criterion="Invalid Transitions (Negative Tests)",
                ))
                tc_id += 1

        return test_cases

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate(self, coverage: str = "all_transitions") -> dict:
        """Generate test cases according to the requested coverage criterion.

        Args:
            coverage: One of
                - ``"all_states"``       – All States Coverage
                - ``"all_transitions"``  – All Transitions Coverage (default)
                - ``"all_with_invalid"`` – All Transitions + Invalid Transitions

        Returns:
            A dictionary containing metadata and the list of test cases.
        """
        test_cases: list = []

        if coverage == "all_states":
            test_cases = self.generate_all_states_coverage()
        elif coverage == "all_transitions":
            test_cases = self.generate_all_transitions_coverage()
        elif coverage == "all_with_invalid":
            test_cases = (
                self.generate_all_transitions_coverage()
                + self.generate_invalid_transitions()
            )
        else:
            raise ValueError(
                f"Unknown coverage criterion: '{coverage}'. "
                "Choose from 'all_states', 'all_transitions', 'all_with_invalid'."
            )

        return {
            "metadata": {
                "total_states": len(self.sm.states),
                "total_events": len(self.sm.events),
                "total_transitions": len(self.sm.transitions),
                "coverage_criterion": coverage,
                "total_test_cases": len(test_cases),
            },
            "test_cases": [_test_case_to_dict(tc) for tc in test_cases],
        }


# ------------------------------------------------------------------
# Serialization helpers
# ------------------------------------------------------------------

def _step_to_dict(step: TestStep) -> dict:
    d = {
        "current_state": step.current_state,
        "event": step.event,
        "next_state": step.next_state,
        "expected_result": step.expected_result,
    }
    return d


def _test_case_to_dict(tc: TestCase) -> dict:
    return {
        "id": tc.id,
        "description": tc.description,
        "precondition": tc.precondition,
        "coverage_criterion": tc.coverage_criterion,
        "steps": [_step_to_dict(s) for s in tc.steps],
        "expected_final_state": tc.expected_final_state,
    }


# ------------------------------------------------------------------
# Input parsing
# ------------------------------------------------------------------

def parse_state_machine(data: dict) -> StateMachine:
    """Parse a StateMachine from a plain dictionary.

    Expected format::

        {
            "states": ["S0", "S1", "S2"],
            "initial_state": "S0",
            "final_states": ["S2"],          // optional
            "transitions": [
                {"from": "S0", "event": "login", "to": "S1"},
                {"from": "S1", "event": "logout", "to": "S0"},
                {"from": "S1", "event": "purchase", "to": "S2"}
            ]
        }
    """
    transitions = []
    for t in data.get("transitions", []):
        transitions.append(Transition(
            from_state=t["from"],
            event=t["event"],
            to_state=t["to"],
            condition=t.get("condition"),
            action=t.get("action"),
        ))

    events = list({t.event for t in transitions})

    return StateMachine(
        states=data["states"],
        initial_state=data["initial_state"],
        final_states=data.get("final_states", []),
        transitions=transitions,
        events=events,
    )
