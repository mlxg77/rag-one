"""实验编排命令的离线参数校验。"""

import argparse

import pytest

from scripts.run_chunk_experiments import parse_configs


def test_parse_chunk_experiment_configs():
    assert parse_configs("600/150, 800/80") == [(600, 150), (800, 80)]


@pytest.mark.parametrize("value", ["", "800", "100/100", "0/0", "x/y"])
def test_invalid_chunk_experiment_configs_are_rejected(value):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_configs(value)
