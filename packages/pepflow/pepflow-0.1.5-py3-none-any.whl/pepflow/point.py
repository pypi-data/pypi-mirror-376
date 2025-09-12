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

import uuid
from typing import Any

import attrs
import numpy as np

from pepflow import pep_context as pc
from pepflow import utils
from pepflow.scalar import Scalar, ScalarRepresentation


def is_numerical_or_point(val: Any) -> bool:
    return utils.is_numerical_or_parameter(val) or isinstance(val, Point)


def is_numerical_or_evaluatedpoint(val: Any) -> bool:
    return utils.is_numerical_or_parameter(val) or isinstance(val, EvaluatedPoint)


@attrs.frozen
class PointRepresentation:
    op: utils.Op
    left_point: Point | float
    right_point: Point | float


@attrs.frozen
class ZeroPoint:
    """A special class to represent 0 in Point."""

    pass


@attrs.frozen
class EvaluatedPoint:
    """
    The concrete representation of the abstract :class:`Point`.

    Each abstract basis :class:`Point` object has a unique concrete
    representation as a unit vector. The concrete representations of
    linear combinations of abstract basis :class:`Point` objects are
    linear combinations of the unit vectors. This information is stored
    in the `vector` attribute.

    :class:`EvaluatedPoint` objects can be constructed as linear combinations
    of other :class:`EvaluatedPoint` objects. Let `a` and `b` be some numeric
    data type. Let `x` and `y` be :class:`EvaluatedPoint` objects. Then, we
    can form a new :class:`EvaluatedPoint` object: `a*x+b*y`.

    Attributes:
        vector (np.ndarray): The concrete representation of an
            abstract :class:`Point`.
    """

    vector: np.ndarray

    @classmethod
    def zero(cls, num_basis_points: int):
        return EvaluatedPoint(vector=np.zeros(num_basis_points))

    def __add__(self, other):
        if isinstance(other, EvaluatedPoint):
            return EvaluatedPoint(vector=self.vector + other.vector)
        elif utils.is_numerical(other):
            return EvaluatedPoint(vector=self.vector + other)
        else:
            return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, EvaluatedPoint):
            return EvaluatedPoint(vector=self.vector - other.vector)
        elif utils.is_numerical(other):
            return EvaluatedPoint(vector=self.vector - other)
        else:
            return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, EvaluatedPoint):
            return EvaluatedPoint(vector=other.vector - self.vector)
        elif utils.is_numerical(other):
            return EvaluatedPoint(vector=other - self.vector)
        else:
            return NotImplemented

    def __mul__(self, other):
        if not utils.is_numerical(other):
            return NotImplemented
        return EvaluatedPoint(vector=self.vector * other)

    def __rmul__(self, other):
        if not utils.is_numerical(other):
            return NotImplemented
        return EvaluatedPoint(vector=other * self.vector)

    def __truediv__(self, other):
        if not utils.is_numerical(other):
            return NotImplemented
        return EvaluatedPoint(vector=self.vector / other)


