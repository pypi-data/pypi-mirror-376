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

from pepflow import parameter as pm
from pepflow import pep_context as pc
from pepflow import point as pt
from pepflow import scalar as sc
from pepflow import utils


def tag_and_coef_to_str(tag: str, v: float) -> str:
    coef = utils.numerical_str(abs(v))
    sign = "+" if v >= 0 else "-"
    if math.isclose(abs(v), 1):
        return f"{sign} {tag} "
    elif math.isclose(v, 0, abs_tol=1e-5):
        return ""
    else:
        return f"{sign} {coef}*{tag} "


class ExpressionManager:
    """
    A class that handles the concrete representations of abstract
    :class:`Point` and :class:`Scalar` objects managed by a particular
    :class:`PEPContext` object.

    Attributes:
        context (:class:`PEPContext`): The :class:`PEPContext` object which
            manages the abstract :class:`Point` and :class:`Scalar` objects
            of interest.
        resolve_parameters (dict[str, :class:`NUMERICAL_TYPE`]): A dictionary that
            maps the name of parameters to the numerical values.
    """

    def __init__(
        self,
        pep_context: pc.PEPContext,
        resolve_parameters: dict[str, utils.NUMERICAL_TYPE] | None = None,
    ):
        self.context = pep_context
        self._basis_points = []
        self._basis_point_uid_to_index = {}
        self._basis_scalars = []
        self._basis_scalar_uid_to_index = {}
        self.resolve_parameters = resolve_parameters or {}
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
        """
        Return the concrete representation of the given :class:`Point`,
        `float`, or `int`. Concrete representations of :class:`Point` objects
        are :class:`EvaluatedPoint` objects. Concrete representations of
        `float` or `int` arguments are themselves.

        Args:
            point (:class:`Point`, float, int): The abstract :class:`Point`,
                `float`, or `int` object whose concrete representation we want
                to find.

        Returns:
            :class:`EvaluatedPoint` | float | int: The concrete representation
            the `point` argument.
        """
        if utils.is_numerical(point):
            return point

        if isinstance(point, pm.Parameter):
            return point.get_value(self.resolve_parameters)

        if point.is_basis:
            index = self.get_index_of_basis_point(point)
            array = np.zeros(self._num_basis_points)
            array[index] = 1
            return pt.EvaluatedPoint(vector=array)

        if isinstance(point.eval_expression, pt.ZeroPoint):
            return pt.EvaluatedPoint.zero(num_basis_points=self._num_basis_points)

        op = point.eval_expression.op
        left_evaled_point = self.eval_point(point.eval_expression.left_point)
        right_evaled_point = self.eval_point(point.eval_expression.right_point)
        if op == utils.Op.ADD:
            return left_evaled_point + right_evaled_point
        if op == utils.Op.SUB:
            return left_evaled_point - right_evaled_point
        if op == utils.Op.MUL:
            return left_evaled_point * right_evaled_point
        if op == utils.Op.DIV:
            return left_evaled_point / right_evaled_point

        raise ValueError(f"Encountered unknown {op=} when evaluation the point.")

    @functools.cache
    def eval_scalar(self, scalar: sc.Scalar | float | int):
        """
        Return the concrete representation of the given :class:`Scalar`,
        `float`, or `int`. Concrete representations of :class:`Scalar` objects
        are :class:`EvaluatedScalar` objects. Concrete representations of
        `float` or `int` arguments are themselves.

        Args:
            scalar (:class:`Point`, float, int): The abstract :class:`Scalar`,
                `float`, or `int` object whose concrete representation we want
                to find.

        Returns:
            :class:`EvaluatedScalar` | float | int: The concrete representation
            the `scalar` argument.
        """
        if utils.is_numerical(scalar):
            return scalar
        if isinstance(scalar, pm.Parameter):
            return scalar.get_value(self.resolve_parameters)

        if scalar.is_basis:
            index = self.get_index_of_basis_scalar(scalar)
            array = np.zeros(self._num_basis_scalars)
            array[index] = 1
            matrix = np.zeros((self._num_basis_points, self._num_basis_points))
            return sc.EvaluatedScalar(
                vector=array,
                matrix=matrix,
                constant=float(0.0),
            )

        if isinstance(scalar.eval_expression, sc.ZeroScalar):
            return sc.EvaluatedScalar.zero(
                num_basis_scalars=self._num_basis_scalars,
                num_basis_points=self._num_basis_points,
            )

        op = scalar.eval_expression.op
        # The special inner product usage.
        if (
            op == utils.Op.MUL
            and isinstance(scalar.eval_expression.left_scalar, pt.Point)
            and isinstance(scalar.eval_expression.right_scalar, pt.Point)
        ):
            array = np.zeros(self._num_basis_scalars)
            return sc.EvaluatedScalar(
                vector=array,
                matrix=utils.SOP(
                    self.eval_point(scalar.eval_expression.left_scalar).vector,
                    self.eval_point(scalar.eval_expression.right_scalar).vector,
                ),
                constant=float(0.0),
            )

        left_evaled_scalar = self.eval_scalar(scalar.eval_expression.left_scalar)
        right_evaled_scalar = self.eval_scalar(scalar.eval_expression.right_scalar)
        if op == utils.Op.ADD:
            return left_evaled_scalar + right_evaled_scalar
        if op == utils.Op.SUB:
            return left_evaled_scalar - right_evaled_scalar
        if op == utils.Op.MUL:
            return left_evaled_scalar * right_evaled_scalar
        if op == utils.Op.DIV:
            return left_evaled_scalar / right_evaled_scalar

        raise ValueError(f"Encountered unknown {op=} when evaluation the scalar.")

    @functools.cache
    def repr_point_by_basis(self, point: pt.Point) -> str:
        """
        Express the given :class:`Point` object as the linear combination of
        the basis :class:`Point` objects of the :class:`PEPContext` associated
        with this :class:`ExpressionManager`. This linear combination is
        expressed as a `str` where, to refer to the basis :class:`Point`
        objects, we use their tags.

        Args:
            point (:class:`Point`): The :class:`Point` object which we want
                to express in terms of the basis :class:`Point` objects.

        Returns:
            str: The representation of `point` in terms of the basis
            :class:`Point` objects of the :class:`PEPContext` associated
            with this :class:`ExpressionManager`.
        """
        assert isinstance(point, pt.Point)
        evaluated_point = self.eval_point(point)
        return self.repr_evaluated_point_by_basis(evaluated_point)

    def repr_evaluated_point_by_basis(self, evaluated_point: pt.EvaluatedPoint) -> str:
        """
        Express the given :class:`EvaluatedPoint` object as the linear
        combination of the basis :class:`Point` objects of the
        :class:`PEPContext` associated with this :class:`ExpressionManager`.
        This linear combination is expressed as a `str` where, to refer to the
        basis :class:`Point` objects, we use their tags.

        Args:
            evaluated_point (:class:`EvaluatedPoint`): The
                :class:`EvaluatedPoint` object which we want to express in
                terms of the basis :class:`Point` objects.

        Returns:
            str: The representation of `evaluated_point` in terms of
            the basis :class:`Point` objects of the :class:`PEPContext`
            associated with this :class:`ExpressionManager`.
        """
        repr_str = ""
        for i, v in enumerate(evaluated_point.vector):
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
    def repr_scalar_by_basis(
        self, scalar: sc.Scalar, greedy_square: bool = True
    ) -> str:
        """Express the given :class:`Scalar` object in terms of the basis
        :class:`Point` and :class:`Scalar` objects of the :class:`PEPContext`
        associated with this :class:`ExpressionManager`.

        A :class:`Scalar` can be formed by linear combinations of basis
        :class:`Scalar` objects. A :class:`Scalar` can also be formed through
        the inner product of two basis :class:`Point` objects. This function
        returns the representation of this :class:`Scalar` object in terms of
        the basis :class:`Point` and :class:`Scalar` objects as a `str` where,
        to refer to the basis :class:`Point` and :class:`Scalar` objects,
        we use their tags.

        Args:
            scalar (:class:`Scalar`): The :class:`Scalar` object which we want
                to express in terms of the basis :class:`Point` and
                :class:`Scalar` objects.
            greedy_square (bool): If `greedy_square` is true, the function will
                try to return :math:`\\|a-b\\|^2` whenever possible. If not,
                the function will return
                :math:`\\|a\\|^2 - 2 * \\langle a, b \\rangle + \\|b\\|^2` instead.
                `True` by default.

        Returns:
            str: The representation of `scalar` in terms of the basis
            :class:`Point` and :class:`Scalar` objects of the
            :class:`PEPContext` associated with this
            :class:`ExpressionManager`.
        """
        assert isinstance(scalar, sc.Scalar)
        evaluated_scalar = self.eval_scalar(scalar)
        return self.repr_evaluated_scalar_by_basis(
            evaluated_scalar, greedy_square=greedy_square
        )

    def repr_evaluated_scalar_by_basis(
        self, evaluated_scalar: sc.EvaluatedScalar, greedy_square: bool = True
    ) -> str:
        """Express the given :class:`EvaluatedScalar` object in terms of the
        basis :class:`Point` and :class:`Scalar` objects of the
        :class:`PEPContext` associated with this :class:`ExpressionManager`.

        A :class:`Scalar` can be formed by linear combinations of basis
        :class:`Scalar` objects. A :class:`Scalar` can also be formed through
        the inner product of two basis :class:`Point` objects. This function
        returns the representation of this :class:`Scalar` object in terms of
        the basis :class:`Point` and :class:`Scalar` objects as a `str` where,
        to refer to the basis :class:`Point` and :class:`Scalar` objects,
        we use their tags.

        Args:
            evaluated_scalar (:class:`EvaluatedScalar`): The
                :class:`EvaluatedScalar` object which we want to express in
                terms of the basis :class:`Point` and :class:`Scalar` objects.
            greedy_square (bool): If `greedy_square` is true, the function will
                try to return :math:`\\|a-b\\|^2` whenever possible. If not,
                the function will return
                :math:`\\|a\\|^2 - 2 * \\langle a, b \\rangle + \\|b\\|^2` instead.
                `True` by default.

        Returns:
            str: The representation of `evaluated_scalar` in terms of
            the basis :class:`Point` and :class:`Scalar` objects of the
            :class:`PEPContext` associated with this :class:`ExpressionManager`.
        """
        repr_str = ""
        if not math.isclose(evaluated_scalar.constant, 0, abs_tol=1e-5):
            repr_str += utils.numerical_str(evaluated_scalar.constant)

        for i, v in enumerate(evaluated_scalar.vector):
            # Note the tag is from scalar basis.
            ith_tag = self.get_tag_of_basis_scalar_index(i)
            repr_str += tag_and_coef_to_str(ith_tag, v)

        if greedy_square:
            diag_elem = np.diag(evaluated_scalar.matrix).copy()
            for i in range(evaluated_scalar.matrix.shape[0]):
                ith_tag = self.get_tag_of_basis_point_index(i)
                # j starts from i+1 since we want to handle the diag elem at last.
                for j in range(i + 1, evaluated_scalar.matrix.shape[0]):
                    jth_tag = self.get_tag_of_basis_point_index(j)
                    v = float(evaluated_scalar.matrix[i, j])
                    # We want to minimize the diagonal elements to zero greedily.
                    if diag_elem[i] * v > 0:  # same sign with diagonal elem
                        diag_elem[i] -= v
                        diag_elem[j] -= v
                        repr_str += tag_and_coef_to_str(f"|{ith_tag}+{jth_tag}|^2", v)
                    else:  # different sign
                        diag_elem[i] += v
                        diag_elem[j] += v
                        repr_str += tag_and_coef_to_str(f"|{ith_tag}-{jth_tag}|^2", -v)
                # Handle the diagonal elements
                repr_str += tag_and_coef_to_str(f"|{ith_tag}|^2", diag_elem[i])
        else:
            for i in range(evaluated_scalar.matrix.shape[0]):
                ith_tag = self.get_tag_of_basis_point_index(i)
                for j in range(i, evaluated_scalar.matrix.shape[0]):
                    jth_tag = self.get_tag_of_basis_point_index(j)
                    v = float(evaluated_scalar.matrix[i, j])
                    if i == j:
                        repr_str += tag_and_coef_to_str(f"|{ith_tag}|^2", v)
                    else:
                        repr_str += tag_and_coef_to_str(
                            f"<{ith_tag}, {jth_tag}>", 2 * v
                        )

        # Post processing
        if repr_str == "":
            return "0"
        if repr_str.startswith("+ "):
            repr_str = repr_str[2:]
        if repr_str.startswith("- "):
            repr_str = "-" + repr_str[2:]
        return repr_str.strip()


