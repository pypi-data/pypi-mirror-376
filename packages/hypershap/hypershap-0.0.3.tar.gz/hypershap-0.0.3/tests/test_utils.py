"""Tests for the utils module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from ConfigSpace import UniformFloatHyperparameter

if TYPE_CHECKING:
    from hypershap import ExplanationTask
    from tests.fixtures.simple_setup import SimpleBlackboxFunction

from hypershap.task import BaselineExplanationTask
from hypershap.utils import Aggregation, RandomConfigSpaceSearcher, evaluate_aggregation

DEFAULT_MODE = Aggregation.MAX
N_SAMPLES = 50_000
EPSILON = 0.2

AGG_LIST = [0.1, 0.2, 0.6]


@pytest.fixture(scope="module")
def random_cs(simple_base_et: ExplanationTask) -> RandomConfigSpaceSearcher:
    """Fixture for creating a random config space searcher."""
    baseline_et = BaselineExplanationTask(
        simple_base_et.config_space,
        simple_base_et.surrogate_model,
        baseline_config=simple_base_et.config_space.get_default_configuration(),
    )

    return RandomConfigSpaceSearcher(
        explanation_task=baseline_et,
        mode=DEFAULT_MODE,
        n_samples=N_SAMPLES,
    )


def test_n_samples(random_cs: RandomConfigSpaceSearcher) -> None:
    """Test whether random config space searcher draws the given number of samples."""
    assert random_cs.random_sample.shape[0] == N_SAMPLES, (
        "Number of samples should be the same as the number of samples in the explanation task."
    )


def test_empty_coalition_search(random_cs: RandomConfigSpaceSearcher) -> None:
    """Test random config space searcher for an empty coalition."""
    et = random_cs.explanation_task
    res = random_cs.search(np.array([False] * random_cs.explanation_task.get_num_hyperparameters()))
    assert res == et.surrogate_model.evaluate_config(et.config_space.get_default_configuration()), (
        "If no hyperparameter is activated for searching, the resulting max performance should be equal to default performance."
    )


def test_grand_coalition_max_search(
    random_cs: RandomConfigSpaceSearcher,
    simple_blackbox_function: SimpleBlackboxFunction,
) -> None:
    """Test random config space searcher for max aggregation."""
    et = random_cs.explanation_task
    res = random_cs.search(np.array([True] * random_cs.explanation_task.get_num_hyperparameters()))

    if isinstance(et.config_space["a"], UniformFloatHyperparameter) and isinstance(
        et.config_space["b"],
        UniformFloatHyperparameter,
    ):
        a: UniformFloatHyperparameter = et.config_space["a"]
        b: UniformFloatHyperparameter = et.config_space["b"]
        a_upper = a.upper
        b_upper = b.upper
        max_value = simple_blackbox_function.value(a_upper, b_upper)
    else:
        raise TypeError

    assert abs(max_value - res < EPSILON), "The max performance should be equal to the upper boundaries value."


def test_grand_coalition_min_search(
    random_cs: RandomConfigSpaceSearcher,
    simple_blackbox_function: SimpleBlackboxFunction,
) -> None:
    """Test random config space searcher for min aggregation."""
    et = random_cs.explanation_task
    random_cs.mode = Aggregation.MIN
    res = random_cs.search(np.array([True] * random_cs.explanation_task.get_num_hyperparameters()))

    if isinstance(et.config_space["a"], UniformFloatHyperparameter) and isinstance(
        et.config_space["b"],
        UniformFloatHyperparameter,
    ):
        a: UniformFloatHyperparameter = et.config_space["a"]
        b: UniformFloatHyperparameter = et.config_space["b"]
        a_lower = a.lower
        b_lower = b.lower
        min_value = simple_blackbox_function.value(a_lower, b_lower)
    else:
        raise TypeError

    assert abs(res - min_value < EPSILON), "The min performance should be equal to the lower boundaries value."


def test_grand_coalition_avg_search(
    random_cs: RandomConfigSpaceSearcher,
    simple_blackbox_function: SimpleBlackboxFunction,
) -> None:
    """Test random config space searcher for avg aggregation."""
    et = random_cs.explanation_task
    random_cs.mode = Aggregation.AVG
    res = random_cs.search(np.array([True] * random_cs.explanation_task.get_num_hyperparameters()))

    avg_value = 0
    if isinstance(et.config_space["a"], UniformFloatHyperparameter) and isinstance(
        et.config_space["b"],
        UniformFloatHyperparameter,
    ):
        a: UniformFloatHyperparameter = et.config_space["a"]
        b: UniformFloatHyperparameter = et.config_space["b"]
        a_middle = a.lower + (a.upper - a.lower) / 2
        b_middle = b.lower + (b.upper - b.lower) / 2
        avg_value = simple_blackbox_function.value(a_middle, b_middle)

    assert abs(res - avg_value < EPSILON), "The avg aggregation should be equal to the middle performance."


def test_baseline_coalition_var_search(
    random_cs: RandomConfigSpaceSearcher,
) -> None:
    """Test random config space searcher for avg aggregation."""
    random_cs.mode = Aggregation.VAR
    res = random_cs.search(np.array([False] * random_cs.explanation_task.get_num_hyperparameters()))
    expected_var = 0
    assert abs(res - expected_var < EPSILON), (
        "If no hyperparameter is activated for searching, the variance should be 0."
    )


def test_evaluate_aggregation() -> None:
    """Test the evaluation of aggregation function."""
    vals = np.array(AGG_LIST)

    assert evaluate_aggregation(Aggregation.MIN, vals) == AGG_LIST[0]
    assert evaluate_aggregation(Aggregation.MAX, vals) == AGG_LIST[2]
    assert evaluate_aggregation(Aggregation.AVG, vals) == np.array(AGG_LIST).mean()
    assert abs(evaluate_aggregation(Aggregation.VAR, vals) - np.array(AGG_LIST).var()) < EPSILON
