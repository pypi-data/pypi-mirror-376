"""Tests for the main HyperSHAP module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
from ConfigSpace import Configuration

if TYPE_CHECKING:
    from shapiq import InteractionValues

from hypershap import ExplanationTask, HyperSHAP
from hypershap.hypershap import NoInteractionValuesError
from hypershap.task import BaselineExplanationTask
from hypershap.utils import Aggregation, RandomConfigSpaceSearcher

EPSILON = 0.2
EXPECTED_A = 0.7
EXPECTED_B = 2
EXPECTED_AB = 0


@pytest.fixture(scope="module")
def hypershap_inst(simple_base_et: ExplanationTask) -> HyperSHAP:
    """Return an instance of hypershap with a simple explanation task."""
    return HyperSHAP(simple_base_et)


@pytest.fixture(scope="module")
def tunability_iv(hypershap_inst: HyperSHAP) -> InteractionValues:
    """Return the interaction values for the tunability game."""
    return hypershap_inst.tunability(
        baseline_config=hypershap_inst.explanation_task.config_space.get_default_configuration(),
    )


def _assert_equals(expected: float, actual: float, message: str) -> None:
    assert abs(expected - actual) < EPSILON, message


def _assert_interaction_values(iv: InteractionValues) -> None:
    assert iv is not None, "Interaction values should not be none"
    _assert_equals(EXPECTED_A, iv.dict_values[(0,)], "Importance value for a should roughly be 0.7")
    _assert_equals(EXPECTED_B, iv.dict_values[(1,)], "Importance value for a should roughly be 2")
    _assert_equals(EXPECTED_AB, iv.dict_values[(0, 1)], "Importance value for a should roughly be 0")


def test_ablation(hypershap_inst: HyperSHAP, simple_base_et: ExplanationTask) -> None:
    """Test the ablation game."""
    hypershap_inst.last_interaction_values = None
    config_of_interest = Configuration(simple_base_et.config_space, vector=np.array([1.0, 1.0]))
    baseline_config = simple_base_et.config_space.get_default_configuration()
    iv = hypershap_inst.ablation(config_of_interest, baseline_config)
    _assert_interaction_values(iv)
    assert hypershap_inst.last_interaction_values is not None


def test_ablation_multibaseline(hypershap_inst: HyperSHAP, simple_base_et: ExplanationTask) -> None:
    """Test the ablation game."""
    hypershap_inst.last_interaction_values = None
    config_of_interest = Configuration(simple_base_et.config_space, vector=np.array([1.0, 1.0]))
    baseline_configs = simple_base_et.config_space.sample_configuration(3)
    iv = hypershap_inst.ablation_multibaseline(config_of_interest, baseline_configs)
    assert iv is not None, "Interaction values should not be none"
    assert hypershap_inst.last_interaction_values is not None


def test_tunability(hypershap_inst: HyperSHAP, simple_base_et: ExplanationTask) -> None:
    """Test the tunability game."""
    hypershap_inst.last_interaction_values = None
    baseline_config = simple_base_et.config_space.get_default_configuration()
    iv = hypershap_inst.tunability(baseline_config, n_samples=50_000)
    _assert_interaction_values(iv)
    assert hypershap_inst.last_interaction_values is not None


def test_tunability_wo_baseline(hypershap_inst: HyperSHAP) -> None:
    """Test the tunability game without providing a baseline."""
    hypershap_inst.last_interaction_values = None
    iv = hypershap_inst.tunability(n_samples=50_000)
    _assert_interaction_values(iv)
    assert hypershap_inst.last_interaction_values is not None


def test_mistunability(hypershap_inst: HyperSHAP, simple_base_et: ExplanationTask) -> None:
    """Test the mistunability game."""
    hypershap_inst.last_interaction_values = None
    baseline_config = Configuration(simple_base_et.config_space, vector=np.array([1.0, 1.0]))
    iv = hypershap_inst.mistunability(baseline_config, n_samples=50_000)
    _assert_equals(-1 * EXPECTED_A, iv.dict_values[(0,)], "Importance value for a should roughly be 0.7")
    _assert_equals(-1 * EXPECTED_B, iv.dict_values[(1,)], "Importance value for a should roughly be 2")
    _assert_equals(EXPECTED_AB, iv.dict_values[(0, 1)], "Importance value for a should roughly be 0")
    assert hypershap_inst.last_interaction_values is not None


def test_mistunability_wo_baseline(hypershap_inst: HyperSHAP) -> None:
    """Test the mistunability game without providing a baseline."""
    hypershap_inst.last_interaction_values = None
    iv = hypershap_inst.mistunability(n_samples=50_000)
    _assert_equals(0 * EXPECTED_A, iv.dict_values[(0,)], "Importance value for a should roughly be 0.7")
    _assert_equals(0 * EXPECTED_B, iv.dict_values[(1,)], "Importance value for a should roughly be 2")
    _assert_equals(EXPECTED_AB, iv.dict_values[(0, 1)], "Importance value for a should roughly be 0")
    assert hypershap_inst.last_interaction_values is not None


def test_sensitivity(hypershap_inst: HyperSHAP, simple_base_et: ExplanationTask) -> None:
    """Test the sensitivity game."""
    hypershap_inst.last_interaction_values = None
    baseline_config = Configuration(simple_base_et.config_space, vector=np.array([1.0, 1.0]))
    iv = hypershap_inst.sensitivity(baseline_config, n_samples=50_000)
    assert iv is not None, "Interaction values should not be none"
    assert iv.values.sum() > 0, "Variance should definitely be >0"
    assert hypershap_inst.last_interaction_values is not None


def test_sensitivity_wo_baseline(hypershap_inst: HyperSHAP) -> None:
    """Test the sensitivity game without providing a baseline."""
    hypershap_inst.last_interaction_values = None
    iv = hypershap_inst.sensitivity(n_samples=50_000)
    assert iv is not None, "Interaction values should not be none"
    assert iv.values.sum() > 0, "Variance should definitely be >0"
    assert hypershap_inst.last_interaction_values is not None


def test_optimizerbias(hypershap_inst: HyperSHAP, simple_base_et: ExplanationTask) -> None:
    """Test the optimizer bias explanation game."""
    hypershap_inst.last_interaction_values = None

    baseline_et = BaselineExplanationTask(
        simple_base_et.config_space,
        simple_base_et.surrogate_model,
        baseline_config=simple_base_et.config_space.get_default_configuration(),
    )

    opt_of_interest = RandomConfigSpaceSearcher(baseline_et, mode=Aggregation.MIN)
    ensemble = [RandomConfigSpaceSearcher(baseline_et)] * 3

    iv = hypershap_inst.optimizer_bias(opt_of_interest, ensemble)
    assert iv is not None, "Interaction values should not be none"
    _assert_equals(-1 * EXPECTED_A, iv.dict_values[(0,)], "Importance value for a should roughly be 0.7")
    _assert_equals(-1 * EXPECTED_B, iv.dict_values[(1,)], "Importance value for a should roughly be 2")
    _assert_equals(EXPECTED_AB, iv.dict_values[(0, 1)], "Importance value for a should roughly be 0")
    assert hypershap_inst.last_interaction_values is not None


def test_plot_si_plot(hypershap_inst: HyperSHAP, tunability_iv: InteractionValues) -> None:
    """Test to plot a Shapley Interaction graph."""
    filename = "test-sigraph.png"
    hypershap_inst.plot_si_graph(tunability_iv, save_path=filename, no_show=True)
    assert Path(filename).is_file(), "no output file was created"
    # tidy up
    Path(filename).unlink()


def test_plot_force_plot(hypershap_inst: HyperSHAP, tunability_iv: InteractionValues) -> None:
    """Test to plot a force plot."""
    filename = "test-force.png"
    hypershap_inst.plot_force(tunability_iv, save_path=filename, no_show=True)
    assert Path(filename).is_file(), "no output file was created"
    # tidy up
    Path(filename).unlink()


def test_plot_upset_plot(hypershap_inst: HyperSHAP, tunability_iv: InteractionValues) -> None:
    """Test to plot an upset plot."""
    filename = "test-upset.png"
    hypershap_inst.plot_upset(tunability_iv, save_path=filename, no_show=True)
    assert Path(filename).is_file(), "no output file was created"
    # tidy up
    Path(filename).unlink()


def test_plot_waterfall_plot(hypershap_inst: HyperSHAP, tunability_iv: InteractionValues) -> None:
    """Test to plot an upset plot."""
    filename = "test-waterfall.png"
    hypershap_inst.plot_waterfall(tunability_iv, save_path=filename, no_show=True)
    assert Path(filename).is_file(), "no output file was created"
    # tidy up
    Path(filename).unlink()


def test_plot_stacked_barchart(hypershap_inst: HyperSHAP, tunability_iv: InteractionValues) -> None:
    """Test to plot an upset plot."""
    filename = "test-stacked-bar.png"
    hypershap_inst.plot_stacked_bar(tunability_iv, save_path=filename, no_show=True)
    assert Path(filename).is_file(), "no output file was created"
    # tidy up
    Path(filename).unlink()


def test_no_interaction_values(hypershap_inst: HyperSHAP) -> None:
    """Test that an error is raised when no interaction values are provided."""
    hypershap_inst.last_interaction_values = None

    # check si graph plot
    exception_raise = False
    try:
        hypershap_inst.plot_si_graph(no_show=True)
    except NoInteractionValuesError:
        exception_raise = True
    assert exception_raise, "No interaction values error is expected to be raised"

    # check force plot
    exception_raise = False
    try:
        hypershap_inst.plot_force(no_show=True)
    except NoInteractionValuesError:
        exception_raise = True
    assert exception_raise, "No interaction values error is expected to be raised"

    # check force plot
    exception_raise = False
    try:
        hypershap_inst.plot_upset(no_show=True)
    except NoInteractionValuesError:
        exception_raise = True
    assert exception_raise, "No interaction values error is expected to be raised"

    # check waterfall plot
    exception_raise = False
    try:
        hypershap_inst.plot_waterfall(no_show=True)
    except NoInteractionValuesError:
        exception_raise = True
    assert exception_raise, "No interaction values error is expected to be raised"

    # check stacked barchart
    exception_raise = False
    try:
        hypershap_inst.plot_stacked_bar(no_show=True)
    except NoInteractionValuesError:
        exception_raise = True
    assert exception_raise, "No interaction values error is expected to be raised"


def test_parallel_evaluation(hypershap_inst: HyperSHAP) -> None:
    """Test the parallel evaluation of the value function."""
    hypershap_inst.n_workers = 2
    hypershap_inst.last_interaction_values = None
    iv = hypershap_inst.tunability(
        hypershap_inst.explanation_task.config_space.get_default_configuration(),
        n_samples=50_000,
    )
    _assert_interaction_values(iv)
    assert hypershap_inst.last_interaction_values is not None


def test_interaction_values_with_names(hypershap_inst: HyperSHAP, tunability_iv: InteractionValues) -> None:
    """Test the interaction values with names."""
    res_dict = hypershap_inst.get_interaction_values_with_names()
    assert res_dict is not None, "No interaction values were returned"

    res_dict2 = hypershap_inst.get_interaction_values_with_names(tunability_iv)
    assert res_dict2 is not None, "No interaction values were returned"

    hypershap_inst.last_interaction_values = None
    error_raised = False
    try:
        hypershap_inst.get_interaction_values_with_names()
    except TypeError:
        error_raised = True
    assert error_raised, "No interaction values should be present, so expecting an error to be raised."
