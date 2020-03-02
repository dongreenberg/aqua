# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" Test Operator construction, including OpPrimitives and singletons. """

import unittest
import itertools
import numpy as np

from qiskit import QuantumCircuit, BasicAer, execute, ClassicalRegister
from qiskit.quantum_info import Statevector

from test.aqua import QiskitAquaTestCase
from qiskit.aqua.operators import StateFn, Zero, One, Plus, Minus, OpPrimitive, H, I, Z, X, Y


class TestStateOpMeasEvals(QiskitAquaTestCase):
    """Tests of evals of Meas-Operator-StateFn combos."""

    def test_statefn_overlaps(self):
        # wf = StateFn({'101010': .5, '111111': .3}) + (Zero^6)
        wf = (4 * StateFn({'101010': .5, '111111': .3})) + ((3 + .1j) * (Zero ^ 6))
        wf_vec = StateFn(wf.to_matrix())
        self.assertAlmostEqual(wf.adjoint().eval(wf), 14.45)
        self.assertAlmostEqual(wf_vec.adjoint().eval(wf_vec), 14.45)
        self.assertAlmostEqual(wf_vec.adjoint().eval(wf), 14.45)
        self.assertAlmostEqual(wf.adjoint().eval(wf_vec), 14.45)

    def test_wf_evals_x(self):
        qbts = 4
        wf = ((Zero^qbts) + (One^qbts))*(1/2**.5)
        # Note: wf = Plus^qbts fails because OpKron can't handle it.
        wf_vec = StateFn(wf.to_matrix())
        op = X^qbts
        # op = I^6
        self.assertAlmostEqual(op.eval(front=wf, back=wf.adjoint()), 1)
        self.assertAlmostEqual(op.eval(front=wf, back=wf_vec.adjoint()), 1)
        self.assertAlmostEqual(op.eval(front=wf_vec, back=wf.adjoint()), 1)
        self.assertAlmostEqual(op.eval(front=wf_vec, back=wf_vec.adjoint()), 1)
        self.assertAlmostEqual(wf.adjoint().eval(op.eval(wf)), 1)
        self.assertAlmostEqual(wf_vec.adjoint().eval(op.eval(wf)), 1)
        self.assertAlmostEqual(wf.adjoint().eval(op.eval(wf_vec)), 1)
        self.assertAlmostEqual(wf_vec.adjoint().eval(op.eval(wf_vec)), 1)

        # op = (H^X^Y)^2
        op = H^6
        wf = ((Zero^6) + (One^6))*(1/2**.5)
        wf_vec = StateFn(wf.to_matrix())
        # print(wf.adjoint().to_matrix() @ op.to_matrix() @ wf.to_matrix())
        self.assertAlmostEqual(op.eval(front=wf, back=wf.adjoint()), .25)
        self.assertAlmostEqual(op.eval(front=wf, back=wf_vec.adjoint()), .25)
        self.assertAlmostEqual(op.eval(front=wf_vec, back=wf.adjoint()), .25)
        self.assertAlmostEqual(op.eval(front=wf_vec, back=wf_vec.adjoint()), .25)
        self.assertAlmostEqual(wf.adjoint().eval(op.eval(wf)), .25)
        self.assertAlmostEqual(wf_vec.adjoint().eval(op.eval(wf)), .25)
        self.assertAlmostEqual(wf.adjoint().eval(op.eval(wf_vec)), .25)
        self.assertAlmostEqual(wf_vec.adjoint().eval(op.eval(wf_vec)), .25)