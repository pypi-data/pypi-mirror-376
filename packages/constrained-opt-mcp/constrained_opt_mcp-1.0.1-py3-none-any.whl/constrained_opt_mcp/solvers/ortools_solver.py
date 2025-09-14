"""
OR-Tools constraint programming and combinatorial optimization solver implementation.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from ortools.sat.python import cp_model
from returns.result import Failure, Result, Success

from ..models.ortools_models import (
    ORToolsConstraint,
    ORToolsObjective,
    ORToolsProblem,
    ORToolsSolution,
    ORToolsVariable,
    ORToolsVariableType,
    ORToolsObjectiveType,
)


def create_variable(
    model: cp_model.CpModel, variable: ORToolsVariable, variables: Dict[str, Any]
) -> Result[None, str]:
    """Create an OR-Tools variable from a ORToolsVariable model.

    Args:
        model: The OR-Tools CpModel
        variable: The variable definition
        variables: Dictionary to store created variables

    Returns:
        Result containing None if successful or an error message
    """
    try:
        name = variable.name
        match variable.type:
            case ORToolsVariableType.BOOLEAN:
                if variable.shape:
                    # Create array of boolean variables using nested lists
                    shape = variable.shape
                    bool_array: List[Any] = []
                    for idx in range(shape[0]):
                        if len(shape) == 1:
                            bool_array.append(model.new_bool_var(f"{name}_{idx}"))
                        else:
                            bool_row: List[Any] = []
                            for jdx in range(shape[1]):
                                if len(shape) == 2:
                                    bool_row.append(
                                        model.new_bool_var(f"{name}_{idx}_{jdx}")
                                    )
                                else:
                                    bool_plane: List[Any] = []
                                    for kdx in range(shape[2]):
                                        bool_plane.append(
                                            model.new_bool_var(
                                                f"{name}_{idx}_{jdx}_{kdx}"
                                            )
                                        )
                                    bool_row.append(bool_plane)
                            bool_array.append(bool_row)
                    variables[name] = bool_array
                else:
                    variables[name] = model.new_bool_var(name)
            case ORToolsVariableType.INTEGER:
                if not variable.domain:
                    return Failure(f"Integer variable {name} requires a domain")
                if variable.shape:
                    # Create array of integer variables using nested lists
                    shape = variable.shape
                    int_array: List[Any] = []
                    for idx in range(shape[0]):
                        if len(shape) == 1:
                            int_array.append(
                                model.new_int_var(
                                    variable.domain[0],
                                    variable.domain[1],
                                    f"{name}_{idx}",
                                )
                            )
                        else:
                            int_row: List[Any] = []
                            for jdx in range(shape[1]):
                                int_row.append(
                                    model.new_int_var(
                                        variable.domain[0],
                                        variable.domain[1],
                                        f"{name}_{idx}_{jdx}",
                                    )
                                )
                            int_array.append(int_row)
                    variables[name] = int_array
                else:
                    variables[name] = model.new_int_var(
                        variable.domain[0], variable.domain[1], name
                    )
            case ORToolsVariableType.INTERVAL:
                if not variable.domain:
                    return Failure(f"Interval variable {name} requires a domain")
                variables[name] = model.new_interval_var(
                    start=model.new_int_var(
                        variable.domain[0], variable.domain[1], f"{name}_start"
                    ),
                    size=variable.domain[1] - variable.domain[0],
                    end=model.new_int_var(
                        variable.domain[0], variable.domain[1], f"{name}_end"
                    ),
                    name=name,
                )
            case _:
                return Failure(f"Unsupported variable type: {variable.type}")
        return Success(None)
    except Exception as e:
        return Failure(f"Error creating variable {variable.name}: {e!s}")


def create_variables(
    model: cp_model.CpModel, variables: List[ORToolsVariable]
) -> Result[Tuple[Dict[str, Any], Dict[str, Any]], str]:
    """Create OR-Tools variables from variable definitions.

    Args:
        model: The OR-Tools CpModel
        variables: List of variable definitions

    Returns:
        Result containing a tuple of (variables_dict, globals_dict) or an error message
    """
    result_dict: Dict[str, Any] = {}

    # First pass: create all variables
    for var in variables:
        result = create_variable(model, var, result_dict)
        if isinstance(result, Failure):
            return result

    # Second pass: add variables to globals for constraint evaluation
    globals_dict: Dict[str, Any] = {}
    for var in variables:
        globals_dict[var.name] = result_dict[var.name]

    return Success((result_dict, globals_dict))


def parse_constraint(
    model: cp_model.CpModel,
    constraint: ORToolsConstraint,
    variables: Dict[str, Any],
    globals_dict: Dict[str, Any],
) -> Result[None, str]:
    """Parse a constraint expression into an OR-Tools constraint.

    Args:
        model: The OR-Tools CpModel
        constraint: The constraint definition
        variables: Dictionary of variable names to OR-Tools variables
        globals_dict: Dictionary of global variables for constraint evaluation

    Returns:
        Result containing None if successful or an error message
    """
    try:
        # Create a local dictionary with OR-Tools functions and variables
        local_dict = {
            "model": model,
            "sum": sum,
            "abs": abs,
            "min": min,
            "max": max,
            "all": all,
            "any": any,
            "range": range,
        }

        # Add variables to the local dictionary
        for name, value in globals_dict.items():
            local_dict[name] = value

        # Evaluate the expression in the context of the local dictionary
        eval(constraint.expression, {"__builtins__": {}}, local_dict)
        return Success(None)
    except Exception as e:
        return Failure(f"Error parsing constraint '{constraint.expression}': {e!s}")


def create_constraints(
    model: cp_model.CpModel,
    constraints: List[ORToolsConstraint],
    variables: Dict[str, Any],
    globals_dict: Dict[str, Any],
) -> Result[None, str]:
    """Create OR-Tools constraints from constraint definitions.

    Args:
        model: The OR-Tools CpModel
        constraints: List of constraint definitions
        variables: Dictionary of variable names to OR-Tools variables
        globals_dict: Dictionary of global variables for constraint evaluation

    Returns:
        Result containing None if successful or an error message
    """
    for constraint in constraints:
        result = parse_constraint(model, constraint, variables, globals_dict)
        if isinstance(result, Failure):
            return result

    return Success(None)


def add_objective(
    model: cp_model.CpModel,
    objective: Optional[ORToolsObjective],
    variables: Dict[str, Any],
    globals_dict: Dict[str, Any],
) -> Result[None, str]:
    """Add objective to the OR-Tools model.

    Args:
        model: The OR-Tools CpModel
        objective: The objective definition
        variables: Dictionary of variable names to OR-Tools variables
        globals_dict: Dictionary of global variables for objective evaluation

    Returns:
        Result containing None if successful or an error message
    """
    if not objective or not objective.expression:
        return Success(None)

    try:
        # Create a local dictionary with OR-Tools functions and variables
        local_dict = {
            **globals_dict,  # Add variables to globals
            "sum": sum,
            "abs": abs,
            "min": min,
            "max": max,
        }

        # Evaluate the objective expression
        obj_expr = eval(objective.expression, {"__builtins__": {}}, local_dict)

        match objective.type:
            case ORToolsObjectiveType.MINIMIZE:
                model.minimize(obj_expr)
            case ORToolsObjectiveType.MAXIMIZE:
                model.maximize(obj_expr)
            case _:
                pass  # Feasibility only

        return Success(None)
    except Exception as e:
        return Failure(f"Error adding objective: {e!s}")


def extract_solution(
    solver: cp_model.CpSolver,
    variables: Dict[str, Any],
    problem_vars: List[ORToolsVariable],
) -> Dict[str, Any]:
    """Extract solution values from the solver.

    Args:
        solver: The OR-Tools CpSolver
        variables: Dictionary of variable names to OR-Tools variables
        problem_vars: List of original variable definitions

    Returns:
        Dictionary of variable names to their solution values
    """
    solution: Dict[str, Any] = {}

    for var in problem_vars:
        name = var.name
        if var.shape:
            # Handle array variables using nested lists
            shape = var.shape
            array: List[Any] = []
            for idx in range(shape[0]):
                if len(shape) == 1:
                    array.append(solver.Value(variables[name][idx]))
                else:
                    row: List[Any] = []
                    for jdx in range(shape[1]):
                        if len(shape) == 2:
                            row.append(solver.Value(variables[name][idx][jdx]))
                        else:
                            plane: List[Any] = []
                            for kdx in range(shape[2]):
                                plane.append(
                                    solver.Value(variables[name][idx][jdx][kdx])
                                )
                            row.append(plane)
                    array.append(row)
            solution[name] = array
        else:
            # Handle scalar variables
            solution[name] = solver.Value(variables[name])

    return solution


def solve_ortools_problem(problem: ORToolsProblem) -> Result[ORToolsSolution, str]:
    """Solve an OR-Tools problem and return the solution.

    Args:
        problem: The problem definition

    Returns:
        Result containing a Solution or an error message
    """
    try:
        # Validate problem
        if not problem.validate():
            return Failure("Invalid problem definition")

        start_time = time.time()
        
        # Create model
        model = cp_model.CpModel()

        # Create variables
        vars_result = create_variables(model, problem.variables)
        if isinstance(vars_result, Failure):
            return vars_result

        variables_dict, globals_dict = vars_result.unwrap()

        # Create constraints
        constraints_result = create_constraints(
            model, problem.constraints, variables_dict, globals_dict
        )
        if isinstance(constraints_result, Failure):
            return constraints_result

        # Add objective
        objective_result = add_objective(
            model, problem.objective, variables_dict, globals_dict
        )
        if isinstance(objective_result, Failure):
            return objective_result

        # Create solver
        solver = cp_model.CpSolver()

        # Add parameters if provided
        if problem.parameters:
            for key, value in problem.parameters.items():
                if hasattr(solver.parameters, key):
                    setattr(solver.parameters, key, value)

        # Set time limit if specified
        if problem.time_limit:
            solver.parameters.max_time_in_seconds = problem.time_limit

        # Solve the problem
        status = solver.Solve(model)
        solve_time = time.time() - start_time

        # Extract solution
        is_feasible = status in [
            cp_model.OPTIMAL,
            cp_model.FEASIBLE,
        ]
        values = (
            extract_solution(solver, variables_dict, problem.variables)
            if is_feasible
            else {}
        )

        # Create solver statistics
        statistics = {
            "num_conflicts": solver.NumConflicts(),
            "num_branches": solver.NumBranches(),
            "wall_time": solver.WallTime(),
            "solve_time": solve_time,
        }

        return Success(
            ORToolsSolution(
                values=values,
                is_feasible=is_feasible,
                status=solver.StatusName(status),
                objective_value=(
                    solver.ObjectiveValue()
                    if is_feasible and problem.objective
                    else None
                ),
                solve_time=solve_time,
                statistics=statistics,
            )
        )
    except Exception as e:
        return Failure(f"Error solving problem: {e!s}")
