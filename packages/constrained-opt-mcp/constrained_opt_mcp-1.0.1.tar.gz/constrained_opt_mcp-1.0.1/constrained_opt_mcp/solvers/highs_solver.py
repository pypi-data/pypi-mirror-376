"""
HiGHS linear and mixed-integer programming solver implementation.
"""

import time
from typing import Dict, List, Optional, Tuple

import highspy
import numpy as np
from returns.result import Failure, Result, Success

from ..models.highs_models import (
    HiGHSConstraints,
    HiGHSConstraintSense,
    HiGHSObjective,
    HiGHSOptions,
    HiGHSProblem,
    HiGHSProblemSpec,
    HiGHSSense,
    HiGHSStatus,
    HiGHSVariable,
    HiGHSVariableType,
)


def _convert_sense_to_highs(sense: HiGHSSense) -> int:
    """Convert HiGHSSense to HiGHs minimize flag."""
    return 1 if sense == HiGHSSense.MINIMIZE else -1


def _convert_constraint_sense(
    sense: HiGHSConstraintSense, rhs: float
) -> Tuple[float, float]:
    """Convert constraint sense to lower and upper bounds."""
    inf = highspy.kHighsInf

    match sense:
        case HiGHSConstraintSense.LESS_EQUAL:
            return (-inf, rhs)
        case HiGHSConstraintSense.GREATER_EQUAL:
            return (rhs, inf)
        case HiGHSConstraintSense.EQUAL:
            return (rhs, rhs)


def _get_variable_bounds(
    var_spec: HiGHSVariable, var_index: int
) -> Tuple[float, float]:
    """Get variable bounds, applying defaults based on variable type."""
    inf = highspy.kHighsInf

    # Default bounds based on type
    if var_spec.type == HiGHSVariableType.BINARY:
        default_lb, default_ub = 0.0, 1.0
    else:
        default_lb, default_ub = 0.0, inf

    lb = var_spec.lb if var_spec.lb is not None else default_lb
    ub = var_spec.ub if var_spec.ub is not None else default_ub

    return (lb, ub)


def _build_constraint_matrix(
    problem_spec: HiGHSProblemSpec,
) -> Result[Tuple[np.ndarray, np.ndarray, np.ndarray], str]:
    """Build constraint matrix in sparse format."""
    try:
        constraints = problem_spec.constraints

        if constraints.dense is not None:
            # Convert dense matrix to sparse format
            dense_matrix = np.array(constraints.dense)
            rows, cols = np.nonzero(dense_matrix)
            values = dense_matrix[rows, cols]

            return Success((rows.astype(int), cols.astype(int), values.astype(float)))

        elif constraints.sparse is not None:
            # Use provided sparse format
            sparse = constraints.sparse
            rows = np.array(sparse.rows, dtype=int)
            cols = np.array(sparse.cols, dtype=int)
            values = np.array(sparse.values, dtype=float)

            return Success((rows, cols, values))
        else:
            return Failure("Either dense or sparse constraint matrix must be provided")

    except Exception as e:
        return Failure(f"Error building constraint matrix: {e}")


def _apply_options(
    h: "highspy.Highs", options: Optional[HiGHSOptions]
) -> Result[None, str]:
    """Apply solver options to HiGHs instance."""
    try:
        if options is None:
            return Success(None)

        # Time limit
        if options.time_limit is not None:
            h.setOptionValue("time_limit", options.time_limit)

        # Presolve
        if options.presolve is not None:
            h.setOptionValue("presolve", options.presolve.value)

        # Solver
        if options.solver is not None:
            h.setOptionValue("solver", options.solver.value)

        # Parallel
        if options.parallel is not None:
            h.setOptionValue("parallel", options.parallel.value)

        # Threads
        if options.threads is not None:
            h.setOptionValue("threads", options.threads)

        # Random seed
        if options.random_seed is not None:
            h.setOptionValue("random_seed", options.random_seed)

        # Tolerances
        if options.primal_feasibility_tolerance is not None:
            h.setOptionValue(
                "primal_feasibility_tolerance", options.primal_feasibility_tolerance
            )

        if options.dual_feasibility_tolerance is not None:
            h.setOptionValue(
                "dual_feasibility_tolerance", options.dual_feasibility_tolerance
            )

        # Logging
        if options.output_flag is not None:
            h.setOptionValue("output_flag", options.output_flag)

        if options.log_to_console is not None:
            h.setOptionValue("log_to_console", options.log_to_console)

        return Success(None)

    except Exception as e:
        return Failure(f"Error applying options: {e}")


def _convert_status(model_status: "highspy.HighsModelStatus") -> HiGHSStatus:
    """Convert HiGHs model status to HiGHSStatus enum."""
    # HiGHs status constants
    if model_status == highspy.HighsModelStatus.kOptimal:
        return HiGHSStatus.OPTIMAL
    elif model_status == highspy.HighsModelStatus.kInfeasible:
        return HiGHSStatus.INFEASIBLE
    elif model_status == highspy.HighsModelStatus.kUnbounded:
        return HiGHSStatus.UNBOUNDED
    elif model_status == highspy.HighsModelStatus.kUnboundedOrInfeasible:
        return HiGHSStatus.UNBOUNDED  # or could be a separate status
    else:
        return HiGHSStatus.UNKNOWN


