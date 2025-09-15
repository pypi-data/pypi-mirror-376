from hjb_solver.config import *
from hjb_solver.core.abstraction import D, P
from hjb_solver.core.mixin import BoundarySearchMixin
from hjb_solver.imports import *


@dataclass
class AbstractSolver(BoundarySearchMixin[P, D], Generic[P, D], ABC):
    """
    (You should implement a concrete subclass of this abstract solver)
    ------------------------------------------------------------------

    Abstract base class for solving HJB equations.

    This class provides a framework for solving Hamilton-Jacobi-Bellman (HJB) equations
    using policy iteration and boundary search methods.

    It is designed to be extended by concrete solver implementations
    that define specific model parameters, policy update methods, and HJB residual calculations.

    Notes
    -----
    - You should firstly implement two concrete subclasses for `AbstractParameter` and `AbstractBoundary`, respectively.
    - You `must` implement the following abstract methods:
        - `initialize_policy()`: to provide an initial guess for the policy.
        - `update_policy()`: to update the policy based on the current value function.
        - `hjb_residual()`: to compute the residual of the HJB equation.
    - You `may` also override the following methods for custom behavior:
        - `update_boundary()`: to update boundary values based on the current solution.
        - `bisection_boundary_error()`: to compute the error for boundary search.

    Methods
    -------
    - `solve()`: Solve the HJB equation using policy iteration for some specific boundary values.
        - This method returns a `Info` object containing the solution and convergence information.
        - `Info` object contains:
            - `converged`: Whether the solver converged.
            - `iterations`: Number of iterations performed.
            - `final_error`: Final error reported by the solver.
            - `message`: Additional information about the solver run.
            - `time`: Time taken for the solver run.
    - `boundary_search()`: Perform a search over boundary values to satisfy boundary conditions.
        - This method alternates between solving the HJB equation and updating the boundary values until convergence.
        - `update_boundary()` should be implemented in subclasses.
    - `bisection_search()`: Perform a bisection search to find boundary values that satisfy a specified condition.
        - If `update_boundary()` is implemented, then it will be used to update the boundary values during the search.
        - `bisection_boundary_error()` should be implemented in subclasses.

    Properties
    ----------
    solution : `Solution`
        The solution of the HJB equation, including value function, policy, and grid.
        You should access the solution only after calling `solve()`, `boundary_search()` or `bisection_search()`.
        The `Solution` object contains:
        - `p`: Model parameters.
        - `boundary`: Boundary conditions.
        - `boundary_derivative`: Derivatives at the boundaries.
        - `s`: Grid points for the state variable.
        - `v`: Value function evaluated at the grid points.
        - `dv`: First derivative of the value function at the grid points.
        - `d2v`: Second derivative of the value function at the grid points.
        - `policy`: Optimal policy evaluated at the grid points.
        - `df`: Pandas DataFrame representation of the solution.
    boundary_derivative : `BoundaryDerivative`
        Derivatives at the boundaries of the state variable.
        Contains:
        - `dv_left`: First derivative at the left boundary.
        - `dv_right`: First derivative at the right boundary.
        - `d2v_left`: Second derivative at the left boundary.
        - `d2v_right`: Second derivative at the right boundary.


    Parameters
    ----------
    p : Parameter
        Model parameters (subclass of AbstractParameter).
    boundary : AbstractBoundary[P]
        Boundary values (subclass of AbstractBoundary).

    number : int, optional
        Number of grid points for the state variable (default is 1000).
    interval : float, optional (Not required if number is provided, and not recommended)
        Grid spacing for the state variable (default is None).

    policy_max_iter : int, optional
        Maximum number of policy iteration steps (default is 50).
    policy_tol : float, optional
        Tolerance for policy convergence (default is 1e-6).
    policy_patience : int, optional
        Number of iterations to wait for improvement before stopping policy iteration (default is 10).

    guess_policy : bool, optional
        Whether to use an initial guess for the policy (default is False).
        If False, the solver will use `update_policy()` method to initialize the policy.
        If True, the solver will use `initialize_policy()` method to initialize the policy.

    value_max_iter : int, optional
        Maximum number of value function update steps (default is 20).
    value_tol : float, optional
        Tolerance for value function convergence (default is 1e-6).
    value_patience : int, optional
        Number of iterations to wait for improvement before stopping value updates (default is 5).

    boundary_max_iter : int, optional
        Maximum number of boundary update steps (default is 20).
    boundary_patience : int, optional
        Number of iterations to wait for improvement before stopping boundary updates (default is 5).
    boundary_tol : float, optional
        Tolerance for boundary convergence (default is 1e-4).

    Examples
    --------
    ```python
    class Solver(AbstractSolver[Parameter, PolicyDict]):

        def initialize_policy(self) -> PolicyDict:
            # Provide an initial guess for the policy
            ...
            return PolicyDict(...)

        def update_policy(
            self, v: Array, dv: Array, d2v: Array, s: Array, p: Parameter
        ) -> PolicyDict:
            # Update the policy based on the current value function
            ...
            return PolicyDict(...)

        @staticmethod
        def hjb_residual(
            v: Array, dv: Array, d2v: Array, s: Array, policy: PolicyDict, p: Parameter
        ) -> Array:
            # Compute the residual of the HJB equation
            ...
            return residual

        def update_boundary(self, solution) -> tuple[dict, float]:
            # Update boundary values based on the current solution
            ...
            return boundary_dict, error

        def bisection_boundary_error(self, solution) -> float:
            # Compute the error for boundary search
            ...
            return error
    ```
    """

    def __post_init__(self):
        """Initialize the solver by setting up the grid, policy, and JIT-compiled functions."""
        self._init()
        self.jitted_value_update_func = self._create_value_update_func()


if __name__ == "__main__":
    ...
