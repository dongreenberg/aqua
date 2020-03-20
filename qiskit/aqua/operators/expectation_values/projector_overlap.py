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

""" Expectation Algorithm Base """

import logging

from .expectation_base import ExpectationBase

logger = logging.getLogger(__name__)


class ProjectorOverlap(ExpectationBase):
    """ A base for Expectation Value algorithms """

    def __init__(self, state=None, operator=None, backend=None):
        """
        Args:

        """
        super().__init__()
        self._operator = operator
        self._state = state
        self.backend = backend

    def compute_expectation(self, state=None, params=None):
        """ compute expectation """
        raise NotImplementedError

    def compute_standard_deviation(self, state=None, params=None):
        """ compute standard deviation """
        raise NotImplementedError