"""
Tests voor WorkflowLoader — ollama/workflow_loader.py

Dekt:
- load() laadt correcte YAML workflows
- list_workflows() geeft alle namen
- get_steps_in_order() respecteert depends_on (topologisch)
- validate() detecteert circulaire afhankelijkheden
- validate() detecteert ontbrekende / ongeldige depends_on
- get_required_steps() filtert correct
- get_chain() geeft juiste chain
- Graceful fallback zonder yaml
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ollama.workflow_loader import (
    WorkflowDefinition,
    WorkflowLoader,
    WorkflowStep,
    _YAML_AVAILABLE,
)

# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def loader() -> WorkflowLoader:
    return WorkflowLoader()


@pytest.fixture
def order_workflow(loader: WorkflowLoader) -> WorkflowDefinition:
    return loader.load("order_pipeline")


@pytest.fixture
def product_workflow(loader: WorkflowLoader) -> WorkflowDefinition:
    return loader.load("product_pipeline")


@pytest.fixture
def fraud_workflow(loader: WorkflowLoader) -> WorkflowDefinition:
    return loader.load("fraud_pipeline")


def _make_simple_workflow(steps: list[WorkflowStep], chains: dict | None = None) -> WorkflowDefinition:
    return WorkflowDefinition(
        name="test-workflow",
        version="1.0",
        capability="test-cap",
        lane="deterministic",
        risk="low",
        audience="internal",
        inputs=[],
        outputs=[],
        steps=steps,
        chains=chains or {},
    )


# ─────────────────────────────────────────────
# 1. load() — correcte YAML laden
# ─────────────────────────────────────────────

@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_order_pipeline_name(order_workflow):
    assert order_workflow.name == "order-analysis-pipeline"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_order_pipeline_capability(order_workflow):
    assert order_workflow.capability == "order-validation"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_order_pipeline_lane(order_workflow):
    assert order_workflow.lane == "deterministic"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_order_pipeline_risk(order_workflow):
    assert order_workflow.risk == "medium"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_order_pipeline_steps_count(order_workflow):
    assert len(order_workflow.steps) == 3


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_product_pipeline(product_workflow):
    assert product_workflow.name == "product-content-pipeline"
    assert product_workflow.lane == "generative"
    assert len(product_workflow.steps) == 3


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_fraud_pipeline(fraud_workflow):
    assert fraud_workflow.name == "fraud-detection-pipeline"
    assert fraud_workflow.capability == "fraud-detection"
    assert fraud_workflow.risk == "high"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_by_workflow_name(loader):
    wf = loader.load("order-analysis-pipeline")
    assert wf.name == "order-analysis-pipeline"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_load_nonexistent_raises(loader):
    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent-workflow")


# ─────────────────────────────────────────────
# 2. list_workflows()
# ─────────────────────────────────────────────

@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_list_workflows_returns_all_three(loader):
    names = loader.list_workflows()
    assert len(names) == 3


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_list_workflows_contains_order(loader):
    names = loader.list_workflows()
    assert "order-analysis-pipeline" in names


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_list_workflows_contains_product(loader):
    names = loader.list_workflows()
    assert "product-content-pipeline" in names


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_list_workflows_contains_fraud(loader):
    names = loader.list_workflows()
    assert "fraud-detection-pipeline" in names


def test_list_workflows_empty_dir(tmp_path):
    loader = WorkflowLoader(workflows_dir=tmp_path)
    assert loader.list_workflows() == []


def test_list_workflows_nonexistent_dir():
    loader = WorkflowLoader(workflows_dir=Path("/nonexistent/path"))
    assert loader.list_workflows() == []


# ─────────────────────────────────────────────
# 3. get_steps_in_order() — topologische sortering
# ─────────────────────────────────────────────

def test_topological_order_respects_depends_on(loader):
    steps = [
        WorkflowStep("step-a", "skill_a", True, []),
        WorkflowStep("step-b", "skill_b", True, ["step-a"]),
        WorkflowStep("step-c", "skill_c", True, ["step-b"]),
    ]
    wf = _make_simple_workflow(steps)
    ordered = loader.get_steps_in_order(wf)
    ids = [s.id for s in ordered]
    assert ids.index("step-a") < ids.index("step-b")
    assert ids.index("step-b") < ids.index("step-c")


def test_topological_order_parallel_branches(loader):
    steps = [
        WorkflowStep("root", "skill_root", True, []),
        WorkflowStep("branch-a", "skill_a", True, ["root"]),
        WorkflowStep("branch-b", "skill_b", True, ["root"]),
    ]
    wf = _make_simple_workflow(steps)
    ordered = loader.get_steps_in_order(wf)
    ids = [s.id for s in ordered]
    assert ids[0] == "root"
    assert "branch-a" in ids
    assert "branch-b" in ids


def test_topological_order_single_step(loader):
    steps = [WorkflowStep("only", "skill_x", True, [])]
    wf = _make_simple_workflow(steps)
    ordered = loader.get_steps_in_order(wf)
    assert len(ordered) == 1
    assert ordered[0].id == "only"


def test_topological_order_raises_on_cycle(loader):
    steps = [
        WorkflowStep("step-a", "skill_a", True, ["step-b"]),
        WorkflowStep("step-b", "skill_b", True, ["step-a"]),
    ]
    wf = _make_simple_workflow(steps)
    with pytest.raises(ValueError, match="[Cc]irculaire"):
        loader.get_steps_in_order(wf)


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_order_pipeline_topo_order(loader, order_workflow):
    ordered = loader.get_steps_in_order(order_workflow)
    ids = [s.id for s in ordered]
    assert ids[0] == "validate-schema"
    assert "fraud-check" in ids
    assert "price-check" in ids


# ─────────────────────────────────────────────
# 4. validate()
# ─────────────────────────────────────────────

def test_validate_valid_workflow(loader):
    steps = [
        WorkflowStep("s1", "skill_one", True, []),
        WorkflowStep("s2", "skill_two", True, ["s1"]),
    ]
    wf = _make_simple_workflow(steps)
    ok, errors = loader.validate(wf)
    assert ok is True
    assert errors == []


def test_validate_detects_circular_dependency(loader):
    steps = [
        WorkflowStep("a", "skill_a", True, ["b"]),
        WorkflowStep("b", "skill_b", True, ["a"]),
    ]
    wf = _make_simple_workflow(steps)
    ok, errors = loader.validate(wf)
    assert ok is False
    assert any("circulaire" in e.lower() for e in errors)


def test_validate_detects_missing_depends_on_target(loader):
    steps = [
        WorkflowStep("s1", "skill_one", True, ["nonexistent"]),
    ]
    wf = _make_simple_workflow(steps)
    ok, errors = loader.validate(wf)
    assert ok is False
    assert any("nonexistent" in e for e in errors)


def test_validate_detects_empty_skill(loader):
    steps = [WorkflowStep("s1", "", True, [])]
    wf = _make_simple_workflow(steps)
    ok, errors = loader.validate(wf)
    assert ok is False
    assert any("skill" in e for e in errors)


def test_validate_detects_missing_name(loader):
    wf = WorkflowDefinition(
        name="",
        version="1.0",
        capability="cap",
        lane="deterministic",
        risk="low",
        audience="internal",
        inputs=[],
        outputs=[],
        steps=[WorkflowStep("s1", "skill_x")],
    )
    ok, errors = loader.validate(wf)
    assert ok is False
    assert any("name" in e for e in errors)


def test_validate_detects_empty_steps(loader):
    wf = _make_simple_workflow([])
    ok, errors = loader.validate(wf)
    assert ok is False
    assert any("stap" in e.lower() for e in errors)


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_validate_all_real_workflows_pass(loader):
    for name in loader.list_workflows():
        wf = loader.load(name)
        ok, errors = loader.validate(wf)
        assert ok is True, f"Workflow '{name}' failed: {errors}"


# ─────────────────────────────────────────────
# 5. get_required_steps()
# ─────────────────────────────────────────────

def test_get_required_steps_filters_optional():
    steps = [
        WorkflowStep("req", "skill_req", True, []),
        WorkflowStep("opt", "skill_opt", False, []),
    ]
    wf = _make_simple_workflow(steps)
    required = wf.get_required_steps()
    assert len(required) == 1
    assert required[0].id == "req"


def test_get_required_steps_all_required():
    steps = [
        WorkflowStep("s1", "skill_1", True, []),
        WorkflowStep("s2", "skill_2", True, []),
    ]
    wf = _make_simple_workflow(steps)
    assert len(wf.get_required_steps()) == 2


def test_get_required_steps_none_required():
    steps = [
        WorkflowStep("s1", "skill_1", False, []),
        WorkflowStep("s2", "skill_2", False, []),
    ]
    wf = _make_simple_workflow(steps)
    assert wf.get_required_steps() == []


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_order_pipeline_required_steps(order_workflow):
    required = order_workflow.get_required_steps()
    req_ids = [s.id for s in required]
    assert "validate-schema" in req_ids
    assert "fraud-check" in req_ids
    assert "price-check" not in req_ids


# ─────────────────────────────────────────────
# 6. get_chain()
# ─────────────────────────────────────────────

def test_get_chain_returns_correct_steps():
    wf = _make_simple_workflow(
        [WorkflowStep("s1", "skill_1")],
        chains={"on_high_risk": ["step-a", "step-b"]},
    )
    assert wf.get_chain("on_high_risk") == ["step-a", "step-b"]


def test_get_chain_unknown_trigger_returns_empty():
    wf = _make_simple_workflow([WorkflowStep("s1", "skill_1")])
    assert wf.get_chain("unknown_trigger") == []


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_order_pipeline_chain_on_high_risk(order_workflow):
    chain = order_workflow.get_chain("on_high_risk")
    assert "fraud-check" in chain
    assert len(chain) == 3


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML niet beschikbaar")
def test_fraud_pipeline_chain_on_high_risk(fraud_workflow):
    chain = fraud_workflow.get_chain("on_high_risk")
    assert "classify_payroll_risk" in chain
    assert "explain_salary_difference" in chain


# ─────────────────────────────────────────────
# 7. Graceful fallback zonder yaml
# ─────────────────────────────────────────────

def test_load_raises_import_error_without_yaml(tmp_path):
    """load() gooit ImportError als PyYAML niet beschikbaar is."""
    with patch("ollama.workflow_loader._YAML_AVAILABLE", False):
        loader = WorkflowLoader(workflows_dir=tmp_path)
        with pytest.raises(ImportError, match="[Pp]y[Yy][Aa][Mm][Ll]"):
            loader.load("anything")


def test_list_workflows_fallback_without_yaml(tmp_path):
    """list_workflows() geeft bestandsnamen terug zonder PyYAML."""
    (tmp_path / "my_workflow.yml").write_text("name: test\n")
    (tmp_path / "other.yml").write_text("name: other\n")
    with patch("ollama.workflow_loader._YAML_AVAILABLE", False):
        loader = WorkflowLoader(workflows_dir=tmp_path)
        names = loader.list_workflows()
    assert "my_workflow" in names
    assert "other" in names


# ─────────────────────────────────────────────
# 8. WorkflowStep defaults
# ─────────────────────────────────────────────

def test_workflow_step_defaults():
    step = WorkflowStep(id="test", skill="skill_test")
    assert step.required is True
    assert step.depends_on == []


def test_workflow_step_optional():
    step = WorkflowStep(id="opt", skill="skill_opt", required=False)
    assert step.required is False


def test_workflow_definition_chains_default():
    wf = WorkflowDefinition(
        name="x", version="1.0", capability="c", lane="l", risk="r",
        audience="a", inputs=[], outputs=[], steps=[],
    )
    assert wf.chains == {}
