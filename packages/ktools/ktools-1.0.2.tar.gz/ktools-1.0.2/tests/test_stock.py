#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2024 fx-kirin <fx.kirin@gmail.com>
#

import logging
import os

import kanilog
import pytest
import stdlogging
from add_parent_path import add_parent_path

with add_parent_path():
    from ktools import stock
    pass


def setup_module(module):
    pass


def teardown_module(module):
    pass


def setup_function(function):
    pass


def teardown_function(function):
    pass


def test_func():
    result = stock.get_ms_warrant_history("4588")
    assert len(result) >= 5


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    kanilog.setup_logger(logfile='/tmp/%s.log' % (os.path.basename(__file__)), level=logging.INFO)
    stdlogging.enable()

    pytest.main([__file__, '-k test_', '-s'])
