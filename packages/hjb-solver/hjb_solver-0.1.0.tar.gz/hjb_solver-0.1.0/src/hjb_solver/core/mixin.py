from hjb_solver.config import *
from hjb_solver.core.abstraction import AbstractBoundary, D, P
from hjb_solver.core.structure import BoundaryDerivative, Info, Solution
from hjb_solver.imports import *
from hjb_solver.utils import get_return_dict_keys


@dataclass
class GridMixin(Generic[P]):
    """
    Mixin that provides a uniform one-dimensional computational grid.

    This mixin stores the spatial grid for the state variable `s`
    and a corresponding discretized value function `v`.

    It also provides "interior" views (i.e., `s_inter` and `v_inter`) that exclude the boundary points,
    which are commonly used when constructing finite-difference stencils or applying boundary conditions.

    Notes
    -----
    - The parameter `number` is recommended rather than `interval` to ensure JIT-compatibility.

    Parameters
    ----------
    p : Parameter
        Model parameters (subclass of AbstractParameter).
    boundary : AbstractBoundary[P]
        Boundary conditions for the state variable and value function.
    number : int
        Number of grid points N (including boundaries).
    interval : Optional[float]
        Grid spacing (step size) used to construct the uniform grid.
        If `None`, the grid spacing is automatically determined.

    Attributes
    ----------
    h : float
        Grid spacing (step size) used to construct the uniform grid.

    s_min : float
        Minimum boundary for the state variable.
    s_max : float
        Maximum boundary for the state variable.
    v_left : float
        Value function at the left boundary (corresponding to `s_min`).
    v_right : float
        Value function at the right boundary (corresponding to `s_max`).

    s : Float[Array, "N"]
        Full grid for the state variable, including both boundary points;
        shape (N, ).
    s_inter : Float[Array, "N-2"]
        Interior grid points for `s`, excluding the first and last elements;
        shape (N-2, ).
    v : Float[Array, "N"]
        Grid of values for the value function `v`, defined on the same nodes as `s`;
        shape (N, ).
        Initialized by _setup_grid using linear interpolation between `v_left` and `v_right`.
    v_inter : Float[Array, "N-2"]
        Interior values of `v`, excluding boundary values;
        shape (N-2, ).
    """

    p: P = field(repr=False)
    boundary: AbstractBoundary[P] = field(repr=True)

    number: int = 1000
    interval: Optional[float] = None  # 1e-4

    h: float = field(init=False)

    s_min: float = field(init=False, repr=False)
    s_max: float = field(init=False, repr=False)
    v_left: float = field(init=False, repr=False)
    v_right: float = field(init=False, repr=False)

    s: Float[Array, "N"] = field(init=False, repr=False)
    s_inter: Float[Array, "N-2"] = field(init=False, repr=False)
    v: Float[Array, "N"] = field(init=False, repr=False)
    v_inter: Float[Array, "N-2"] = field(init=False, repr=False)

    def _setup_grid(self):
        """
        Set up the computational grid for the state variable `s` and the value function `v`.

        Parameters
        ----------
        s_min : float
            Minimum boundary for the state variable `s`.
        s_max : float
            Maximum boundary for the state variable `s`.
        v_left : float
            Value function at the left boundary (corresponding to `s_min`).
        v_right : float
            Value function at the right boundary (corresponding to `s_max`).
        """
        self.s_min, self.s_max, self.v_left, self.v_right = self.boundary.get_boundary()
        # Determine grid spacing
        if self.interval is None:
            self.s = jnp.linspace(self.s_min, self.s_max, self.number)
            self.h = (self.s_max - self.s_min) / (self.number - 1)
        else:
            self.h = self.interval
            self.s = jnp.arange(self.s_min, self.s_max + self.h, self.h)
        self.number = self.s.size
        # Interior grid points (excluding boundaries)
        self.s_inter = self.s[1:-1]
        # Number of grid points
        # Create grid for value function `v`
        self.v = jnp.linspace(self.v_left, self.v_right, self.number)
        # Interior grid points for value function `v`
        self.v_inter = self.v[1:-1]


@dataclass
class NewtonSolver(Generic[P]):
    """
    This mixin provides a Newton solver for policy functions.

    Parameters
    ----------
    newton_max_iter : int
        Maximum number of Newton iterations to perform.
    newton_tol : float
        Tolerance level for convergence checking.

    Methods
    -------
    _newton_solve
        Solve for the policy function using Newton's method.

    Notes
    -----
    - The `_newton_solve` method performs a fixed number of iterations defined by `self.newton_max_iter`.
      This approach is more JIT-friendly compared to a convergence-based stopping criterion.
    - The convergence is monitored by the norm of the update step.
    """

    newton_max_iter: int = 5
    newton_tol: float = 1e-10

    def _newton_solve(
        self,
        initial_guess: Float[Array, "N-2"],
        policy_foc: Callable,
        v: Float[Array, "N-2"],
        dv: Float[Array, "N-2"],
        d2v: Float[Array, "N-2"],
        s: Float[Array, "N-2"],
        other_policy: Optional[dict[str, Float[Array, "N-2"]]] = None,
    ) -> tuple[Float[Array, "N-2"], float]:
        """
        Solve for the policy function using Newton's method.

        Notes
        -----
        - It performs a fixed number of iterations defined by `self.newton_max_iter`.
          Compare to a convergence-based stopping criterion, this approach is more JIT-friendly.
        - The convergence is monitored by the norm of the update step.
        - The `policy_foc` function should return the residual of the first-order condition:
            ```python
            def policy_foc(policy_val, v, dv, d2v, s, other_policy):
                # Compute the first-order condition
                return foc_residual
            ```
            You can change the specific naming of the parameters,
            but you need to maintain the number and order of the parameters consistent with those in the example.
        Parameters
        ----------
        initial_guess : Float[Array, "N-2"]
            Initial guess for the policy function.
        policy_foc : Callable
            Function representing the first-order condition of the policy.
        v : Float[Array, "N-2"]
            Current value function.
        dv : Float[Array, "N-2"]
            First derivative of the value function.
        d2v : Float[Array, "N-2"]
            Second derivative of the value function.
        s : Float[Array, "N-2"]
            Current state vector.
        other_policy : dict[str, Float[Array, "N-2"]]
            Other policy functions needed for the FOC.

        Returns
        -------
        new_policy : Float[Array, "N-2"]
            Updated policy function after applying Newton's method.
        newton_error : float
            Norm of the difference between the last two iterations, used for convergence checking.
        """
        # JIT compile the function to compute the policy FOC and its gradient
        value_and_grad_foc = value_and_grad(policy_foc, argnums=0)

        @jit
        def jit_newton_solve(
            guess_val: Float[Array, "N-2"],
            v: Float[Array, "N-2"],
            dv: Float[Array, "N-2"],
            d2v: Float[Array, "N-2"],
            s: Float[Array, "N-2"],
            other_policy: Optional[dict[str, Float[Array, "N-2"]]] = None,
        ) -> tuple[Float[Array, "N-2"], Array]:
            """JIT-compiled Newton solver for policy functions."""

            # Define a single Newton iteration step
            def step(
                old_val: Float[Array, "N-2"], _
            ) -> tuple[Float[Array, "N-2"], Array]:
                # Calculate function value and its gradient
                f_val, f_prime = value_and_grad_foc(
                    old_val, v, dv, d2v, s, other_policy
                )
                # Update using Newton's method
                update = f_val / f_prime
                # Compute the difference and its norm
                return (
                    (new_val := old_val - update),
                    (diff := jnp.linalg.norm(update)),
                )

            # Use jax.lax.scan to efficiently perform a fixed number of iterations
            final_val, diff = lax.scan(
                step,
                guess_val,
                None,
                length=self.newton_max_iter,
            )
            return final_val, diff

        #   Vectorize the solver to run simultaneously across all state points
        vectorized_solver: Callable = vmap(
            jit_newton_solve,
            in_axes=(0, 0, 0, 0, 0, 0),
        )
        new_policy, diff = vectorized_solver(initial_guess, v, dv, d2v, s, other_policy)
        return (
            new_policy,
            (newton_error := jnp.linalg.norm(diff[:, -1])),
        )


