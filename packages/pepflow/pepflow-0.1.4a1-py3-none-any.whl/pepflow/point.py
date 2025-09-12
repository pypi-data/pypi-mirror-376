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
from pepflow.scalar import EvalExpressionScalar, Scalar


def is_numerical_or_point(val: Any) -> bool:
    return utils.is_numerical(val) or isinstance(val, Point)


def is_numerical_or_evaluatedpoint(val: Any) -> bool:
    return utils.is_numerical(val) or isinstance(val, EvaluatedPoint)


@attrs.frozen
class EvalExpressionPoint:
    op: utils.Op
    left_point: Point | float
    right_point: Point | float


@attrs.frozen
class EvaluatedPoint:
    vector: np.ndarray

    def __add__(self, other):
        if isinstance(other, EvaluatedPoint):
            return EvaluatedPoint(vector=self.vector + other.vector)
        elif utils.is_numerical(other):
            return EvaluatedPoint(vector=self.vector + other)
        else:
            raise ValueError(
                f"Unsupported add operation between EvaluatedPoint and {type(other)}"
            )

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, EvaluatedPoint):
            return EvaluatedPoint(vector=self.vector - other.vector)
        elif utils.is_numerical(other):
            return EvaluatedPoint(vector=self.vector - other)
        else:
            raise ValueError(
                f"Unsupported sub operation between EvaluatedPoint and {type(other)}"
            )

    def __rsub__(self, other):
        if isinstance(other, EvaluatedPoint):
            return EvaluatedPoint(vector=other.vector - self.vector)
        elif utils.is_numerical(other):
            return EvaluatedPoint(vector=other - self.vector)
        else:
            raise ValueError(
                f"Unsupported sub operation between EvaluatedPoint and {type(other)}"
            )

    def __mul__(self, other):
        assert utils.is_numerical(other)
        return EvaluatedPoint(vector=self.vector * other)

    def __rmul__(self, other):
        assert utils.is_numerical(other)
        return EvaluatedPoint(vector=other * self.vector)

    def __truediv__(self, other):
        assert utils.is_numerical(other)
        return EvaluatedPoint(vector=self.vector / other)


@attrs.frozen
class Point:
    # If true, the point is the basis for the evaluations of G
    is_basis: bool

    # How to evaluate the point.
    eval_expression: EvalExpressionPoint | None = None

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

    @property
    def tag(self):
        if len(self.tags) == 0:
            raise ValueError("Point should have a name.")
        return self.tags[-1]

    def add_tag(self, tag: str) -> None:
        self.tags.append(tag)

    def __repr__(self):
        if self.tags:
            return self.tag
        return super().__repr__()

    def _repr_latex_(self):
        s = repr(self)
        s = s.replace("star", r"\star")
        s = s.replace("gradient_", r"\nabla ")
        s = s.replace("|", r"\|")
        return rf"$\\displaystyle {s}$"

    # TODO: add a validator that `is_basis` and `eval_expression` are properly setup.
    def __add__(self, other):
        assert isinstance(other, Point)
        return Point(
            is_basis=False,
            eval_expression=EvalExpressionPoint(utils.Op.ADD, self, other),
            tags=[f"{self.tag}+{other.tag}"],
        )

    def __radd__(self, other):
        # TODO: come up with better way to handle this
        if other == 0:
            return self
        assert isinstance(other, Point)
        return Point(
            is_basis=False,
            eval_expression=EvalExpressionPoint(utils.Op.ADD, other, self),
            tags=[f"{other.tag}+{self.tag}"],
        )

    def __sub__(self, other):
        assert isinstance(other, Point)
        tag_other = utils.parenthesize_tag(other)
        return Point(
            is_basis=False,
            eval_expression=EvalExpressionPoint(utils.Op.SUB, self, other),
            tags=[f"{self.tag}-{tag_other}"],
        )

    def __rsub__(self, other):
        assert isinstance(other, Point)
        tag_self = utils.parenthesize_tag(self)
        return Point(
            is_basis=False,
            eval_expression=EvalExpressionPoint(utils.Op.SUB, other, self),
            tags=[f"{other.tag}-{tag_self}"],
        )

    def __mul__(self, other):
        # TODO allow the other to be point so that we return a scalar.
        assert is_numerical_or_point(other)
        tag_self = utils.parenthesize_tag(self)
        if utils.is_numerical(other):
            return Point(
                is_basis=False,
                eval_expression=EvalExpressionPoint(utils.Op.MUL, self, other),
                tags=[f"{tag_self}*{other:.4g}"],
            )
        else:
            tag_other = utils.parenthesize_tag(other)
            return Scalar(
                is_basis=False,
                eval_expression=EvalExpressionScalar(utils.Op.MUL, self, other),
                tags=[f"{tag_self}*{tag_other}"],
            )

    def __rmul__(self, other):
        # TODO allow the other to be point so that we return a scalar.
        assert is_numerical_or_point(other)
        tag_self = utils.parenthesize_tag(self)
        if utils.is_numerical(other):
            return Point(
                is_basis=False,
                eval_expression=EvalExpressionPoint(utils.Op.MUL, other, self),
                tags=[f"{other:.4g}*{tag_self}"],
            )
        else:
            tag_other = utils.parenthesize_tag(other)
            return Scalar(
                is_basis=False,
                eval_expression=EvalExpressionScalar(utils.Op.MUL, other, self),
                tags=[f"{tag_other}*{tag_self}"],
            )

    def __pow__(self, power):
        assert power == 2
        return Scalar(
            is_basis=False,
            eval_expression=EvalExpressionScalar(utils.Op.MUL, self, self),
            tags=[rf"|{self.tag}|^{power}"],
        )

    def __neg__(self):
        tag_self = utils.parenthesize_tag(self)
        return Point(
            is_basis=False,
            eval_expression=EvalExpressionPoint(utils.Op.MUL, -1, self),
            tags=[f"-{tag_self}"],
        )

    def __truediv__(self, other):
        assert utils.is_numerical(other)
        tag_self = utils.parenthesize_tag(self)
        return Point(
            is_basis=False,
            eval_expression=EvalExpressionPoint(utils.Op.DIV, self, other),
            tags=[f"1/{other:.4g}*{tag_self}"],
        )

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.uid == other.uid

    def eval(self, ctx: pc.PEPContext | None = None) -> np.ndarray:
        from pepflow.expression_manager import ExpressionManager

        # Note this can be inefficient.
        if ctx is None:
            ctx = pc.get_current_context()
        if ctx is None:
            raise RuntimeError("Did you forget to create a context?")
        em = ExpressionManager(ctx)
        return em.eval_point(self).vector
