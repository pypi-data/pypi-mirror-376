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

import functools
import math

import numpy as np

from pepflow import pep_context as pc
from pepflow import point as pt
from pepflow import scalar as sc
from pepflow import utils


def tag_and_coef_to_str(tag: str, v: float) -> str:
    coef = f"{abs(v):.3g}"
    sign = "+" if v >= 0 else "-"
    if math.isclose(abs(v), 1):
        return f"{sign} {tag} "
    elif math.isclose(v, 0):
        return ""
    else:
        return f"{sign} {coef}*{tag} "


class ExpressionManager:
    def __init__(self, pep_context: pc.PEPContext):
        self.context = pep_context
        self._basis_points = []
        self._basis_point_uid_to_index = {}
        self._basis_scalars = []
        self._basis_scalar_uid_to_index = {}
        for point in self.context.points:
            if point.is_basis:
                self._basis_points.append(point)
                self._basis_point_uid_to_index[point.uid] = len(self._basis_points) - 1
        for scalar in self.context.scalars:
            if scalar.is_basis:
                self._basis_scalars.append(scalar)
                self._basis_scalar_uid_to_index[scalar.uid] = (
                    len(self._basis_scalars) - 1
                )

        self._num_basis_points = len(self._basis_points)
        self._num_basis_scalars = len(self._basis_scalars)

    def get_index_of_basis_point(self, point: pt.Point) -> int:
        return self._basis_point_uid_to_index[point.uid]

    def get_index_of_basis_scalar(self, scalar: sc.Scalar) -> int:
        return self._basis_scalar_uid_to_index[scalar.uid]

    def get_tag_of_basis_point_index(self, index: int) -> str:
        return self._basis_points[index].tag

    def get_tag_of_basis_scalar_index(self, index: int) -> str:
        return self._basis_scalars[index].tag

    @functools.cache
    def eval_point(self, point: pt.Point | float | int):
        if utils.is_numerical(point):
            return point

        array = np.zeros(self._num_basis_points)
        if point.is_basis:
            index = self.get_index_of_basis_point(point)
            array[index] = 1
            return pt.EvaluatedPoint(vector=array)

        op = point.eval_expression.op
        if op == utils.Op.ADD:
            return self.eval_point(point.eval_expression.left_point) + self.eval_point(
                point.eval_expression.right_point
            )
        if op == utils.Op.SUB:
            return self.eval_point(point.eval_expression.left_point) - self.eval_point(
                point.eval_expression.right_point
            )
        if op == utils.Op.MUL:
            return self.eval_point(point.eval_expression.left_point) * self.eval_point(
                point.eval_expression.right_point
            )
        if op == utils.Op.DIV:
            return self.eval_point(point.eval_expression.left_point) / self.eval_point(
                point.eval_expression.right_point
            )

        raise ValueError("This should never happen!")

    @functools.cache
    def eval_scalar(self, scalar: sc.Scalar | float | int):
        if utils.is_numerical(scalar):
            return scalar

        array = np.zeros(self._num_basis_scalars)
        if scalar.is_basis:
            index = self.get_index_of_basis_scalar(scalar)
            array[index] = 1
            return sc.EvaluatedScalar(
                vector=array,
                matrix=np.zeros((self._num_basis_points, self._num_basis_points)),
                constant=float(0.0),
            )
        op = scalar.eval_expression.op
        if op == utils.Op.ADD:
            return self.eval_scalar(
                scalar.eval_expression.left_scalar
            ) + self.eval_scalar(scalar.eval_expression.right_scalar)
        if op == utils.Op.SUB:
            return self.eval_scalar(
                scalar.eval_expression.left_scalar
            ) - self.eval_scalar(scalar.eval_expression.right_scalar)
        if op == utils.Op.MUL:
            if isinstance(scalar.eval_expression.left_scalar, pt.Point) and isinstance(
                scalar.eval_expression.right_scalar, pt.Point
            ):
                return sc.EvaluatedScalar(
                    vector=np.zeros(self._num_basis_scalars),
                    matrix=utils.SOP(
                        self.eval_point(scalar.eval_expression.left_scalar).vector,
                        self.eval_point(scalar.eval_expression.right_scalar).vector,
                    ),
                    constant=float(0.0),
                )
            else:
                return self.eval_scalar(
                    scalar.eval_expression.left_scalar
                ) * self.eval_scalar(scalar.eval_expression.right_scalar)
        if op == utils.Op.DIV:
            return self.eval_scalar(
                scalar.eval_expression.left_scalar
            ) / self.eval_scalar(scalar.eval_expression.right_scalar)

        raise ValueError("This should never happen!")

    @functools.cache
    def repr_point_by_basis(self, point: pt.Point) -> str:
        assert isinstance(point, pt.Point)
        repr_array = self.eval_point(point).vector

        repr_str = ""
        for i, v in enumerate(repr_array):
            ith_tag = self.get_tag_of_basis_point_index(i)
            repr_str += tag_and_coef_to_str(ith_tag, v)

        # Post processing
        if repr_str == "":
            return "0"
        if repr_str.startswith("+ "):
            repr_str = repr_str[2:]
        if repr_str.startswith("- "):
            repr_str = "-" + repr_str[2:]
        return repr_str.strip()

    @functools.cache
    def repr_scalar_by_basis(self, scalar: sc.Scalar) -> str:
        assert isinstance(scalar, sc.Scalar)
        evaluated_scalar = self.eval_scalar(scalar)

        repr_str = ""
        if not math.isclose(evaluated_scalar.constant, 0):
            repr_str += f"{evaluated_scalar.constant:.3g}"

        for i, v in enumerate(evaluated_scalar.vector):
            # Note the tag is from scalar basis.
            ith_tag = self.get_tag_of_basis_scalar_index(i)
            repr_str += tag_and_coef_to_str(ith_tag, v)

        for i in range(evaluated_scalar.matrix.shape[0]):
            for j in range(i, evaluated_scalar.matrix.shape[0]):
                ith_tag = self.get_tag_of_basis_point_index(i)
                v = evaluated_scalar.matrix[i, j]
                if i == j:
                    repr_str += tag_and_coef_to_str(f"|{ith_tag}|^2", v)
                    continue
                jth_tag = self.get_tag_of_basis_point_index(j)
                repr_str += tag_and_coef_to_str(f"<{ith_tag}, {jth_tag}>", 2 * v)

        # Post processing
        if repr_str == "":
            return "0"
        if repr_str.startswith("+ "):
            repr_str = repr_str[2:]
        if repr_str.startswith("- "):
            repr_str = "-" + repr_str[2:]
        return repr_str.strip()
