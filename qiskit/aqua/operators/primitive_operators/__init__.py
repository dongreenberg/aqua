# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Primitive Operators (:mod:`qiskit.aqua.operators.primitive_operators`)
======================================================================
Primitive operators...

.. currentmodule:: qiskit.aqua.operators.primitive_operators

Primitive Operators
===================

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

   CircuitOp
   MatrixOp
   PauliOp
   PrimitiveOp

"""

from .primitive_op import PrimitiveOp
from .pauli_op import PauliOp
from .matrix_op import MatrixOp
from .circuit_op import CircuitOp

__all__ = ['PrimitiveOp',
           'PauliOp',
           'MatrixOp',
           'CircuitOp']