@dataclass
class PolicyMixin(NewtonSolver[P], Generic[P, D]):
    """
    This mixin manages the policy functions (control variables) used in the HJB solver.

    It requires subclasses to implement methods for initializing and updating the policy.

    Parameters
    ----------
    guess_policy : bool
        Whether to use the initial policy guess provided by the user.
        If `False`, the solver will perform an initial policy improvement step before starting iterations.
    newton_max_iter : int
        Maximum number of Newton iterations to perform when solving for policy functions.
    newton_tol : float
        Tolerance level for convergence checking in the Newton solver.

    Attributes
    ----------
    policy : D
        Current policy functions stored in a dictionary-like container (PolicyDict).
    policy_inter : dict[str, Float[Array, "N-2"]]
        Interior values of the policy functions, excluding boundary points.
    policy_names : list[str]
        List of policy variable names (keys of the `policy` dictionary).

    Methods
    -------
    initialize_policy
        Abstract method to create an initial policy guess.
    update_policy
        Abstract method to update the policy based on the current value function and its derivatives.
    solve_policy
        Solve for a specific policy using the provided first-order condition function.

    """

    guess_policy: bool = False

    policy: D = field(init=False, repr=False)
    policy_names: list[str] = field(init=False)

    @abstractmethod
    def initialize_policy(self) -> D:
        """
        (The NECESSARY method you need to implement)
        --------------------------------------------

        Create an initial policy guess for the solver.

        This abstract method should be implemented by subclasses to
        provide an initial policy for the control variables used by the HJB solver.

        Notes
        -----
        - The method is called once during solver setup.
        - The solver expects every policy variable it references during iteration
          to be present in the returned mapping.
          Failing to provide required keys may raise an error when the solver starts.
        - The returned object must be a dictionary-like mapping (type PolicyDict)
          that contains entries for every policy variable the solver expects.
        - If you have a meaningful initial guess for the policy, you should return it here,
          and the solver will use it as the starting point when `guess_policy` is `True`.
        - If you do not have a meaningful initial guess,
          you can set `guess_policy` to `False` in the solver configuration.
          Then the solver will ignore this initial guess
          and perform an initial policy improvement step before starting iterations.

        Availability
        -----------
        Implementations may freely use the following instance attributes:
        - 'self.p' : Parameter
        - `self.s` : Float[Array, "N"]
        - `self.v` : Float[Array, "N"]
        - `self.number` : int

        Returns
        -------
        A dictionary-like container (PolicyDict) that maps policy variable names to arrays of values.
        Each array should have a shape compatible with the solver's state grid
        (typically the same shape as `self.s` or a 1-D array of length `self.number`).


        Examples
        --------
        ```python
        class PolicyDict(AbstractPolicyDict):
            control_var1: Float[Array, "N"]
            control_var2: Float[Array, "N"]

        def initialize_policy(self) -> PolicyDict:
            control_var1_val: Float[Array, "N"] = ...  # some computation using self.s, self.v, self.p, etc.
            return PolicyDict(
                control_var1=jnp.full_like(self.s, control_var1_val),
                control_var2=jnp.ones(self.number),
            )
        ```
        """

    def _setup_policy(self):
        """Set up the initial policy"""
        self.policy = self.initialize_policy()
        self.policy_inter = self.get_policy_interior()
        self.policy_names = list(self.policy.keys())

    @abstractmethod
    def update_policy(
        self,
        v: Float[Array, "N-2"],
        dv: Float[Array, "N-2"],
        d2v: Float[Array, "N-2"],
        s: Float[Array, "N-2"],
        p: P,
    ) -> D:
        """
        (The NECESSARY method you need to implement)
        --------------------------------------------

        Update the policy variables using the current value function and its derivatives.

        Notes
        -----
        - This abstract method must be implemented by subclasses to compute the control/policy variables
          given the current value function and its first and second derivatives on the interior grid.
        - Implementations may use closed-form expressions when available
          or solve first-order conditions (FOCs) numerically (with `self.solve_policy`).
            - When solving FOCs numerically, the FOC function passed to `self.solve_policy` should have the `signature`
                ```python
                def foc(policy_val, v, dv, d2v, s, other_policy):
                    foc_residual = ...  # compute the FOC residual
                    return foc_residual
                ```
            Here, `policy_val` is the candidate value for the policy variable being solved for,
            `other_policy` is a dictionary of the other current policy variables.
            You can change the specific naming of the parameters,
            but you need to maintain the number and order of the parameters consistent with those in the example.
            The FOC function should return the residual of the first-order condition evaluated at each interior grid point.
        - Implementations should ensure array shapes and indexing correspond to the interior nodes only.
        - The returned `PolicyDict` must have the same keys as the initial policy provided when the solver was constructed.

        Parameters
        ----------
        v : Float[Array, "N-2"]
            Interior values of the value function (1-D array of length N-2).
        dv : Float[Array, "N-2"]
            First derivative of the value function on the interior grid (1-D array of length N-2).
        d2v : Float[Array, "N-2"]
            Second derivative of the value function on the interior grid (1-D array of length N-2).
        s : Float[Array, "N-2"]
            Interior values of the state variable (1-D array of length N-2).
        p : Parameter
            Model parameters.

        Returns
        -------
        PolicyDict
            A mapping from policy variable names (strings) to arrays (typically 1-D arrays of length N-2)
            containing the updated policy values on the interior grid.
            The returned PolicyDict must have the same keys as the initial policy .

        Example
        -------
            ```python
            def update_policy(
                self, v: Array, dv: Array, d2v: Array, s: Array, p: Parameter
            ) -> PolicyDict:

                new_control_var1 = (some closed-form solution)

                def control_var2_foc(
                    policy_val: Array,
                    v: Array,
                    dv: Array,
                    d2v: Array,
                    s: Array,
                    other_policy: dict[str, Array],
                ):
                    # You can also use model parameters `p` as needed
                    foc_residual = ...  # compute the FOC residual
                    return foc_residual
                other_policy = {
                    "control_var1": new_control_var1
                }
                new_control_var2, diff_norm2 = self.solve_policy(
                    "control_var2", control_var2_foc, v, dv, d2v, s, other_policy
                )

                return PolicyDict(
                    control_var1 = new_control_var1,
                    control_var2 = new_control_var2,
                )
        """

    def solve_policy(
        self,
        policy_name: str,
        policy_foc: Callable,
        v: Float[Array, "N-2"],
        dv: Float[Array, "N-2"],
        d2v: Float[Array, "N-2"],
        s: Float[Array, "N-2"],
        other_policy: Optional[dict[str, Float[Array, "N-2"]]] = None,
    ):
        """
        Solve for a specific policy using the provided first-order condition (`policy_foc`) function.

        This method uses Newton's iteration to find the root of the FOC.

        Notes
        -----
        - The `policy_foc` function should have the signature:
            ```python
            def policy_foc(policy_val, v, dv, d2v, s, other_policy):
                # Compute the first-order condition
                # You can also use model parameters `p` as needed
                return foc_residual
            ```
            Here, `policy_val` is the candidate value for the policy variable being solved for,
            `other_policy` is a dictionary of the other current policy variables.
            You can change the specific naming of the parameters,
            but you need to maintain the number and order of the parameters consistent with those in the example.
            The FOC function should return the residual of the first-order condition evaluated at each interior grid point.
        - The method checks the convergence of the Newton iteration using `self.newton_tol`.
        - If the Newton iteration does not converge within the specified tolerance,
          a warning is logged, but the method still returns the last computed policy.

        Parameters
        ----------
        policy_name : str
            Name of the policy variable to solve for.
        policy_foc : Callable
            Function representing the first-order condition of the policy.
        v : Float[Array, "N-2"]
            Current value function.
        dv : Float[Array, "N-2"]
            First derivative of the value function.
        d2v : Float[Array, "N-2"]
            Second derivative of the value function.
        s : Float[Array, "N-2"]
            Current state vector.
        other_policy : dict[str, Float[Array, "N-2"]], optional
            Other policy functions needed for the FOC.

        Returns
        -------
        new_policy : Float[Array, "N-2"]
            Updated policy function after applying Newton's method.
        newton_error : float
            Norm of the difference between the last two iterations, used for convergence checking.
        """

        new_policy, newton_error = self._newton_solve(
            initial_guess=self.policy[policy_name][1:-1],
            policy_foc=policy_foc,
            v=v,
            dv=dv,
            d2v=d2v,
            s=s,
            other_policy=other_policy,
        )
        if newton_error > self.newton_tol:
            logger.warning(
                f"\nNewton solver for policy '{policy_name}' did not converge within the tolerance {self.newton_tol}. "
                f"\nFinal error: {newton_error}."
            )
        return new_policy

    def get_policy_interior(self) -> dict[str, Float[Array, "N-2"]]:
        """
        Extract the interior values of the policy dictionary.

        Returns
        -------
        dict[str, Float[Array, "N-2"]]
            A dictionary containing the interior policy values.

        Returns
        -------
        dict[str, Float[Array, "N-2"]]
            A dictionary containing the interior policy values.
            Each array has the shape (N-2,), excluding the boundary points.
            ```python
            { 'policy1': Array([a2, a3, ..., aN-2, aN-1]),
              'policy2': Array([b2, b3, ..., bN-2, bN-1]),
             ...
            }
            ```
        """
        return {
            key: value[1:-1]  # pyright: ignore[reportIndexIssue]
            for key, value in self.policy.items()
        }


