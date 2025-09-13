"""burla_io - small utility helpers.

Usage:
    from burla_io import cd, prepare_inputs
"""

from __future__ import annotations

import os
import itertools
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Mapping

__all__ = ["cd", "prepare_inputs", "__version__"]
__version__ = "0.1.0"


@contextmanager
def cd(path: str):
    """Temporarily change the working directory within a context.

    Example:
        with cd('/tmp'):
            ...
    """
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def prepare_inputs(params_to_test: Mapping[str, Iterable[Any]]) -> List[Dict[str, Any]]:
    """Create a list of param dictionaries from a cartesian product.

    Given a mapping of parameter names to iterables of values, returns a list
    of dictionaries representing the cartesian product of all combinations.
    """
    data: List[Dict[str, Any]] = []
    keys = list(params_to_test.keys())
    values = list(params_to_test.values())

    for combination in itertools.product(*values):
        param_dict = dict(zip(keys, combination))
        data.append(param_dict)
    return data

