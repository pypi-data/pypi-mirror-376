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

import enum
import numbers
from typing import TYPE_CHECKING, Any

import numpy as np
import sympy as sp

if TYPE_CHECKING:
    from pepflow.function import Function
    from pepflow.point import Point
    from pepflow.scalar import Scalar


NUMERICAL_TYPE = numbers.Number | sp.Rational


def SOP(v, w, sympy_mode: bool = False) -> np.ndarray:
    """Symmetric Outer Product."""
    coef = sp.S(1) / 2 if sympy_mode else 1 / 2
    return coef * (np.outer(v, w) + np.outer(w, v))


def SOP_self(v, sympy_mode: bool = False) -> np.ndarray:
    return SOP(v, v, sympy_mode=sympy_mode)


class Op(enum.Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"


class Comparator(enum.Enum):
    GT = "GT"
    LT = "LT"
    EQ = "EQ"


def is_numerical(val: Any) -> bool:
    return isinstance(val, numbers.Number) or isinstance(val, sp.Rational)


def is_numerical_or_parameter(val: Any) -> bool:
    from pepflow import parameter as param

    return is_numerical(val) or isinstance(val, param.Parameter)


def numerical_str(val: Any) -> str:
    from pepflow import parameter as param

    if not is_numerical_or_parameter(val):
        raise ValueError(
            "Cannot call numerical_str for {val} since it is not numerical."
        )
    if isinstance(val, param.Parameter):
        return str(val)
    return str(val) if isinstance(val, sp.Rational) else f"{val:.4g}"


def parenthesize_tag(val: Point | Scalar | Function) -> str:
    tmp_tag = val.tag
    if not val.is_basis:
        if op := getattr(val.eval_expression, "op", None):
            if op in (Op.ADD, Op.SUB):
                tmp_tag = f"({val.tag})"
    return tmp_tag


def str_to_latex(s: str) -> str:
    """Convert string into latex style."""
    s = s.replace("star", r"\star")
    s = s.replace("gradient_", r"\nabla ")
    s = s.replace("|", r"\|")
    return rf"$\displaystyle {s}$"