class CalculationMixin:
    """
    Mixin class for performing some calculations.

    Methods
    -------
    _cal_derivatives:
        Compute first and second central finite differences on an interior grid.
    _cal_derivatives_from_slice:
        Compute first and second central finite differences from 3-point slices.
    extrapolate:
        Linearly extrapolate boundaries from the first two and last two interior points.
    """

    @staticmethod
    def _cal_derivatives(
        v_inter: Float[Array, "N-2"],
        v_left: float,
        v_right: float,
        h: float,
    ) -> tuple[Float[Array, "N-2"], Float[Array, "N-2"]]:
        """
        Compute first and second central finite differences on an interior grid.

        Parameters
        ----------
        v_inter : Array, shape (N-2,)
            Function values at the interior grid points.
        v_left : float
            Boundary value at the left end (corresponds to index 0 of the full grid).
        v_right : float
            Boundary value at the right end (corresponds to last index of the full grid).
        h : float
            Grid spacing.

        Returns
        -------
        dv, d2v : tuple of Arrays
        dv : Array, shape (N-2,)
            First derivative at interior points.
        d2v : Array, shape (N-2,)
            Second derivative at interior points.

        Notes
        -----
        The full grid is assumed to be [v_left, *v_inter, v_right]. For interior index i
        (corresponding to v_inter[i]), neighbors are taken from that full grid.
        """
        # Construct full grid by appending boundary values
        v_full = jnp.concatenate([jnp.array([v_left]), v_inter, jnp.array([v_right])])
        # Neighboring points
        v_im1 = v_full[:-2]
        v_ip1 = v_full[2:]
        # Central differences
        return (dv := (v_ip1 - v_im1) / (2 * h)), (
            d2v := (v_ip1 - 2 * v_inter + v_im1) / (h**2)
        )

    @staticmethod
    def _cal_derivatives_from_slice(
        v_slice: Float[Array, "N-2 3"], h: float
    ) -> tuple[Float[Array, "N-2"], Float[Array, "N-2"]]:
        """
        Compute first and second central finite differences from 3-point slices.

        Parameters
        ----------
        v_slice : Array, shape (N-2, 3)
            Array whose rows correspond to v_{i-1}, v_i, v_{i+1} for each interior point.
        h : float
            Grid spacing.

        Returns
        -------
        dv, d2v : tuple of Arrays
        dv : Array, shape (N-2,)
            First derivative at interior points.
        d2v : Array, shape (N-2,)
            Second derivative at interior points.
        """
        v_im1, v_i, v_ip1 = v_slice
        return (dv := (v_ip1 - v_im1) / (2 * h)), (
            d2v := (v_ip1 - 2 * v_i + v_im1) / (h**2)
        )

    @staticmethod
    @jax.jit
    def extrapolate(
        interior_vals: Float[Array, "N-2"],
    ) -> Float[Array, "N"]:
        """
        Linearly extrapolate boundaries from the first two and last two interior points.

        ```
        v1 = 2*v2 - v3
        vN = 2*vN-1 - vN-2
        ```

        Notes
        -----
        - Assumes uniform grid spacing at the boundaries. Thus interval `h` should be small enough.
        - The input `interior_vals` should have at least two elements to perform extrapolation.

        Parameters
        ----------
        interior_vals: Float[Array, "N-2"]
            Array of interior values (size N-2).

        Returns
        -------
        full_vals: Float[Array, "N"]
            Full array including extrapolated boundary values (size N).

        Example
        -------
            ```python
            interior_vals = jnp.array([v2, v3, ..., vN-1])
            full_vals = extrapolate(interior_vals)
            full_vals = jnp.array([v1, v2, v3, ..., vN-1, vN])
            ```
        """
        return jnp.concatenate(
            (
                jnp.array([2 * interior_vals[0] - interior_vals[1]]),
                interior_vals,
                jnp.array([2 * interior_vals[-1] - interior_vals[-2]]),
            )
        )


