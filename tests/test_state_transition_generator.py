"""Tests for the state transition test case generator skill."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.state_transition_test.generator import (
    parse_state_machine,
    StateTransitionTestGenerator,
)
from skills.state_transition_test.skill import run, SKILL_DEFINITION


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SIMPLE_SM = {
    "states": ["S0", "S1", "S2"],
    "initial_state": "S0",
    "final_states": ["S2"],
    "transitions": [
        {"from": "S0", "event": "E1", "to": "S1"},
        {"from": "S1", "event": "E2", "to": "S2"},
        {"from": "S1", "event": "E3", "to": "S0"},
    ],
}

BRANCHING_SM = {
    "states": ["Idle", "Processing", "Approved", "Declined"],
    "initial_state": "Idle",
    "final_states": ["Approved", "Declined"],
    "transitions": [
        {"from": "Idle",       "event": "submit",  "to": "Processing"},
        {"from": "Processing", "event": "approve", "to": "Approved"},
        {"from": "Processing", "event": "decline", "to": "Declined"},
    ],
}


# ---------------------------------------------------------------------------
# parse_state_machine
# ---------------------------------------------------------------------------

class TestParseStateMachine:
    def test_basic_parse(self):
        sm = parse_state_machine(SIMPLE_SM)
        assert sm.states == ["S0", "S1", "S2"]
        assert sm.initial_state == "S0"
        assert sm.final_states == ["S2"]
        assert len(sm.transitions) == 3

    def test_events_extracted(self):
        sm = parse_state_machine(SIMPLE_SM)
        assert set(sm.events) == {"E1", "E2", "E3"}

    def test_optional_condition_action(self):
        data = {
            "states": ["A", "B"],
            "initial_state": "A",
            "transitions": [
                {"from": "A", "event": "go", "to": "B", "condition": "x>0", "action": "log()"},
            ],
        }
        sm = parse_state_machine(data)
        t = sm.transitions[0]
        assert t.condition == "x>0"
        assert t.action == "log()"

    def test_missing_final_states_defaults_to_empty(self):
        data = {
            "states": ["A", "B"],
            "initial_state": "A",
            "transitions": [{"from": "A", "event": "e", "to": "B"}],
        }
        sm = parse_state_machine(data)
        assert sm.final_states == []


# ---------------------------------------------------------------------------
# All States Coverage
# ---------------------------------------------------------------------------

class TestAllStatesCoverage:
    def setup_method(self):
        sm = parse_state_machine(SIMPLE_SM)
        self.gen = StateTransitionTestGenerator(sm)

    def test_all_states_are_covered(self):
        test_cases = self.gen.generate_all_states_coverage()
        visited = set()
        for tc in test_cases:
            visited.add(tc.expected_final_state)
            for step in tc.steps:
                visited.add(step.current_state)
                if step.next_state:
                    visited.add(step.next_state)
        assert {"S0", "S1", "S2"}.issubset(visited)

    def test_returns_list_of_test_cases(self):
        test_cases = self.gen.generate_all_states_coverage()
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0

    def test_coverage_criterion_label(self):
        for tc in self.gen.generate_all_states_coverage():
            assert tc.coverage_criterion == "All States Coverage"


# ---------------------------------------------------------------------------
# All Transitions Coverage
# ---------------------------------------------------------------------------

class TestAllTransitionsCoverage:
    def setup_method(self):
        sm = parse_state_machine(SIMPLE_SM)
        self.gen = StateTransitionTestGenerator(sm)

    def test_all_transitions_covered(self):
        test_cases = self.gen.generate_all_transitions_coverage()
        covered = set()
        for tc in test_cases:
            for step in tc.steps:
                covered.add((step.current_state, step.event, step.next_state))

        for t in parse_state_machine(SIMPLE_SM).transitions:
            assert (t.from_state, t.event, t.to_state) in covered, (
                f"Transition {t.from_state}--[{t.event}]-->{t.to_state} not covered"
            )

    def test_branching_sm_all_transitions(self):
        sm = parse_state_machine(BRANCHING_SM)
        gen = StateTransitionTestGenerator(sm)
        test_cases = gen.generate_all_transitions_coverage()
        covered = set()
        for tc in test_cases:
            for step in tc.steps:
                covered.add((step.current_state, step.event, step.next_state))
        for t in sm.transitions:
            assert (t.from_state, t.event, t.to_state) in covered

    def test_coverage_criterion_label(self):
        for tc in self.gen.generate_all_transitions_coverage():
            assert tc.coverage_criterion == "All Transitions Coverage"

    def test_steps_start_from_initial_state(self):
        sm = parse_state_machine(SIMPLE_SM)
        gen = StateTransitionTestGenerator(sm)
        for tc in gen.generate_all_transitions_coverage():
            if tc.steps:
                assert tc.steps[0].current_state == sm.initial_state


# ---------------------------------------------------------------------------
# Invalid Transitions (Negative Tests)
# ---------------------------------------------------------------------------

class TestInvalidTransitions:
    def setup_method(self):
        sm = parse_state_machine(SIMPLE_SM)
        self.gen = StateTransitionTestGenerator(sm)
        self.sm = sm

    def test_negative_tests_generated(self):
        neg_tests = self.gen.generate_invalid_transitions()
        assert len(neg_tests) > 0

    def test_invalid_step_has_no_next_state(self):
        neg_tests = self.gen.generate_invalid_transitions()
        for tc in neg_tests:
            last_step = tc.steps[-1]
            assert last_step.next_state is None

    def test_state_unchanged_expectation(self):
        neg_tests = self.gen.generate_invalid_transitions()
        for tc in neg_tests:
            last_step = tc.steps[-1]
            assert tc.expected_final_state == last_step.current_state

    def test_coverage_criterion_label(self):
        for tc in self.gen.generate_invalid_transitions():
            assert tc.coverage_criterion == "Invalid Transitions (Negative Tests)"


# ---------------------------------------------------------------------------
# generate() entry point
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_all_states_mode(self):
        sm = parse_state_machine(SIMPLE_SM)
        gen = StateTransitionTestGenerator(sm)
        result = gen.generate("all_states")
        assert "metadata" in result
        assert "test_cases" in result
        assert result["metadata"]["coverage_criterion"] == "all_states"

    def test_all_transitions_mode(self):
        sm = parse_state_machine(SIMPLE_SM)
        gen = StateTransitionTestGenerator(sm)
        result = gen.generate("all_transitions")
        assert result["metadata"]["coverage_criterion"] == "all_transitions"

    def test_all_with_invalid_mode(self):
        sm = parse_state_machine(SIMPLE_SM)
        gen = StateTransitionTestGenerator(sm)
        result = gen.generate("all_with_invalid")
        criteria = {tc["coverage_criterion"] for tc in result["test_cases"]}
        assert "All Transitions Coverage" in criteria
        assert "Invalid Transitions (Negative Tests)" in criteria

    def test_invalid_coverage_raises(self):
        sm = parse_state_machine(SIMPLE_SM)
        gen = StateTransitionTestGenerator(sm)
        with pytest.raises(ValueError, match="Unknown coverage criterion"):
            gen.generate("unknown")

    def test_metadata_counts(self):
        sm = parse_state_machine(SIMPLE_SM)
        gen = StateTransitionTestGenerator(sm)
        result = gen.generate("all_transitions")
        assert result["metadata"]["total_states"] == 3
        assert result["metadata"]["total_transitions"] == 3
        assert result["metadata"]["total_test_cases"] == len(result["test_cases"])


# ---------------------------------------------------------------------------
# run() skill entry point
# ---------------------------------------------------------------------------

class TestRunSkill:
    def test_run_with_state_machine_key(self):
        result = run({"state_machine": SIMPLE_SM, "coverage": "all_transitions"})
        assert "test_cases" in result
        assert len(result["test_cases"]) > 0

    def test_run_default_coverage(self):
        result = run({"state_machine": BRANCHING_SM})
        assert result["metadata"]["coverage_criterion"] == "all_transitions"

    def test_test_case_fields_present(self):
        result = run({"state_machine": SIMPLE_SM, "coverage": "all_transitions"})
        for tc in result["test_cases"]:
            assert "id" in tc
            assert "description" in tc
            assert "precondition" in tc
            assert "steps" in tc
            assert "expected_final_state" in tc
            assert "coverage_criterion" in tc

    def test_step_fields_present(self):
        result = run({"state_machine": SIMPLE_SM, "coverage": "all_transitions"})
        for tc in result["test_cases"]:
            for step in tc["steps"]:
                assert "current_state" in step
                assert "event" in step
                assert "next_state" in step
                assert "expected_result" in step


# ---------------------------------------------------------------------------
# SKILL_DEFINITION schema
# ---------------------------------------------------------------------------

class TestSkillDefinition:
    def test_name(self):
        assert SKILL_DEFINITION["name"] == "generate_state_transition_test_cases"

    def test_required_fields(self):
        assert "description" in SKILL_DEFINITION
        assert "parameters" in SKILL_DEFINITION

    def test_coverage_enum(self):
        props = SKILL_DEFINITION["parameters"]["properties"]
        assert set(props["coverage"]["enum"]) == {
            "all_states",
            "all_transitions",
            "all_with_invalid",
        }
