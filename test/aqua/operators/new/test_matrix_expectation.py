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

" Test MatrixExpectation"

from test.aqua import QiskitAquaTestCase

import numpy as np
import itertools

from qiskit.aqua.operators import X, Y, Z, I, CX, T, H, S, OpPrimitive, OpSum, OpComposition, OpVec
from qiskit.aqua.operators import StateFn, Zero, One, Plus, Minus

from qiskit.aqua.operators.expectation_values import ExpectationBase, MatrixExpectation
from qiskit import BasicAer


class TestMatrixExpectation(QiskitAquaTestCase):
    """Pauli Change of Basis Expectation tests."""

    def test_matrix_expect_pair(self):
        op = (Z ^ Z)
        expect = MatrixExpectation(operator=op)
        # wf = (Pl^Pl) + (Ze^Ze)
        wf = CX @ (H^I) @ Zero
        mean = expect.compute_expectation(wf)
        self.assertAlmostEqual(mean, 0)

    def test_matrix_expect_single(self):
        paulis = [Z, X, Y, I]
        states = [Zero, One, Plus, Minus, S@Plus, S@Minus]
        for pauli, state in itertools.product(paulis, states):
            expect = MatrixExpectation(operator=pauli)
            mean = expect.compute_expectation(state)
            matmulmean = state.adjoint().to_matrix() @ pauli.to_matrix() @ state.to_matrix()
            # print('{}, {}'.format(pauli.primitive, np.round(float(matmulmean[0]), decimals=3)))
            np.testing.assert_array_almost_equal(mean, matmulmean)

    def test_matrix_expect_op_vector(self):
        paulis_op = OpVec([X, Y, Z, I])

        expect = MatrixExpectation(operator=paulis_op)
        plus_mean = expect.compute_expectation(Plus)
        np.testing.assert_array_almost_equal(plus_mean, [1, 0, 0, 1])

        minus_mean = expect.compute_expectation(Minus)
        np.testing.assert_array_almost_equal(minus_mean, [-1, 0, 0, 1])

        zero_mean = expect.compute_expectation(Zero)
        np.testing.assert_array_almost_equal(zero_mean, [0, 0, 1, 1])

        sum_plus = (Zero + One) * (.5 ** .5)
        sum_plus_mean = expect.compute_expectation(sum_plus)
        np.testing.assert_array_almost_equal(sum_plus_mean, [1, 0, 0, 1])

        sum_zero = (Plus + Minus)*(.5**.5)
        print(np.around(sum_zero.adjoint().to_matrix() @
                        ((Z.to_matrix() @ Plus.to_matrix()) + (Z.to_matrix() @ One.to_matrix()))))
        print(np.around(sum_zero.adjoint().to_matrix() @ Z.to_matrix() @ sum_zero.to_matrix()))
        print(np.around(Zero.adjoint().to_matrix() @ Z.to_matrix() @ Zero.to_matrix()))
        sum_zero_mean = expect.compute_expectation(sum_zero)
        np.testing.assert_array_almost_equal(sum_zero_mean, [0, 0, 1, 1])

        for i, op in enumerate(paulis_op.oplist):
            # print(op)
            mat_op = op.to_matrix()
            np.testing.assert_array_almost_equal(plus_mean[i],
                                                 Plus.adjoint().to_matrix() @ mat_op @ Plus.to_matrix())
            np.testing.assert_array_almost_equal(minus_mean[i],
                                                 Minus.adjoint().to_matrix() @ mat_op @ Minus.to_matrix())
            np.testing.assert_array_almost_equal(sum_zero_mean[i],
                                                 sum_zero.adjoint().to_matrix() @ mat_op @ sum_zero.to_matrix())

    def test_matrix_expect_state_vector(self):
        states_op = OpVec([One, Zero, Plus, Minus])

        paulis_op = X
        expect = MatrixExpectation(operator=paulis_op)
        means = expect.compute_expectation(states_op)
        np.testing.assert_array_almost_equal(means, [0, 0, 1, -1])

    def test_matrix_expect_op_vector_state_vector(self):
        paulis_op = OpVec([X, Y, Z, I])
        states_op = OpVec([One, Zero, Plus, Minus])

        expect = MatrixExpectation(operator=paulis_op)
        means = expect.compute_expectation(states_op)
        valids = [[+0, 0, 1, -1],
                  [+0, 0, 0,  0],
                  [-1, 1, 0, -0],
                  [+1, 1, 1,  1]]
        np.testing.assert_array_almost_equal(means, valids)