@dataclass
class PolicyEvaluationMixin(
    CalculationMixin,
    PolicyMixin[P, D],
    GridMixin,
    Generic[P, D],
):
    """
    Mixin that provides policy evaluation capabilities for solving HJB equations.

    Parameters
    ----------
    value_max_iter : int
        Maximum number of iterations for the value function update.
    value_tol : float
        Tolerance level for convergence checking of the value function.
    value_patience : int
        Number of consecutive iterations with improvement below `value_tol` before stopping.

    Methods
    -------
    hjb_residual
        Abstract method to compute the HJB residual.
    _create_value_update_func
        Create a jitted function to perform a single Newton update step for the value function.
    _policy_evaluation
        Perform policy evaluation to update the value function.
    """

    value_max_iter: int = 20
    value_tol: float = 1e-6
    value_patience: int = 5

    @staticmethod
    @abstractmethod
    def hjb_residual(
        v: Float[Array, "N-2"],
        dv: Float[Array, "N-2"],
        d2v: Float[Array, "N-2"],
        s: Float[Array, "N-2"],
        policy: dict[str, Float[Array, "N-2"]],
        p: P,
    ) -> float:
        """
        (The NECESSARY method you need to implement)
        --------------------------------------------

        Calculate the pointwise HJB residual on the interior grid.

        Notes
        -----
        - Keep the parameter order and return shape as specified; the solver expects this signature.
        - This is a `static` method and does not have access to instance attributes.

        Parameters
        ----------
        v : Float[Array, "N-2"]
            Value function evaluated at interior grid points.
        dv : Float[Array, "N-2"]
            First derivative of the value function at interior points.
        d2v : Float[Array, "N-2"]
            Second derivative of the value function at interior points.
        s : Float[Array, "N-2"]
            State variable values at interior grid points.
        policy : dict[str, Float[Array, "N-2"]]
            Mapping of policy variable names to their values on the interior grid.
        p : Parameter
            Model parameters.

        Returns
        -------
        Float[Array, "N-2"]
            HJB residual evaluated at each interior grid point.


        Example
        -------
        ```python
        @staticmethod # Make sure to include the @staticmethod decorator
        def hjb_residual(v, dv, d2v, s, policy, p):
            control1 = policy["control1"]
            ...
            # compute residual using v, dv, d2v, s, policy and parameters p
            residual = ...
            return residual
        ```
        """
        pass

    def _create_value_update_func(self) -> Callable:
        """
        Create a jitted function to perform a single Newton update step for the value function

        Returns
        -------
        Callable
            A jitted function that performs a single Newton update step for the value function.

        Notes
        -----
        - The returned function has the signature:
            ```python
            def value_update_step(
                v_inter: Float[Array, "N-2"],
                policy_inter: dict[str, Float[Array, "N-2"]],
                s_inter: Float[Array, "N-2"],
                v_left: float,
                v_right: float,
                h: float,
                p: P,
            ) -> tuple[Float[Array, "N-2"], float]:
            ```
            Here, `p` is fixed to `self.p` via `functools.partial`.
        """

        def residual_wrapper(
            v_slice: Float[Array, "N-2"],
            s_inter: Float[Array, "N-2"],
            policy: dict[str, Float[Array, "N-2"]],
            h: float,
            p: P,
        ) -> float:
            """
            Wrapper for HJB residual calculation.

            This wrapper takes the raw v_slice and internally
            calls the subclass method `hjb_residual` with the computed derivatives.
            """
            # Extract the center point values from the slice
            v = v_slice[1]
            # Compute derivatives using the slice
            dv, d2v = self._cal_derivatives_from_slice(v_slice, h)
            # Calculate the HJB residual using the subclass-implemented method
            return self.hjb_residual(v, dv, d2v, s_inter, policy, p)

        def _v_update_step(
            v_inter: Float[Array, "N-2"],
            policy_inter: dict[str, Float[Array, "N-2"]],
            s_inter: Float[Array, "N-2"],
            v_left: float,
            v_right: float,
            h: float,
            p: P,
        ):
            """
            Perform a single Newton update step for the value function on the interior grid.
            """
            # 1. Create all 3-point slices for interior points in a vectorized way.
            v_full = jnp.concatenate(
                [jnp.array([v_left]), v_inter, jnp.array([v_right])]
            )
            num_inter = len(v_inter)
            # Each slice corresponds to (v_{i-1}, v_i, v_{i+1}).
            v_slices = jax.vmap(lambda i: jax.lax.dynamic_slice(v_full, (i,), (3,)))(
                jnp.arange(num_inter)
            )

            # 2. Calculate all derivatives in a vectorized way.
            all_dv, all_d2v = jax.vmap(
                self._cal_derivatives_from_slice, in_axes=(0, None)
            )(v_slices, h)

            # 3. Calculate residuals for all interior points.
            policy_in_axes = jax.tree_util.tree_map(lambda _: 0, policy_inter)
            residuals = jax.vmap(
                self.hjb_residual,
                in_axes=(
                    0,
                    0,
                    0,
                    0,
                    policy_in_axes,
                    None,
                ),
            )(v_inter, all_dv, all_d2v, s_inter, policy_inter, p)

            # 4. Calculate the Jacobian of the wrapper function w.r.t v_slice.
            # This correctly captures dependencies on v_{i-1}, v_i, v_{i+1}.
            J_local_diagonals = jax.vmap(
                jax.jacfwd(residual_wrapper, argnums=0),
                in_axes=(0, 0, policy_in_axes, None, None),
            )(v_slices, s_inter, policy_inter, h, p)

            # 5. Extract the tridiagonal components from the Jacobian.
            # Each row of J_local_diagonals corresponds to the Jacobian of residual[i] w.r.t v_{i-1}, v_i, v_{i+1}.
            d = J_local_diagonals[:, 1]
            dl = jnp.concatenate([jnp.array([0.0]), J_local_diagonals[1:, 0]])
            du = jnp.concatenate([J_local_diagonals[:-1, 2], jnp.array([0.0])])

            # 6. Solve the linear system for the Newton update: dv, J = -residuals
            dv_update = jax.lax.linalg.tridiagonal_solve(
                dl, d, du, -residuals[:, None]  # pyright: ignore[reportIndexIssue]
            ).squeeze(axis=-1)

            return (v_inter_new := v_inter + dv_update), (
                update_error := jnp.linalg.norm(dv_update)
            )

        return jax.jit(partial(_v_update_step, p=self.p))

    def _policy_evaluation(self, jitted_value_update_func: Callable):
        """
        Evaluate the policy by performing a fixed-point iteration.

        Parameters
        ----------
        jitted_value_update_func : Callable
            A JIT-compiled function that performs a single value update step.
            This function is typically created by `self._create_value_update_func()`.

        Updates
        -------
        `self.v_inter` : Float[Array, "N-2"]
            Updated interior values of the value function after policy evaluation.

        Notes
        -----
        - The convergence is monitored by the improvement in the update error.
        """
        # Initialize variables for the fixed-point iteration.
        best_error = float("inf")
        patience_counter = 0
        # Perform the fixed-point iteration.
        for iter_num in range(self.value_max_iter):
            self.v_inter, update_error = jitted_value_update_func(
                v_inter=self.v_inter,
                # During each iteration, fix the policy and update the value function.
                policy_inter=self.policy_inter,
                s_inter=self.s_inter,
                v_left=self.v_left,
                v_right=self.v_right,
                h=self.h,
            )
            # Check for improvement and update patience counter.
            if update_error < best_error:
                best_error = update_error
                patience_counter = 0
            else:
                patience_counter += 1
            # Check for convergence or patience limit.
            if update_error < self.value_tol:
                # Converged
                break
            if patience_counter >= self.value_patience and iter_num > (
                self.value_patience * 2
            ):
                logger.warning(
                    f"\nValue function update stopped early at iteration {iter_num+1} due to lack of improvement."
                    f"\nBest error: {best_error:.2e}."
                )
                break
                # return True
        # return False


