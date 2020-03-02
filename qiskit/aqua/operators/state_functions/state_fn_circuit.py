# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" An Object to represent State Functions constructed from Operators """


import numpy as np
import itertools

from qiskit import QuantumCircuit, BasicAer, execute
from qiskit.circuit import Instruction

from qiskit.quantum_info import Statevector
from qiskit.aqua.operators import StateFn, OperatorBase, OpVec, OpSum


class StateFnCircuit(StateFn):
    """ A class for representing state functions and measurements.

    State functions are defined to be complex functions over a single binary string (as compared to an operator,
    which is defined as a function over two binary strings, or a function taking a binary function to another
    binary function). This function may be called by the eval() method.

    Measurements are defined to be functionals over StateFns, taking them to real values. Generally, this real value
    is interpreted to represent the probability of some classical state (binary string) being observed from a
    probabilistic or quantum system represented by a StateFn. This leads to the equivalent definition, which is that
    a measurement m is a function over binary strings producing StateFns, such that the probability of measuring
    a given binary string b from a system with StateFn f is equal to the inner product between f and m(b).

    NOTE: State functions here are not restricted to wave functions, as there is no requirement of normalization.
    """

    # TODO maybe break up into different classes for different fn definition primitives
    # TODO allow normalization somehow?
    def __init__(self, primitive, coeff=1.0, is_measurement=False):
        """
        Args:
            primitive(str, dict, OperatorBase, Result, np.ndarray, list)
            coeff(int, float, complex): A coefficient by which to multiply the state
        """
        if isinstance(primitive, QuantumCircuit):
            primitive = primitive.to_instruction()

        super().__init__(primitive, coeff=coeff, is_measurement=is_measurement)

    def get_primitives(self):
        """ Return a set of strings describing the primitives contained in the Operator """
        return {'Instruction'}

    @property
    def num_qubits(self):
        return self.primitive.num_qubits

    def add(self, other):
        """ Addition. Overloaded by + in OperatorBase. """
        if not self.num_qubits == other.num_qubits:
            raise ValueError('Sum over operators with different numbers of qubits, {} and {}, is not well '
                             'defined'.format(self.num_qubits, other.num_qubits))

        if isinstance(other, StateFnCircuit) and self.primitive == other.primitive:
            return StateFnCircuit(self.primitive, coeff=self.coeff + other.coeff)

        # Covers all else.
        return OpSum([self, other])

    def adjoint(self):
        return StateFnCircuit(self.primitive.inverse(),
                              coeff=np.conj(self.coeff),
                              is_measurement=(not self.is_measurement))

    def kron(self, other):
        """ Kron
        Note: You must be conscious of Qiskit's big-endian bit printing convention. Meaning, Plus.kron(Zero)
        produces a |+⟩ on qubit 0 and a |0⟩ on qubit 1, or |+⟩⨂|0⟩, but would produce a QuantumCircuit like
        |0⟩--
        |+⟩--
        Because Terra prints circuits and results with qubit 0 at the end of the string or circuit.
        """
        # TODO accept primitives directly in addition to OpPrimitive?

        if isinstance(other, StateFnCircuit):
            new_qc = QuantumCircuit(self.num_qubits + other.num_qubits)
            # NOTE!!! REVERSING QISKIT ENDIANNESS HERE
            new_qc.append(other.primitive, new_qc.qubits[0:other.primitive.num_qubits])
            new_qc.append(self.primitive, new_qc.qubits[other.primitive.num_qubits:])
            # TODO Fix because converting to dag just to append is nuts
            # TODO Figure out what to do with cbits?
            return StateFnCircuit(new_qc.decompose().to_instruction(), coeff=self.coeff * other.coeff)

        from qiskit.aqua.operators import OpKron
        return OpKron([self, other])

    def to_density_matrix(self, massive=False):
        """ Return numpy matrix of density operator, warn if more than 16 qubits to force the user to set
        massive=True if they want such a large matrix. Generally big methods like this should require the use of a
        converter, but in this case a convenience method for quick hacking and access to classical tools is
        appropriate. """

        if self.num_qubits > 16 and not massive:
            # TODO figure out sparse matrices?
            raise ValueError('to_matrix will return an exponentially large matrix, in this case {0}x{0} elements.'
                             ' Set massive=True if you want to proceed.'.format(2**self.num_qubits))

        # TODO handle list case
        # Rely on StateFnVectors logic here.
        return StateFn(self.primitive.to_matrix() * self.coeff).to_density_matrix()

    def to_matrix(self, massive=False):
        """
        NOTE: THIS DOES NOT RETURN A DENSITY MATRIX, IT RETURNS A CLASSICAL MATRIX CONTAINING THE QUANTUM OR CLASSICAL
        VECTOR REPRESENTING THE EVALUATION OF THE STATE FUNCTION ON EACH BINARY BASIS STATE. DO NOT ASSUME THIS IS
        IS A NORMALIZED QUANTUM OR CLASSICAL PROBABILITY VECTOR. If we allowed this to return a density matrix,
        then we would need to change the definition of composition to be ~Op @ StateFn @ Op for those cases,
        whereas by this methodology we can ensure that composition always means Op @ StateFn.

        Return numpy vector of state vector, warn if more than 16 qubits to force the user to set
        massive=True if they want such a large vector. Generally big methods like this should require the use of a
        converter, but in this case a convenience method for quick hacking and access to classical tools is
        appropriate. """

        if self.num_qubits > 16 and not massive:
            # TODO figure out sparse matrices?
            raise ValueError('to_vector will return an exponentially large vector, in this case {0} elements.'
                             ' Set massive=True if you want to proceed.'.format(2**self.num_qubits))

        qc = self.to_circuit(meas=False)
        statevector_backend = BasicAer.get_backend('statevector_simulator')
        statevector = execute(qc, statevector_backend, optimization_level=0).result().get_statevector()
        return statevector * self.coeff

    def __str__(self):
        """Overload str() """
        prim_str = str(self.primitive)
        if self.coeff == 1.0:
            return "{}({})".format('StateFunction' if not self.is_measurement else 'Measurement', prim_str)
        else:
            return "{}({}) * {}".format('StateFunction' if not self.is_measurement else 'Measurement',
                                        prim_str,
                                        self.coeff)

    def eval(self, other=None):
        # Validate bitstring: re.fullmatch(rf'[01]{{{0}}}', val1)

        if not self.is_measurement and isinstance(other, OperatorBase):
            raise ValueError('Cannot compute overlap with StateFn or Operator if not Measurement. Try taking '
                             'sf.adjoint() first to convert to measurement.')
        return StateFn(self.to_matrix(), is_measurement=True).eval(other)

    def to_circuit(self, meas=False):
        if meas:
            qc = QuantumCircuit(self.num_qubits, self.num_qubits)
            qc.append(self.primitive, qargs=range(self.primitive.num_qubits))
            qc.measure(qubit=range(self.num_qubits), cbit=range(self.num_qubits))
        else:
            qc = QuantumCircuit(self.num_qubits)
            qc.append(self.primitive, qargs=range(self.primitive.num_qubits))
        return qc

    # TODO
    def sample(self, shots):
        """ Sample the statefunction as a normalized probability distribution."""
        raise NotImplementedError