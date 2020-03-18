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

""" Eager Operator Kron Container """

from typing import List, Union
from functools import reduce, partial
import numpy as np

from ..operator_base import OperatorBase
from .op_vec import OpVec


class OpKron(OpVec):
    """ Eager Operator Kron Container """
    def __init__(self,
                 oplist: List[OperatorBase],
                 coeff: Union[int, float, complex] = 1.0,
                 abelian: bool = False) -> None:
        """
        Args:
            oplist: The operators being summed.
            coeff: A coefficient multiplying the primitive
            abelian: indicates if abelian
        """
        super().__init__(oplist, combo_fn=partial(reduce, np.kron), coeff=coeff, abelian=abelian)

    @property
    def num_qubits(self):
        return sum([op.num_qubits for op in self.oplist])

    # TODO: Keep this property for evals or just enact distribution at composition time?
    @property
    def distributive(self):
        """ Indicates whether the OpVec or subclass is distributive under
        composition. OpVec and OpSum are,
        meaning that opv @ op = opv[0] @ op + opv[1] @ op +...
        (plus for OpSum, vec for OpVec, etc.),
        while OpComposition and OpKron do not behave this way."""
        return False

    def kron(self, other):
        """ Kron """
        if isinstance(other, OpKron):
            return OpKron(self.oplist + other.oplist, coeff=self.coeff * other.coeff)
        return OpKron(self.oplist + [other], coeff=self.coeff)

    # TODO Kron eval should partial trace the input into smaller StateFns each of size
    #  op.num_qubits for each op in oplist. Right now just works through matmul like OpComposition.
    def eval(self, front=None, back=None):
        """ A square binary Operator can be defined as a function over two binary strings of
        equal length. This
        method returns the value of that function for a given pair of binary strings.
        For more information,
        see the eval method in operator_base.py.
        """

        # pylint: disable=cyclic-import,import-outside-toplevel
        from ..operator_primitives import OpPrimitive
        kron_mat_op = OpPrimitive(self.combo_fn([op.to_matrix() for op in self.oplist]),
                                  coeff=self.coeff)
        return kron_mat_op.eval(front=front, back=back)

    # Try collapsing list or trees of krons.
    # TODO do this smarter
    def reduce(self):
        reduced_ops = [op.reduce() for op in self.oplist]
        reduced_ops = reduce(lambda x, y: x.kron(y), reduced_ops) * self.coeff
        if isinstance(reduced_ops, OpVec) and len(reduced_ops.oplist) == 1:
            return reduced_ops.oplist[0]
        else:
            return reduced_ops
