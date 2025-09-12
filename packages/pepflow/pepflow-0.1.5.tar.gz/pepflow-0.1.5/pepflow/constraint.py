# Copyright: 2025 The PEPFlow Developers
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from pepflow.point import Scalar

from pepflow import utils


@attrs.frozen
class Constraint:
    """A :class:`Constraint` object that represents inequalities and
    equalities of :class:`Scalar` objects.

    Denote an arbitrary :class:`Scalar` object as `x`. Constraints represent:
    `x <= 0`, `x >= 0`, and `x = 0`.

    Attributes:
        scalar (:class:`Scalar`): The :class:`Scalar` object involved in
            the inequality or equality.
        comparator (:class:`Comparator`): :class:`Comparator` is an enumeration
            that can be either `GT`, `LT`, or `EQ`. They represent `>=`, `<=`,
            and `=` respectively.
        name (str): The unique name of the :class:`Comparator` object.
        associated_dual_var_constraints (list[tuple[utils.Comparator, float]]):
            A list of all the constraints imposed on the associated dual
            variable of this :class:`Constraint` object.
    """

    scalar: Scalar | float
    comparator: utils.Comparator
    name: str

    # Used to represent the constraint on primal variable in dual PEP.
    associated_dual_var_constraints: list[tuple[utils.Comparator, float]] = attrs.field(
        factory=list
    )

    def dual_lt(self, val: float) -> None:
        """
        Denote the associated dual variable of this constraint as `lambd`.
        This generates a relation of the form `lambd <= val`.

        Args:
            val (float): The other object in the relation.
        """
        if not utils.is_numerical(val):
            raise ValueError(f"The input {val=} must be a numerical value")
        self.associated_dual_var_constraints.append((utils.Comparator.LT, val))

    def dual_gt(self, val: float) -> None:
        """
        Denote the associated dual variable of this constraint as `lambd`.
        This generates a relation of the form `lambd >= val`.

        Args:
            val (float): The other object in the relation.
        """
        if not utils.is_numerical(val):
            raise ValueError(f"The input {val=} must be a numerical value")
        self.associated_dual_var_constraints.append((utils.Comparator.GT, val))

    def dual_eq(self, val: float) -> None:
        """
        Denote the associated dual variable of this constraint as `lambd`.
        This generates a relation of the form `lambd = val`.

        Args:
            val (float): The other object in the relation.
        """
        if not utils.is_numerical(val):
            raise ValueError(f"The input {val=} must be a numerical value")
        self.associated_dual_var_constraint.append((utils.Comparator.EQ, val))