def solve_highs_problem(problem: HiGHSProblem) -> Result[HiGHSProblem, str]:
    """Solve a HiGHs optimization problem."""
    try:
        # Validate problem
        if not problem.validate():
            return Failure("Invalid problem definition")

        start_time = time.time()
        
        # Create HiGHs instance
        h = highspy.Highs()

        # Always disable output for MCP server compatibility
        h.setOptionValue("output_flag", False)
        h.setOptionValue("log_to_console", False)

        # Apply options
        options_result = _apply_options(h, problem.options)
        if isinstance(options_result, Failure):
            return options_result

        problem_spec = problem.problem
        num_vars = len(problem_spec.variables)
        num_constraints = len(problem_spec.constraints.sense)

        # Set up objective
        obj_coeffs = np.array(problem_spec.objective.linear, dtype=float)
        if len(obj_coeffs) != num_vars:
            return Failure(
                f"Objective coefficients length ({len(obj_coeffs)}) doesn't match number of variables ({num_vars})"
            )

        # Set up variable bounds
        var_lower = np.zeros(num_vars, dtype=float)
        var_upper = np.full(num_vars, highspy.kHighsInf, dtype=float)

        for i, var_spec in enumerate(problem_spec.variables):
            lb, ub = _get_variable_bounds(var_spec, i)
            var_lower[i] = lb
            var_upper[i] = ub

        # Build constraint matrix
        matrix_result = _build_constraint_matrix(problem_spec)
        if isinstance(matrix_result, Failure):
            return matrix_result

        rows, cols, values = matrix_result.unwrap()

        # Set up constraint bounds
        constraint_lower = np.zeros(num_constraints, dtype=float)
        constraint_upper = np.zeros(num_constraints, dtype=float)

        for i, (sense, rhs) in enumerate(
            zip(
                problem_spec.constraints.sense,
                problem_spec.constraints.rhs,
                strict=False,
            )
        ):
            lb, ub = _convert_constraint_sense(sense, rhs)
            constraint_lower[i] = lb
            constraint_upper[i] = ub

        # Add variables
        h.addCols(
            num_vars,
            obj_coeffs,
            var_lower,
            var_upper,
            0,
            np.array([]),
            np.array([]),
            np.array([]),
        )

        # Set variable integrality constraints
        integrality = np.zeros(num_vars, dtype=int)  # 0 = continuous
        for i, var_spec in enumerate(problem_spec.variables):
            if var_spec.type == HiGHSVariableType.BINARY:
                integrality[i] = 1  # 1 = integer (binary is integer with bounds 0-1)
            elif var_spec.type == HiGHSVariableType.INTEGER:
                integrality[i] = 1  # 1 = integer
            # else: continuous (already 0)

        # Apply integrality constraints if any variables are integer/binary
        if np.any(integrality > 0):
            h.changeColsIntegrality(num_vars, np.arange(num_vars), integrality)

        # Add constraints using sparse format
        if len(rows) > 0:
            # Convert to row-wise sparse format for HiGHs
            # Group by rows and create start array
            unique_rows = np.unique(rows)
            start_array = np.zeros(num_constraints + 1, dtype=int)

            for row in unique_rows:
                start_array[row] = np.sum(rows < row)

            start_array[-1] = len(rows)  # Final start

            h.addRows(
                num_constraints,
                constraint_lower,
                constraint_upper,
                len(values),
                start_array,
                cols,
                values,
            )
        else:
            # No constraints case
            h.addRows(
                num_constraints,
                constraint_lower,
                constraint_upper,
                0,
                np.array([0]),
                np.array([]),
                np.array([]),
            )

        # Set objective sense
        if problem_spec.sense == HiGHSSense.MAXIMIZE:
            h.changeObjectiveSense(highspy.ObjSense.kMaximize)
        else:
            h.changeObjectiveSense(highspy.ObjSense.kMinimize)

        # Solve the problem
        h.run()
        solve_time = time.time() - start_time

        # Get results
        model_status = h.getModelStatus()
        solution = h.getSolution()
        info = h.getInfo()

        # Convert status
        status = _convert_status(model_status)

        # Extract solution values
        solution_values = solution.col_value if hasattr(solution, "col_value") else []
        dual_values = solution.row_dual if hasattr(solution, "row_dual") else []
        reduced_costs = solution.col_dual if hasattr(solution, "col_dual") else []

        # Get objective value
        objective_value = (
            info.objective_function_value
            if hasattr(info, "objective_function_value")
            else 0.0
        )

        # Create solution with variable names
        values = {}
        for i, var_spec in enumerate(problem_spec.variables):
            var_name = var_spec.name or f"x{i}"
            values[var_name] = solution_values[i] if i < len(solution_values) else 0.0

        # Create solver statistics
        solver_stats = {
            "solve_time": solve_time,
            "iterations": getattr(info, "simplex_iteration_count", 0),
            "num_variables": num_vars,
            "num_constraints": num_constraints,
        }

        solution = HiGHSProblem(
            problem=problem_spec,
            options=problem.options,
            values=values,
            objective_value=objective_value,
            status=status,
            is_optimal=status == HiGHSStatus.OPTIMAL,
            solve_time=solve_time,
            dual_values=dual_values,
            reduced_costs=reduced_costs,
            solver_stats=solver_stats,
        )

        return Success(solution)

    except Exception as e:
        return Failure(f"Error solving HiGHs problem: {e}")
