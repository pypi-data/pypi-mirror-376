import math

from pepflow import function
from pepflow import parameter as pm
from pepflow import pep
from pepflow import pep_context as pc


def test_gd_e2e():
    ctx = pc.PEPContext("gd").set_as_current()
    pep_builder = pep.PEPBuilder()
    eta = 1
    N = 9

    f = pep_builder.declare_func(function.SmoothConvexFunction, "f", L=1)
    x = pep_builder.set_init_point("x_0")
    x_star = f.add_stationary_point("x_star")
    pep_builder.set_initial_constraint(
        ((x - x_star) ** 2).le(1, name="initial_condition")
    )

    # We first build the algorithm with the largest number of iterations.
    for i in range(N):
        x = x - eta * f.gradient(x)
        x.add_tag(f"x_{i + 1}")

    # To achieve the sweep, we can just update the performance_metric.
    for i in range(1, N + 1):
        p = ctx.get_by_tag(f"x_{i}")
        pep_builder.set_performance_metric(
            f.function_value(p) - f.function_value(x_star)
        )
        result = pep_builder.solve_primal()
        expected_opt_value = 1 / (4 * i + 2)
        assert math.isclose(result.primal_opt_value, expected_opt_value, rel_tol=1e-3)

        dual_result = pep_builder.solve_dual()
        assert math.isclose(
            dual_result.dual_opt_value, expected_opt_value, rel_tol=1e-3
        )


def test_gd_diff_stepsize_e2e():
    pc.PEPContext("gd").set_as_current()
    pep_builder = pep.PEPBuilder()
    eta = 1 / pm.Parameter(name="L")
    N = 4

    f = pep_builder.declare_func(
        function.SmoothConvexFunction, "f", L=pm.Parameter(name="L")
    )
    x = pep_builder.set_init_point("x_0")
    x_star = f.add_stationary_point("x_star")
    pep_builder.set_initial_constraint(
        ((x - x_star) ** 2).le(1, name="initial_condition")
    )

    # We first build the algorithm with the largest number of iterations.
    for i in range(N):
        x = x - eta * f.gradient(x)
        x.add_tag(f"x_{i + 1}")
    pep_builder.set_performance_metric(f(x) - f(x_star))

    for l_val in [1, 4, 0.25]:
        result = pep_builder.solve_primal(resolve_parameters={"L": l_val})
        expected_opt_value = l_val / (4 * N + 2)
        assert math.isclose(result.primal_opt_value, expected_opt_value, rel_tol=1e-3)

        dual_result = pep_builder.solve_dual(resolve_parameters={"L": l_val})
        assert math.isclose(
            dual_result.dual_opt_value, expected_opt_value, rel_tol=1e-3
        )


def test_pgm_e2e():
    ctx = pc.PEPContext("pgm").set_as_current()
    pep_builder = pep.PEPBuilder()
    eta = 1
    N = 1

    f = pep_builder.declare_func(function.SmoothConvexFunction, "f", L=1)
    g = pep_builder.declare_func(function.ConvexFunction, "g")

    h = f + g

    x = pep_builder.set_init_point("x_0")
    x_star = h.add_stationary_point("x_star")
    pep_builder.set_initial_constraint(
        ((x - x_star) ** 2).le(1, name="initial_condition")
    )

    # We first build the algorithm with the largest number of iterations.
    for i in range(N):
        y = x - eta * f.gradient(x)
        y.add_tag(f"y_{i + 1}")
        x = g.proximal_step(y, eta)
        x.add_tag(f"x_{i + 1}")

    # To achieve the sweep, we can just update the performance_metric.
    for i in range(1, N + 1):
        p = ctx.get_by_tag(f"x_{i}")
        pep_builder.set_performance_metric(
            h.function_value(p) - h.function_value(x_star)
        )

        result = pep_builder.solve_primal()
        expected_opt_value = 1 / (4 * i)
        assert math.isclose(result.primal_opt_value, expected_opt_value, rel_tol=1e-3)

        dual_result = pep_builder.solve_dual()
        assert math.isclose(
            dual_result.dual_opt_value, expected_opt_value, rel_tol=1e-3
        )