@attrs.frozen
class Point:
    """
    A :class:`Point` object represents an element of a pre-Hilbert space.
    Examples include a point or a gradient.

    :class:`Point` objects can be constructed as linear combinations of
    other :class:`Point` objects. Let `a` and `b` be some numeric data type.
    Let `x` and `y` be :class:`Point` objects. Then, we can form a new
    :class:`Point` object: `a*x+b*y`.

    The inner product of two :class:`Point` objects can also be taken.
    Let `x` and `y` be :class:`Point` objects. Then, their inner product is
    `x*y` and returns a :class:`Scalar` object.

    Attributes:
        is_basis (bool): `True` if this point is not formed through a linear
            combination of other points. `False` otherwise.
        tags (list[str]): A list that contains tags that can be used to
            identify the :class:`Point` object. Tags should be unique.
    """

    # If true, the point is the basis for the evaluations of G
    is_basis: bool

    # The representation of point used for evaluation.
    eval_expression: PointRepresentation | ZeroPoint | None = None

    # Human tagged value for the Point
    tags: list[str] = attrs.field(factory=list)

    # Generate an automatic id
    uid: uuid.UUID = attrs.field(factory=uuid.uuid4, init=False)

    def __attrs_post_init__(self):
        if self.is_basis:
            assert self.eval_expression is None
        else:
            assert self.eval_expression is not None

        pep_context = pc.get_current_context()
        if pep_context is None:
            raise RuntimeError("Did you forget to create a context?")
        pep_context.add_point(self)

    @staticmethod
    def zero() -> Point:
        return Point(is_basis=False, eval_expression=ZeroPoint(), tags=["0"])

    @property
    def tag(self):
        """Returns the most recently added tag.

        Returns:
            str: The most recently added tag of this :class:`Point` object.
        """
        if len(self.tags) == 0:
            raise ValueError("Point should have a name.")
        return self.tags[-1]

    def add_tag(self, tag: str) -> None:
        """Add a new tag for this :class:`Point` object.

        Args:
            tag (str): The new tag to be added to the `tags` list.
        """
        self.tags.append(tag)

    def __repr__(self):
        if self.tags:
            return self.tag
        return super().__repr__()

    def _repr_latex_(self):
        return utils.str_to_latex(repr(self))

    # TODO: add a validator that `is_basis` and `eval_expression` are properly setup.
    def __add__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return Point(
            is_basis=False,
            eval_expression=PointRepresentation(utils.Op.ADD, self, other),
            tags=[f"{self.tag}+{other.tag}"],
        )

    def __radd__(self, other):
        # TODO: come up with better way to handle this
        if other == 0:
            return self
        if not isinstance(other, Point):
            return NotImplemented
        return Point(
            is_basis=False,
            eval_expression=PointRepresentation(utils.Op.ADD, other, self),
            tags=[f"{other.tag}+{self.tag}"],
        )

    def __sub__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        tag_other = utils.parenthesize_tag(other)
        return Point(
            is_basis=False,
            eval_expression=PointRepresentation(utils.Op.SUB, self, other),
            tags=[f"{self.tag}-{tag_other}"],
        )

    def __rsub__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        tag_self = utils.parenthesize_tag(self)
        return Point(
            is_basis=False,
            eval_expression=PointRepresentation(utils.Op.SUB, other, self),
            tags=[f"{other.tag}-{tag_self}"],
        )

    def __mul__(self, other):
        if not is_numerical_or_point(other):
            return NotImplemented
        tag_self = utils.parenthesize_tag(self)
        if utils.is_numerical_or_parameter(other):
            tag_other = utils.numerical_str(other)
            return Point(
                is_basis=False,
                eval_expression=PointRepresentation(utils.Op.MUL, self, other),
                tags=[f"{tag_self}*{tag_other}"],
            )
        else:
            tag_other = utils.parenthesize_tag(other)
            return Scalar(
                is_basis=False,
                eval_expression=ScalarRepresentation(utils.Op.MUL, self, other),
                tags=[f"{tag_self}*{tag_other}"],
            )

    def __rmul__(self, other):
        if not is_numerical_or_point(other):
            return NotImplemented
        tag_self = utils.parenthesize_tag(self)
        if utils.is_numerical_or_parameter(other):
            tag_other = utils.numerical_str(other)
            return Point(
                is_basis=False,
                eval_expression=PointRepresentation(utils.Op.MUL, other, self),
                tags=[f"{tag_other}*{tag_self}"],
            )
        else:
            tag_other = utils.parenthesize_tag(other)
            return Scalar(
                is_basis=False,
                eval_expression=ScalarRepresentation(utils.Op.MUL, other, self),
                tags=[f"{tag_other}*{tag_self}"],
            )

    def __pow__(self, power):
        if power != 2:
            return NotImplemented
        return Scalar(
            is_basis=False,
            eval_expression=ScalarRepresentation(utils.Op.MUL, self, self),
            tags=[rf"|{self.tag}|^{power}"],
        )

    def __neg__(self):
        tag_self = utils.parenthesize_tag(self)
        return Point(
            is_basis=False,
            eval_expression=PointRepresentation(utils.Op.MUL, -1, self),
            tags=[f"-{tag_self}"],
        )

    def __truediv__(self, other):
        if not utils.is_numerical_or_parameter(other):
            return NotImplemented
        tag_self = utils.parenthesize_tag(self)
        tag_other = f"1/{utils.numerical_str(other)}"
        return Point(
            is_basis=False,
            eval_expression=PointRepresentation(utils.Op.DIV, self, other),
            tags=[f"{tag_other}*{tag_self}"],
        )

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.uid == other.uid

    def eval(self, ctx: pc.PEPContext | None = None) -> np.ndarray:
        """
        Return the concrete representation of this :class:`Point`.
        Concrete representations of :class:`Point` objects are
        :class:`EvaluatedPoint` objects.

        Args:
            ctx (:class:`PEPContext` | None): The :class:`PEPContext` object
                we consider. `None` if we consider the current global
                :class:`PEPContext` object.

        Returns:
            :class:`EvaluatedPoint`: The concrete representation of
            this :class:`Point`.
        """
        from pepflow.expression_manager import ExpressionManager

        # Note this can be inefficient.
        if ctx is None:
            ctx = pc.get_current_context()
        if ctx is None:
            raise RuntimeError("Did you forget to create a context?")
        em = ExpressionManager(ctx)
        return em.eval_point(self).vector

    def repr_by_basis(self, ctx: pc.PEPContext | None = None) -> str:
        """
        Express this :class:`Point` object as the linear combination of
        the basis :class:`Point` objects of the given :class:`PEPContext`.
        This linear combination is expressed as a `str` where, to refer to
        the basis :class:`Point` objects, we use their tags.

        Args:
            ctx (:class:`PEPContext`): The :class:`PEPContext` object
                whose basis :class:`Point` objects we consider. `None` if
                we consider the current global :class:`PEPContext` object.

        Returns:
            str: The representation of this :class:`Point` object in terms of
            the basis :class:`Point` objects of the given :class:`PEPContext`.
        """
        from pepflow.expression_manager import ExpressionManager

        # Note this can be inefficient.
        if ctx is None:
            ctx = pc.get_current_context()
        if ctx is None:
            raise RuntimeError("Did you forget to create a context?")
        em = ExpressionManager(ctx)
        return em.repr_point_by_basis(self)
