"""
Differentiation module for MacroStat

The macrostat.diff module consists of a series of classes that implement both
a numerical and autodiff approach to differentiation of a model's output.

The  module consists of the following classes

.. autosummary::
    :toctree: diff

    JacobianBase
    JacobianNumerical
    JacobianAutodiff
"""

from .jacobian_autodiff import JacobianAutodiff
from .jacobian_base import JacobianBase
from .jacobian_numerical import JacobianNumerical

__all__ = ["JacobianBase", "JacobianNumerical", "JacobianAutodiff"]