@dataclass
class PolicyIterationMixin(
    PolicyEvaluationMixin[P, D],
    Generic[P, D],
):
    """
    Mixin class to perform policy iteration for solving HJB equations.

    Parameters
    ----------
    policy_max_iter : int
        Maximum number of policy iteration steps to perform.
    policy_tol : float
        Tolerance level for convergence checking in the policy iteration.
    policy_patience : int
        Number of iterations to wait for improvement before stopping early.

    Attributes
    ----------
    jitted_value_update_func : Callable
        A JIT-compiled function for updating the value function, created by `_create_value_update_func()`.

    Methods
    -------
    _policy_iteration
        Perform policy iteration to find the optimal policy and value function.
    _init
        Initialize the grid and policy.
    solve
        Solve the HJB equation for a specific boundary setting using policy iteration.

    Properties
    ----------
    boundary_derivative
        Calculate and return the boundary condition derivatives as a BoundaryDerivative dataclass.
    solution
        Return the current solution as a Solution dataclass.
    """

    policy_max_iter: int = 50
    policy_tol: float = 1e-6
    policy_patience: int = 10

    jitted_value_update_func: Callable = field(init=False, repr=False)

    def derivatives(
        self,
    ) -> tuple[
        Float[Array, "N-2"],
        Float[Array, "N-2"],
    ]:
        """
        Calculate first and second derivatives using central differences.

        Returns
        -------
        tuple:
            - `dv_inter` (Float[Array, "N-2"]):
                First derivative of the value function.
            - `d2v_inter` (Float[Array, "N-2"]):
                Second derivative of the value function.

        """
        return self._cal_derivatives(self.v_inter, self.v_left, self.v_right, self.h)

    def _policy_iteration(self, solve_info: Info, progress_bar: bool = True):
        """
        Perform policy iteration to find the optimal policy and value function.

        Parameters
        ----------
        solve_info : Info
            An Info object to track the progress and convergence of the policy iteration.
        progress_bar : bool, optional
            Whether to display a progress bar during iterations. Default is True.

        Returns
        -------
        Info
            An Info object containing details about the convergence of the policy iteration.

        Notes
        -----
        - The method alternates between policy evaluation and policy improvement steps.
        - Convergence is checked based on the change in policy functions.
        - Early stopping is implemented if no improvement is observed over a number of iterations defined by `policy_patience`.
        """

        def _policy_improvement():
            """
            Update the policy based on the `self.update_policy` method.

            Returns
            -------
            bool
                True if the policy has converged, False otherwise.
            """
            dv_inter, d2v_inter = self.derivatives()
            old_policy_inter = self.policy_inter
            self.policy_inter = self.update_policy(
                v=self.v_inter,
                dv=dv_inter,
                d2v=d2v_inter,
                s=self.s_inter,
                p=self.p,
            )
            if (
                policy_change_error := float(
                    jnp.max(
                        jnp.array(
                            [
                                jnp.linalg.norm(
                                    old_policy_inter[key] - self.policy_inter[key]
                                )
                                for key in self.policy_names
                            ]
                        )
                    )
                )
            ) < self.policy_tol:
                solve_info.converged = True
                solve_info.message = "Policy iteration converged."

            solve_info.final_error = f"{policy_change_error:.2e}"
            return solve_info.converged

        # Set up the patience counter for early stopping.
        patience_counter = 0

        # If no initial guess is provided, perform an initial policy improvement
        if not self.guess_policy:
            _policy_improvement()

        # Perform policy iteration
        for iter_num in trange(
            self.policy_max_iter,
            desc="Policy Iteration",
            disable=not progress_bar,
        ):

            # 1. Policy Evaluation: Update the value function given the current policy
            self._policy_evaluation(self.jitted_value_update_func)

            # 2. Policy Improvement: Update the policy given the new value function
            last_error = float(solve_info.final_error)
            if policy_converged := _policy_improvement():
                # Check for convergence
                break

            # 3. Check for improvement in the policy change error
            if float(solve_info.final_error) < last_error:
                patience_counter = 0
            else:
                patience_counter += 1

            # 4. Early stopping if no improvement over several iterations
            if (patience_counter >= self.policy_patience) and (
                iter_num > (self.policy_patience * 2)
            ):
                # Early stopping
                solve_info.message = (
                    "Policy iteration stopped early due to lack of improvement."
                )
                logger.warning(
                    f"\nPolicy iteration stopped early at iteration {iter_num+1} due to lack of improvement."
                    f"\nBest error: {solve_info.final_error}."
                )
                break

        # Finalize the solution information
        solve_info.iterations = iter_num + 1
        solve_info.time = f"{(time.time() - solve_info.time):.2f} seconds"  # pyright: ignore[reportOperatorIssue]
        return solve_info

    def _init(self):
        """
        (This method should be called after `self._create_value_update_func()`)

        Initialize the grid and policy.

        This method should be called when boundary values are updated.
        """
        self._setup_grid()
        self._setup_policy()

    def solve(self):
        """
        Solve the HJB equation using policy iteration.

        Returns
        -------
        Info
            An Info object containing details about the convergence of the policy iteration.
        """
        return self._policy_iteration(
            solve_info=Info(
                converged=False,
                iterations=0,
                final_error=float("inf"),
                message="Maximum policy iterations reached without convergence.",
                time=time.time(),
            ),
            progress_bar=True,
        )

    @property
    def boundary_derivative(self):
        """
        Calculate and return the boundary condition derivatives as a BoundaryDerivative dataclass.

        Returns
        -------
            `BoundaryDerivative`: A dataclass containing the derivatives at the boundaries.
            - `dv_left`: First derivative at the left boundary.
            - `d2v_left`: Second derivative at the left boundary.
            - `dv_right`: First derivative at the right boundary.
            - `d2v_right`: Second derivative at the right boundary.
        """
        # v'(s_max)
        dv_right = (self.v[-1] - self.v[-2]) / self.h
        # v''(s_max)
        d2v_right = (self.v[-1] - 2 * self.v[-2] + self.v[-3]) / (self.h**2)
        # v'(s_min)
        dv_left = (self.v[1] - self.v[0]) / self.h
        # v''(s_min)
        d2v_left = (self.v[2] - 2 * self.v[1] + self.v[0]) / (self.h**2)
        return BoundaryDerivative(
            dv_left=float(dv_left),
            d2v_left=float(d2v_left),
            dv_right=float(dv_right),
            d2v_right=float(d2v_right),
        )

    @property
    def solution(self) -> Solution[P, D]:
        """
        Construct and return the full solution including value function, its derivatives, and policy functions.

        Returns
        -------
        `Solution`: A dataclass containing the full solution with attributes:
            - `p`: Model parameters.
            - `boundary`: Boundary values.
            - `boundary_derivative`: Derivatives at the boundaries.
            - `s`: State variable grid points.
            - `v`: Full value function including boundaries.
            - `dv`: First derivative of the value function.
            - `d2v`: Second derivative of the value function.
            - `policy`: Dictionary of policy functions including boundaries.
        """
        # Construct the full value function and its derivatives
        self.v = jnp.concatenate(
            (jnp.array([self.v_left]), self.v_inter, jnp.array([self.v_right]))
        )
        dv_inter, d2v_inter = self.derivatives()
        self.dv = self.extrapolate(dv_inter)
        self.d2v = self.extrapolate(d2v_inter)
        # Construct the full policy functions
        for policy_name, policy_inter in self.policy_inter.items():
            policy_full = self.extrapolate(policy_inter)
            setattr(self, policy_name, policy_full)
            self.policy[policy_name] = policy_full
        return Solution(
            p=self.p,
            boundary=self.boundary,
            boundary_derivative=self.boundary_derivative,
            s=self.s,
            v=self.v,
            dv=self.dv,
            d2v=self.d2v,
            policy=self.policy,
        )


