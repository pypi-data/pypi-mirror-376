"""
Count-Min Sketch Python bindings

A high-performance implementation of the Count-Min Sketch probabilistic data structure.
"""


# start delvewheel patch
def _delvewheel_patch_1_11_1():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'cmsketch.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_1()
del _delvewheel_patch_1_11_1
# end delvewheel patch

from importlib.metadata import version

from cmsketch.base import (
    BaseCountMinSketch,
    BaseCountMinSketchStr,
    BaseCountMinSketchInt,
)
from cmsketch._core import (
    CountMinSketchStr,
    CountMinSketchInt,
)
from cmsketch.py.count_min_sketch import (
    PyCountMinSketchStr,
    PyCountMinSketchInt,
)


__version__ = version("cmsketch")

__all__ = [
    "BaseCountMinSketch",
    "BaseCountMinSketchStr",
    "BaseCountMinSketchInt",
    "CountMinSketchStr",
    "CountMinSketchInt",
    "PyCountMinSketchStr",
    "PyCountMinSketchInt",
]
