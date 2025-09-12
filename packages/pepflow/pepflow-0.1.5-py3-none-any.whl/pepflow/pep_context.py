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

from collections import defaultdict
from typing import TYPE_CHECKING

import natsort
import pandas as pd

if TYPE_CHECKING:
    from pepflow.function import Function, Triplet
    from pepflow.point import Point
    from pepflow.scalar import Scalar

# A global variable for storing the current context that is used for points or scalars.
CURRENT_CONTEXT: PEPContext | None = None
# Keep the track of all previous created context
GLOBAL_CONTEXT_DICT: dict[str, PEPContext] = {}


def get_current_context() -> PEPContext | None:
    """
    Return the current global :class:`PEPContext`.

    Returns:
        :class:`PEPContext`: The current global :class:`PEPContext`.
    """
    return CURRENT_CONTEXT


def set_current_context(ctx: PEPContext | None):
    """
    Change the current global :class:`PEPContext`.

    Args:
        ctx (:class:`PEPContext`): The :class:`PEPContext` to set as the new
            global :class:`PEPContext`.
    """
    global CURRENT_CONTEXT
    assert ctx is None or isinstance(ctx, PEPContext)
    CURRENT_CONTEXT = ctx


class PEPContext:
    """
    A :class:`PEPContext` object is a context manager which maintains
    the abstract mathematical objects of the Primal and Dual PEP.

    Attributes:
        name (str): The unique name of the :class:`PEPContext` object.
    """

    def __init__(self, name: str):
        self.name = name
        self.points: list[Point] = []
        self.scalars: list[Scalar] = []
        self.triplets: dict[Function, list[Triplet]] = defaultdict(list)
        # self.triplets will contain all stationary_triplets. They are not mutually exclusive.
        self.stationary_triplets: dict[Function, list[Triplet]] = defaultdict(list)

        GLOBAL_CONTEXT_DICT[name] = self

    def set_as_current(self) -> PEPContext:
        """
        Set this :class:`PEPContext` object as the global context.

        Returns:
            :class:`PEPContext`: This :class:`PEPContext` object.
        """
        set_current_context(self)
        return self

    def add_point(self, point: Point):
        self.points.append(point)

    def add_scalar(self, scalar: Scalar):
        self.scalars.append(scalar)

    def add_triplet(self, function: Function, triplet: Triplet):
        self.triplets[function].append(triplet)

    def add_stationary_triplet(self, function: Function, stationary_triplet: Triplet):
        self.stationary_triplets[function].append(stationary_triplet)

    def get_by_tag(self, tag: str) -> Point | Scalar:
        """
        Under this :class:`PEPContext`, get the :class:`Point` or
        :class:`Scalar` object associated with the provided `tag`.

        Args:
            tag (str): The tag of the :class:`Point` or :class:`Scalar` object
                we want to retrieve.

        Returns:
            :class:`Point` | :class:`Scalar`: The :class:`Point` or
            :class:`Scalar` object associated with the provided `tag`.
        """
        for p in self.points:
            if tag in p.tags:
                return p
        for s in self.scalars:
            if tag in s.tags:
                return s
        raise ValueError("Cannot find the point, scalar, or function of given tag.")

    def clear(self):
        """Reset this :class:`PEPContext` object."""
        self.points.clear()
        self.scalars.clear()
        self.triplets.clear()
        self.stationary_triplets.clear()

    def tracked_point(self, func: Function) -> list[Point]:
        """
        Each function :math:`f` used in Primal and Dual PEP is associated with
        a set of triplets :math:`\\{x_i, f(x_i), \\nabla f(x_i)\\}` visited by
        the considered algorithm. We can also consider a subgradient
        :math:`\\widetilde{\\nabla} f(x)` instead of the gradient. This
        function returns a list of the visited points :math:`\\{x_i\\}` under
        this :class:`PEPContext`.

        Args:
            func (:class:`Function`): The function associated with the set
                of triplets :math:`\\{x_i, f(x_i), \\nabla f(x_i)\\}`.

        Returns:
            list[:class:`Point`]: The list of the visited points
            :math:`\\{x_i\\}`.
        """
        return natsort.natsorted(
            [t.point for t in self.triplets[func]], key=lambda x: x.tag
        )

    def tracked_grad(self, func: Function) -> list[Point]:
        """
        Each function :math:`f` used in Primal and Dual PEP is associated with
        a set of triplets :math:`\\{x_i, f(x_i), \\nabla f(x_i)\\}` visited by
        the considered algorithm. We can also consider a subgradient
        :math:`\\widetilde{\\nabla} f(x)` instead of the gradient
        :math:`\\nabla f(x_i)`. This function returns a list of the visited
        gradients :math:`\\{\\nabla f(x_i)\\}` under this :class:`PEPContext`.

        Args:
            func (:class:`Function`): The function associated with the set
                of triplets :math:`\\{x_i, f(x_i), \\nabla f(x_i)\\}`.

        Returns:
            list[:class:`Point`]: The list of the visited gradients
            :math:`\\{\\nabla f(x_i)\\}`.

        """
        return natsort.natsorted(
            [t.gradient for t in self.triplets[func]], key=lambda x: x.tag
        )

    def tracked_func_value(self, func: Function) -> list[Scalar]:
        """
        Each function :math:`f` used in Primal and Dual PEP is associated with
        a set of triplets :math:`\\{x_i, f(x_i), \\nabla f(x_i)\\}` visited by
        the considered algorithm. We can also consider a subgradient
        :math:`\\widetilde{\\nabla} f(x)` instead of the gradient
        :math:`\\nabla f(x_i)`. This function returns a list of the visited
        function values :math:`\\{f(x_i)\\}` under this :class:`PEPContext`.

        Args:
            func (:class:`Function`): The function associated with the set of
                triplets :math:`\\{x_i, f(x_i), \\nabla f(x_i)\\}`.

        Returns:
            list[:class:`Scalar`]: The list of the visited function values
            :math:`\\{f(x_i)\\}`.

        """
        return natsort.natsorted(
            [t.function_value for t in self.triplets[func]], key=lambda x: x.tag
        )

    def order_of_point(self, func: Function) -> list[str]:
        return natsort.natsorted([t.point.tag for t in self.triplets[func]])

    def triplets_to_df_and_order(
        self,
    ) -> tuple[dict[Function, pd.DataFrame], dict[Function, list[str]]]:
        func_to_df: dict[Function, pd.DataFrame] = {}
        func_to_order: dict[Function, list[str]] = {}

        def name_to_point_tuple(c_name: str) -> list[str]:
            _, points = c_name.split(":")
            return points.split(",")

        for func, triplets in self.triplets.items():
            order = self.order_of_point(func)
            df = pd.DataFrame(
                [
                    (
                        constraint.name,
                        *name_to_point_tuple(constraint.name),
                    )
                    for constraint in func.get_interpolation_constraints(self)
                ],
                columns=["constraint_name", "col_point", "row_point"],
            )
            df["row"] = df["row_point"].map(lambda x: order.index(x))
            df["col"] = df["col_point"].map(lambda x: order.index(x))
            func_to_df[func] = df
            func_to_order[func] = order

        return func_to_df, func_to_order

    def basis_points(self) -> list[Point]:
        """
        Return a list of the basis :class:`Point` objects managed by this
        :class:`PEPContext`.

        Returns:
            list[:class:`Point`]: A list of the basis :class:`Point` objects
            managed by this :class:`PEPContext`.
        """
        return [
            p for p in self.points if p.is_basis
        ]  # Note the order is always the same as added time

    def basis_scalars(self) -> list[Scalar]:
        """
        Return a list of the basis :class:`Scalar` objects managed by this
        :class:`PEPContext`.

        Returns:
            list[:class:`Scalar`]: A list of the basis :class:`Scalar` objects
            managed by this :class:`PEPContext`.
        """
        return [
            s for s in self.scalars if s.is_basis
        ]  # Note the order is always the same as added time