@dataclass
class BoundarySearchMixin(
    PolicyIterationMixin[P, D],
    Generic[P, D],
):
    """
    Mixin class for searching optimal boundary values.

    Parameters
    ----------
    boundary_max_iter : int, default 20
        Maximum number of boundary search iterations.
    boundary_tol : float, default 1e-4
        Tolerance for boundary condition convergence.
    boundary_patience : int, default 5
        Number of iterations to wait for improvement before stopping early.

    Notes
    -----
    - There are two methods to search for optimal boundary values:
        1. `boundary_search`: Uses the `update_boundary` method to iteratively update boundary values.
        2. `bisection_search`: Uses bisection to find a boundary value for a specified boundary condition.
    - If both methods are specified, `bisection_search` will be executed in the outer loop,
        and `boundary_search` will be called within it when the specified boundary is updated
    """

    boundary_max_iter: int = 20
    boundary_tol: float = 1e-4
    boundary_patience: int = 5

    bisection_search_boundary: Optional[
        Literal["s_min", "s_max", "v_left", "v_right"]
    ] = field(init=False, repr=False, default=None)

    _repeated_jit_compiled: bool = field(init=False, repr=False, default=False)

    def update_boundary(
        self, solution: Solution[P, D]
    ) -> tuple[dict[Literal["s_min", "s_max", "v_left", "v_right"], float], float]:
        """
        (Optional method you may implement)
        -----------------------------------

        Update boundary values based on the current solution.

        Notes
        -----
        - This method is optional; if not implemented, the solver will keep the boundary values fixed.
        - If implemented, the method should return a dictionary with any of the keys:
          's_min', 's_max', 'v_left', 'v_right' to update the corresponding boundary values.
        - The method should also return a float representing the error in the boundary condition.
        - The solver will use the returned boundary values in the next iteration.
        - The error can be used to monitor convergence of the boundary conditions.
        - These properties and parameters can utilize:
          - The `solution` parameter to access the current value function, its derivatives and policy function.
          - Instance attributes such as `self.s`, `self.v`, `self.dv`, `self.d2v`, etc.
          - The `self.boundary` attribute to access the current boundary values
            or directly use `self.s_min`, `self.s_max`, `self.v_left`, `self.v_right`.
          - Model parameters via `self.p`.
          - Methods such as `self.boundary_derivatives`.

        Parameters
        ----------
        solution : Solution
            The current solution containing the value function and its derivatives.

        Returns
        -------
        tuple[dict[Literal["s_min", "s_max", "v_left", "v_right"], float], float]:
            - boundary_dict (dict[Literal["s_min", "s_max", "v_left", "v_right"], float]):
                A dictionary mapping boundary names to their values.
                Keys are 's_min', 's_max', 'v_left', 'v_right'.
                Values are floats representing the boundary values.
            - error (float):
                A float representing the error in the boundary condition.

        Example
        -------
        ```python
        # Don't forget to include the `solution` parameter
        def update_boundary(self, solution: Solution) -> tuple[dict, float]:
            # Example implementation that updates the left boundary value
            new_v_left = self.v_left + 1.0  # some logic
            boundary_dict = {'v_left': new_v_left}
            error = abs(new_v_left - self.v_left)  # some error metric
            return boundary_dict, error
        ```
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.update_boundary method not implemented."
        )

    def _setup_boundary_search(self) -> None:
        """
        Validate the keys returned by `update_boundary` and `bisection_search`

        Notes
        -----
        This method should be called before `boundary_search` and `bisection_search` method.
        """
        boundary_names: set[str] = cast(
            set[str],
            (
                get_return_dict_keys(
                    cls=self.__class__,
                    method_name="update_boundary",
                )
            ),
        )
        if self.bisection_search_boundary is not None:
            boundary_names.add(self.bisection_search_boundary)
        for name in boundary_names:
            if name not in {
                "s_min",
                "s_max",
                "v_left",
                "v_right",
            }:
                raise ValueError(
                    f"Invalid boundary in 'update_boundary' return or bisection search: {name}."
                    "\nAllowed boundaries are 's_min', 's_max', 'v_left', 'v_right'."
                )
            if name in self.boundary.dependent:
                raise ValueError(
                    f"{name} is a dependent boundary, which should not be actively updated!"
                )
                # If the grid shape has changed
        if self.interval is not None and (boundary_names & {"s_min", "s_max"}):
            self._repeated_jit_compiled = True
            # Re-setup the JIT-compiled function with new grid and boundary values
            logger.warning(
                f'\nThe "interval" parameter is set, and the grid shape has been changed.'
                f"\nThus the JIT-compiled function may re-setup with new grid and boundary values."
                f"\nThis may lead to repeated compilation and slow down the searching process."
            )

    def search_boundary(self) -> Info:
        """
        (To call this method, you should implement the `update_boundary` first)
        -----------------------------------------------------------------------

        Search for the optimal boundary values.

        This method alternates between solving the HJB equation and updating the boundary values until convergence.

        Notes
        -----
        - This method performs an outer loop of boundary search around the policy iteration.
        - It relies on the `update_boundary` method to get new boundary values and the associated error.
        - The method checks for convergence based on the boundary error returned by `update_boundary`.
        - If the grid shape changes due to boundary updates (when `self.interval` is set),
          the solver will be re-compiled in each iteration.
          This may lead to repeated JIT compilation and slow down the solving process.
          Consider setting `number` instead of `interval` to keep the grid fixed.
        - Early stopping is implemented if no improvement is observed over a number of iterations defined by `boundary_patience`.

        Returns
        -------
        Info
            An Info object summarizing the result of the boundary search.
        """
        self._setup_boundary_search()
        solve_info = self._search_boundary(
            solve_info=Info(
                converged=False,
                iterations=0,
                final_error=float("inf"),
                message="Maximum boundary search iterations reached without convergence.",
                time=time.time(),
            ),
            progress_bar=True,
        )
        if self._repeated_jit_compiled:
            logger.warning(
                f'\nThe "value_update_function" are compiled for {self.jitted_value_update_func._cache_size()} times.'
                '\nTry setting parameter "number" instead of "interval" to achieve faster solution speed. '
            )
        return solve_info

    def _search_boundary(self, solve_info: Info, progress_bar: bool = True) -> Info:
        """
        Search for the optimal boundary values.

        Parameters
        ----------
        solve_info : Info
            An Info object to track the progress and convergence of the boundary search.
        progress_bar : bool, optional
            Whether to display a progress bar during boundary search iterations. Default is True.

        Returns
        -------
        Info
            An Info object containing details about the convergence of the boundary search.
        """
        # Set up the patience counter for early stopping.
        patience_counter = 0
        best_error = float("inf")
        # Perform the boundary search
        for iter_num in trange(
            self.boundary_max_iter,
            desc="Boundary Search",
            disable=not progress_bar,
        ):
            # 1. Policy Iteration: Solve the HJB with current boundary values
            self._policy_iteration(
                solve_info=Info(
                    converged=False,
                    iterations=0,
                    final_error=float("inf"),
                    message="Maximum policy iterations reached without convergence.",
                    time=time.time(),
                ),
                progress_bar=False,
            )
            # 2. Update the boundary values based on the current solution
            boundary_dict, boundary_error = self.update_boundary(self.solution)
            # 3. Apply the updated boundary values
            (self.s_min, self.s_max, self.v_left, self.v_right) = (
                self.boundary.update_boundaries(boundary_dict=boundary_dict)
            )
            # 4. Check for convergence in boundary conditions
            if boundary_error < self.boundary_tol:
                solve_info.converged = True
                solve_info.message = "Boundary search converged."
                # solve_info.final_error = boundary_error
                break
            # 5. Re-setup the grid and policy
            self._init()
            # 6. Check for improvement and update patience counter
            if boundary_error < best_error:
                best_error = boundary_error
                patience_counter = 0
            else:
                patience_counter += 1
            # 7. Early stopping if no improvement over several iterations
            if (patience_counter >= self.boundary_patience) and (
                iter_num > (self.boundary_patience * 2)
            ):
                solve_info.message = (
                    "Boundary search stopped early due to lack of improvement."
                )
                # solve_info.final_error = boundary_error
                logger.warning(
                    f"\nBoundary search stopped early at iteration {iter_num+1} due to lack of improvement."
                    f"\nBest error: {best_error:.2e}."
                )
                # Early stopping
                break
        # Finalize the solution information
        solve_info.iterations = iter_num + 1
        solve_info.time = f"{time.time() - solve_info.time:.2f} seconds"  # pyright: ignore[reportOperatorIssue]
        solve_info.final_error = f"{boundary_error:.2e}"
        return solve_info

    def bisection_boundary_error(self, solution: Solution[P, D]) -> float:
        """
        (Optional method you may implement)
        -----------------------------------

        Calculate the error in boundary conditions for bisection search.

        Notes
        -----
        - These properties and parameters can utilize:
          - The `solution` parameter to access the current value function, its derivatives and policy function.
          - Instance attributes such as `self.s`, `self.v`, `self.dv`, `self.d2v`, etc.
          - The `self.boundary` attribute to access the current boundary values
            or directly use `self.s_min`, `self.s_max`, `self.v_left`, `self.v_right`.
          - Model parameters via `self.p`.
          - Methods such as `self.boundary_derivatives`.
        - The sign of the error should indicate the direction to adjust the boundary:
            - Positive error: Boundary value is too `high`, `decrease` the boundary value.
            - Negative error: Boundary value is too `low`, `increase` the boundary value.

                For example, if you are adjusting `s_max` based on a smooth pasting condition `d2v(s_max) = 0`.
                Assuming v(s) is monotonically increasing and concave (i.e., `dv>0, d2v < 0`).
                Then if `d2v(s_max) < 0`, it suggests that `s_max` is too low and should be increased.
                Thus the sign of the boundary error is the same as our definition error.
                You might define the error as
                    ```python
                    # # Don't forget to include the `solution` parameter
                    def bisection_boundary_error(self, solution) -> float:
                        error = solution.boundary_derivatives.d2v_right
                        # A simpler definition could be just
                        # error = self.d2v_right
                        return error
                    ```

        Parameters
        ----------
        solution : Solution
            The current solution containing the value function and its derivatives.


        Returns
        -------
        float
            A float representing the sign and error in the boundary condition.

        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.bisection_boundary_error method not implemented."
        )

    def bisection_search(
        self,
        boundary_name: Literal["s_min", "s_max", "v_left", "v_right"],
        low: float,
        high: float,
        max_iter: int = 30,
        patience: int = 5,
        tol: float = 1e-4,
        progress_bar: bool = True,
    ):
        """
        (This method requires the `bisection_boundary_error` method to be implemented)
        ------------------------------------------------------------------------------

        Perform bisection search on the specified boundary.

        Notes
        -----
        - The method performs a bisection search to find the boundary value that minimizes the boundary error.
        - The sign of the boundary error should indicate the direction to adjust the boundary:
            - `Positive` error: Boundary value is too `high`, `decrease` the boundary value.
            - `Negative` error: Boundary value is too `low`, `increase` the boundary value.
        - Early stopping is implemented if no improvement is observed over a number of iterations defined by `patience`.
        - If the grid shape changes due to boundary updates (when `self.interval` is set),
          the solver will be re-compiled in each iteration.
          This may lead to repeated JIT compilation and slow down the solving process.

        Parameters
        ----------
        boundary_name : Literal["s_min", "s_max", "v_left", "v_right"]
            The boundary to perform bisection search on.
        low : float
            The lower bound of the boundary search interval.
        high : float
            The upper bound of the boundary search interval.
        max_iter : int
            Maximum number of bisection iterations. Default is 30.
        patience : int
            Number of iterations to wait for improvement before stopping early. Default is 5.
        tol : float
            Tolerance for convergence in boundary error. Default is 1e-4.
        progress_bar : bool
            Whether to display a progress bar during bisection search. Default is True.

        Returns
        -------
        Info
            An Info object containing details about the convergence of the bisection search.

        """
        # Set up
        self.bisection_search_boundary = boundary_name
        self._setup_boundary_search()
        solve_info = Info(
            converged=False,
            iterations=0,
            final_error=float("inf"),
            message="Maximum boundary search iterations reached without convergence.",
            time=time.time(),
        )
        best_error = float("inf")
        patience_counter = 0
        if "update_boundary" not in self.__class__.__dict__:
            solve_func = self._policy_iteration
        else:
            solve_func = self._search_boundary
        for iter_num in trange(
            max_iter,
            desc=f"Bisection Search for {boundary_name}",
            disable=not progress_bar,
        ):
            # 1. Update boundary guess
            mid = (low + high) / 2
            (self.s_min, self.s_max, self.v_left, self.v_right) = (
                self.boundary.update_boundaries({boundary_name: mid})
            )
            # 2. Re-setup the grid and policy
            self._init()
            # 3. Solve the HJB with current boundary guess
            solve_func(
                solve_info=Info(
                    converged=False,
                    iterations=0,
                    final_error=float("inf"),
                    message="Maximum iterations reached without convergence.",
                    time=time.time(),
                ),
                progress_bar=False,
            )
            # 4. Calculate the boundary error at the current guess
            boundary_error = self.bisection_boundary_error(self.solution)
            # 5. Check for convergence
            if abs(boundary_error) < tol:
                solve_info.converged = True
                solve_info.message = "Bisection search converged."
                solve_info.final_error = abs(boundary_error)
                break
            # 6. Update the upper or lower bound
            if boundary_error > 0:
                high = mid
            elif boundary_error < 0:
                low = mid
            else:
                solve_info.converged = True
                solve_info.message = "Bisection search found exact solution."
                solve_info.final_error = 0.0
                break
            # 7. Check for improvement and update patience counter
            if abs(boundary_error) < best_error:
                best_error = abs(boundary_error)
                patience_counter = 0
            else:
                patience_counter += 1
            # 8. Early stop
            if (patience_counter >= patience) and (iter_num > (patience * 2)):
                solve_info.message = (
                    "Bisection search stopped early due to lack of improvement."
                )
                solve_info.final_error = abs(boundary_error)
                logger.warning(
                    f"\nBisection search stopped early at iteration {iter_num+1} due to lack of improvement."
                    f"\nBest error: {best_error:.2e}."
                )
                break
        solve_info.iterations = iter_num + 1
        solve_info.time = f"{time.time() - solve_info.time:.2f} seconds "  # pyright: ignore[reportOperatorIssue]
        solve_info.final_error = f"{solve_info.final_error:.2e}"
        if self._repeated_jit_compiled:
            logger.warning(
                f'\nThe "value_update_function" are compiled for {self.jitted_value_update_func._cache_size()} times.'
                '\nTry setting parameter "number" instead of "interval" to achieve faster solution speed. '
            )
        return solve_info
