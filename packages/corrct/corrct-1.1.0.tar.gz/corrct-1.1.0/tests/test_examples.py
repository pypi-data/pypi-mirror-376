#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the examples.

@author: Nicola VIGANÒ, Computational Imaging group, CWI, The Netherlands,
and ESRF - The European Synchrotron, Grenoble, France
"""

import glob
import importlib
import os

import matplotlib.pyplot as plt
import pytest

examples_list = glob.glob(os.path.join("examples", "example_*"))


@pytest.mark.parametrize("example_file", examples_list)
def test_import(example_file: str):
    module_name = "examples." + os.path.split(example_file)[-1][:-3]
    print(f"\nTesting: {example_file}: {module_name}\n")
    importlib.import_module(module_name)
    plt.close("all")
