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

""" Eager Operator Composition Container """

from typing import List, Union
from functools import reduce, partial
import numpy as np

from ..operator_base import OperatorBase
from .op_vec import OpVec


# pylint: disable=invalid-name

class OpComposition(OpVec):
    """ Eager Operator Composition Container """

    def __init__(self,
                 oplist: List[OperatorBase],
                 coeff: Union[int, float, complex] = 1.0,
                 abelian: bool = False) -> None:
        """
        Args:
            oplist: The operators being summed.
            coeff: A coefficient multiplying the operator
            abelian: indicates if abelian
        """
        super().__init__(oplist, combo_fn=partial(reduce, np.dot), coeff=coeff, abelian=abelian)

    @property
    def num_qubits(self) -> int:
        return self.oplist[0].num_qubits

    # TODO: Keep this property for evals or just enact distribution at composition time?
    @property
    def distributive(self) -> bool:
        """ Indicates whether the OpVec or subclass is distributive under composition.
        OpVec and OpSum are,
        meaning that opv @ op = opv[0] @ op + opv[1] @ op +...
        (plus for OpSum, vec for OpVec, etc.),
        while OpComposition and OpKron do not behave this way."""
        return False

    # TODO: need to kron all others with identity so dims are right? Maybe just delete this.
    # def kron(self, other):
    #     """ Kron. We only need to Kron to the last element in the composition. """
    #     return OpComposition(self.oplist[:-1] + [self.oplist[-1].kron(other)], coeff=self.coeff)

    # TODO take advantage of the mixed product property, kronpower each element in the composition
    # def kronpower(self, other):
    #     """ Kron with Self Multiple Times """
    #     raise NotImplementedError

    def adjoint(self) -> OperatorBase:
        return OpComposition([op.adjoint() for op in reversed(self.oplist)], coeff=self.coeff)

    def compose(self, other: OperatorBase) -> OperatorBase:
        """ Operator Composition (Circuit-style, left to right) """
        # Try composing with last element in list
        if isinstance(other, OpComposition):
            return OpComposition(self.oplist + other.oplist, coeff=self.coeff * other.coeff)

        # Try composing with last element of oplist. We only try
        # this if that last element isn't itself an
        # OpComposition, so we can tell whether composing the
        # two elements directly worked. If it doesn't,
        # continue to the final return statement below, appending other to the oplist.
        if not isinstance(self.oplist[-1], OpComposition):
            comp_with_last = self.oplist[-1].compose(other)
            # Attempt successful
            if not isinstance(comp_with_last, OpComposition):
                new_oplist = self.oplist[0:-1] + [comp_with_last]
                return OpComposition(new_oplist, coeff=self.coeff)

        return OpComposition(self.oplist + [other], coeff=self.coeff)

    def eval(self,
             front: Union[str, dict, np.ndarray,
                          OperatorBase] = None) -> Union[OperatorBase, float, complex]:
        """ A square binary Operator can be defined as a function over two
        binary strings of equal length. This
        method returns the value of that function for a given pair
        of binary strings. For more information,
        see the eval method in operator_base.py.
        """

        def tree_recursive_eval(r, l):
            # if isinstance(l, list):
            #     return [tree_recursive_eval(l_op, r) for l_op in l]
            if isinstance(r, list):
                return [tree_recursive_eval(r_op, l) for r_op in r]
            else:
                return l.eval(r)

        eval_list = self.oplist
        # Only one op needs to be multiplied, so just multiply the first.
        eval_list[0] = eval_list[0] * self.coeff
        eval_list = eval_list + [front] if front else eval_list

        return reduce(tree_recursive_eval, reversed(eval_list))

    # Try collapsing list or trees of compositions into a single <Measurement | Op | State>.
    def non_distributive_reduce(self) -> OperatorBase:
        """ non distributive reduce """
        reduced_ops = [op.reduce() for op in self.oplist]
        reduced_ops = reduce(lambda x, y: x.compose(y), reduced_ops) * self.coeff
        if isinstance(reduced_ops, OpComposition) and len(reduced_ops.oplist) > 1:
            return reduced_ops
        else:
            return reduced_ops[0]

    def reduce(self) -> OperatorBase:
        reduced_ops = [op.reduce() for op in self.oplist]

        def distribute_compose(l, r):
            if isinstance(l, OpVec) and l.distributive:
                # Either OpVec or OpSum, returns correct type
                return l.__class__([distribute_compose(l_op, r) for l_op in l.oplist])
            if isinstance(r, OpVec) and r.distributive:
                return r.__class__([distribute_compose(l, r_op) for r_op in r.oplist])
            else:
                return l.compose(r)

        reduced_ops = reduce(distribute_compose, reduced_ops) * self.coeff
        if isinstance(reduced_ops, OpVec) and len(reduced_ops.oplist) == 1:
            return reduced_ops.oplist[0]
        else:
            return reduced_ops
