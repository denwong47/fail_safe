# -*- coding: utf-8 -*-
from fail_safe import config


def test_env():
    """
    Assert that the PYTEST flag is actually set.
    """
    assert config.env.PYTEST_IS_RUNNING