def represent_matrix_by_basis(matrix: np.ndarray, ctx: pc.PEPContext) -> str:
    """Express the given matrix in terms of the basis :class:`Point` objects
    of the given :class:`PEPContext`.

    The concrete representation of the inner product of two abstract
    basis :class:`Point` objects is a matrix (the outer product of the
    basis vectors corresponding to the concrete representations of the abstract
    basis :class:`Point` objects). The given matrix can then be expressed
    as a linear combination of the inner products of abstract basis
    :class:`Point` objects. This is provided as a `str` where, to refer to
    the basis :class:`Point` objects, we use their tags.

    Args:
        matrix (np.ndarray): The matrix which we want to express in terms of
            the basis :class:`Point` objects of the given :class:`PEPContext`.
        ctx (:class:`PEPContext`): The :class:`PEPContext` whose basis
            :class:`Point` objects we consider.

    Returns:
        str: The representation of `matrix` in terms of the basis
        :class:`Point` objects of `ctx`.
    """
    em = ExpressionManager(ctx)
    matrix_shape = (len(em._basis_points), len(em._basis_points))
    if matrix.shape != matrix_shape:
        raise ValueError(
            "The valid matrix for given context should have shape {matrix_shape}"
        )
    if not np.allclose(matrix, matrix.T):
        raise ValueError("Input matrix must be symmetric.")

    return em.repr_evaluated_scalar_by_basis(
        sc.EvaluatedScalar(
            vector=np.zeros(len(em._basis_scalars)), matrix=matrix, constant=0.0
        )
    )
