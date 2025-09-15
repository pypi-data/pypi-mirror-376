from hjb_solver import (
    AbstractBoundary,
    AbstractParameter,
    AbstractPolicyDict,
    AbstractSolver,
    Array,
    dataclass,
    jax,
    jnp,
    plt,
    pp,
    struct,
)

"""
This script implements a solver for the dynamic hedging problem of a financially constrained firm,
as described in the paper "A unified theory of tobin's q, corporate investment, financing, and risk management"
by Patrick Bolton, Hui Chen, and Neng Wang (2011).
"""


@struct.dataclass(frozen=True)
class Parameter(AbstractParameter):
    r: float = 0.06  # Risk-free rate
    delta: float = 0.1007  # Rate of depreciation
    mu: float = 0.18  # Risk-neutral mean productivity shock
    sigma: float = 0.09  # Volatility of productivity shock
    theta: float = 1.5  # Adjustment cost parameter
    lambda_: float = 0.01  # Proportional cash-carrying cost
    l: float = 0.9  # Capital liquidation value
    phi: float = 0.01  # Fixed financing cost
    gamma: float = 0.06  # Proportional financing cost

    # rho (ρ): Correlation between the firm's productivity shock and the market return.
    rho: float = 0.8
    # sigma_m (σm): Volatility of the aggregate market portfolio (futures price).
    sigma_m: float = 0.20
    # pi (π): A constant multiple defining the margin requirement. The hedge position cannot exceed π times the cash in the margin account.
    pi: float = 5.0
    # epsilon (ε): The additional flow cost per unit of cash held in the margin account.
    epsilon: float = 0.005


class PolicyDict(AbstractPolicyDict):
    # investment (i): The investment rate in physical capital as a fraction of the firm's total capital.
    investment: Array
    # psi (ψ): The hedge ratio, representing the firm's position in market index futures as a fraction of its total cash.
    psi: Array


@dataclass
class Boundary(AbstractBoundary[Parameter]):

    def independent_boundary(self):
        """The left boundary value v_left is set to the liquidation value of capital l"""
        return {"v_left": self.p.l}

    def dependent_boundary(self):
        """
        Calculates the firm's value-capital ratio at the optimal payout boundary (w_bar).

        This calculation is derived from the Hamilton-Jacobi-Bellman (HJB) equation (Eq. 13)
        under the specific conditions that hold at the endogenous payout boundary, w_bar (here s_max).

        At this boundary, two key conditions apply:
        1. The marginal value of cash is equal to its value outside the firm (i.e., one),
           so p'(w_bar) = 1 (from Eq. 16).
        2. The boundary is chosen optimally, which implies the "super contact" or "smooth pasting"
           condition, p''(w_bar) = 0 (from Eq. 17).

        Applying these two conditions to the HJB differential equation causes it to simplify into
        a standard algebraic quadratic equation in terms of the value-capital ratio p(w_bar).
        This function implements the solution to that quadratic equation to find p(w_bar).
        """
        # Since the calculation of v_right depends on s_max, we ensure s_max is provided
        if self.s_max is None:
            raise ValueError("s_max must be provided for the boundary.")
        # This term corresponds to the discriminant of the quadratic equation for p(w_bar) derived from the HJB equation.
        # It gathers all the model parameters (r, delta, mu, theta, lambda) evaluated at the boundary s_max.
        sqrt_term_val = (
            self.p.r + self.p.delta + (self.s_max + 1) / self.p.theta
        ) ** 2 - (2 / self.p.theta) * (
            self.p.mu
            + (self.p.r + self.p.delta - self.p.lambda_) * self.s_max
            + (self.s_max + 1) ** 2 / (2 * self.p.theta)
        )
        # Solves the quadratic equation for p(w_bar), which is denoted here as v_right.
        # The negative sign before the square root is chosen to select the economically relevant root for the firm value.
        v_right = self.p.theta * (
            (self.p.r + self.p.delta + (self.s_max + 1) / self.p.theta)
            - (sqrt_term_val) ** 0.5
        )
        return (
            {"v_right": v_right},
            {"s_max"},  # depends on s_max
        )


class Solver(AbstractSolver[Parameter, PolicyDict]):
    def initialize_policy(self) -> PolicyDict:
        # The optimal investment rate in the frictionless case (without financing frictions), from Equation (7).
        inv_first_best = (
            self.p.r
            + self.p.delta
            - (
                (self.p.r + self.p.delta) ** 2
                - 2 * (self.p.mu - (self.p.r + self.p.delta)) / self.p.theta
            )
            ** 0.5
        )
        # Initialize the hedge ratio with the optimal frictionless hedge ratio from Equation (27).
        # In the frictionless case (no margin costs/requirements), the optimal hedge is constant.
        psi_frictionless = -self.p.rho * self.p.sigma / self.p.sigma_m
        return PolicyDict(
            investment=jnp.full_like(self.s, inv_first_best),
            psi=jnp.full_like(self.s, psi_frictionless),
        )

    def update_policy(
        self, v: Array, dv: Array, d2v: Array, s: Array, p: Parameter
    ) -> PolicyDict:

        # from FOC: 1 + θi = (v - s*v') / v'
        new_investment = (1 / p.theta) * (v / dv - s - 1)

        # Calculate the optimal hedge ratio for the interior region, as defined in Equation (30).
        # This balances the risk-reduction benefits of hedging against the costs from margin requirements (ε).
        # 's' is the cash-capital ratio w, 'dv' is p'(w), and 'd2v' is p''(w).
        psi_interior = (
            1
            / s
            * (
                (-p.rho * p.sigma / p.sigma_m)
                - ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
            )
        )

        # Apply the maximum-hedging boundary (w-). When cash is very low, the firm hedges at the maximum allowed level, ψ = -π.
        # This clips the hedge ratio at -π, ensuring it doesn't exceed the constraint.
        psi_clipped = jnp.maximum(psi_interior, -p.pi)

        # This logic determines the zero-hedging boundary (w+).
        # 'marginal_benefit' represents the absolute benefit of hedging from risk reduction (the frictionless component).
        marginal_benefit = p.rho * p.sigma / p.sigma_m
        # 'marginal_cost' represents the absolute marginal cost of hedging due to margin requirements.
        # Note: The variable naming might be counter-intuitive; this term captures the cost.
        marginal_cost = jnp.abs((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
        # The firm should hedge only if the benefit outweighs the cost.
        should_hedge = marginal_cost < marginal_benefit

        # Combine the three hedging regions:
        # 1. If 'should_hedge' is False (cost > benefit), set hedge ratio to 0 (zero-hedging region).
        # 2. If 'should_hedge' is True, use the clipped value, which covers both the interior solution and the maximum-hedging boundary.
        new_psi = jnp.where(should_hedge, psi_clipped, 0.0)

        return PolicyDict(investment=new_investment, psi=new_psi)

    @staticmethod
    def hjb_residual(
        v: Array, dv: Array, d2v: Array, s: Array, policy: PolicyDict, p: Parameter
    ) -> Array:
        inv = policy["investment"]
        psi = policy["psi"]

        # Calculate kappa (κ), the fraction of cash held in the margin account, from Equation (29).
        # This is the minimum required to satisfy the margin constraint |ψ| ≤ πκ.
        kappa = jnp.minimum(jnp.abs(psi) / p.pi, 1.0)

        # Drift term from capital accumulation
        drift_K = (inv - p.delta) * (v - s * dv)

        # Drift term from cash evolution.
        # This includes the flow cost of holding cash in the margin account (-ε * κ * w), as seen in Equation (26).
        cash_flow_drift = (
            (p.r - p.lambda_) * s
            + p.mu
            - inv
            - 0.5 * p.theta * inv**2
            - p.epsilon * kappa * s
        )
        drift_W = cash_flow_drift * dv

        # The total variance term (diffusion) from the HJB Equation (28) after normalization.
        # It includes the firm's idiosyncratic variance (σ²), the variance from hedging (ψ²σm²w²),
        # and the covariance term.
        total_variance = (
            p.sigma**2
            + (psi**2) * (p.sigma_m**2) * (s**2)
            + 2 * p.rho * p.sigma * p.sigma_m * psi * s
        )
        diffusion = 0.5 * total_variance * d2v

        # Discounting term from the HJB equation
        discount = -p.r * v

        # The HJB residual combines all components.
        # A correct solution should have this residual close to zero.
        return drift_K + drift_W + diffusion + discount

    def update_boundary(self, solution) -> tuple[dict, float]:
        # Update the left boundary value v_left based on the smooth-pasting condition at the optimal liquidation point m.
        # The optimal liquidation point m satisfies p'(m) = 1 + γ, where γ is the proportional financing cost.
        # At this point, the value function must satisfy p(m) = l + (1 + γ)m, ensuring smooth pasting.
        # We find the index i where the derivative dv is closest to 1 + γ, then compute the corresponding m and v(m).
        # Using these, we update v_left to ensure the boundary condition holds.
        v_left = self.v_left  # current left boundary value
        dv = solution.dv  # first derivative of the value function
        # Find the index where dv is closest to 1 + gamma
        i = jax.numpy.argmin(jnp.abs(dv - (1 + self.p.gamma)))
        # Compute the corresponding m and v(m)
        m = self.s[i]
        v_m = self.v[i]
        # Update v_left using the smooth-pasting condition
        v_left = v_m - self.p.phi - (1 + self.p.gamma) * m
        return (
            {"v_left": v_left},
            (error := abs(self.v_left - v_left)),
        )

    def bisection_boundary_error(self, solution) -> float:
        # The boundary error is defined as the second derivative at the right boundary (s_max).
        # For the correct s_max, we expect the second derivative to be zero (smooth pasting).
        # Thus, the sign of the boundary error is the same as our definition error.
        error = solution.boundary_derivative.d2v_right
        return error


def plot_results(solution, p):
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(
        "Dynamic Hedging Policy of a Financially Constrained Firm", fontsize=16
    )

    s = solution.s

    # Panel A: Hedge Ratio ψ(w)
    ax = axs[0, 0]
    ax.plot(s, solution.policy["psi"], label="Hedge ratio $\\psi(w)$")
    ax.axhline(
        y=-p.pi,
        color="r",
        linestyle="--",
        label=f"Max hedge limit (-$\\pi$ = {-p.pi})",
    )
    ax.set_title("A. Hedge ratio: $\\psi(w)$")
    ax.legend()

    # Panel B: Investment-Capital Ratio i(w)
    ax = axs[0, 1]
    ax.plot(s, solution.policy["investment"])
    ax.set_title("B. Investment rate: $i(w)$")

    # Panel C: Firm Value-Capital Ratio p(w)
    ax = axs[1, 0]
    ax.plot(s, solution.v)
    ax.set_title("C. Firm value: $p(w)$")
    ax.set_xlabel("cash-capital ratio: $w = W/K$")

    # Panel D: Marginal Value of Cash p'(w)
    ax = axs[1, 1]
    ax.plot(s, solution.dv)
    ax.set_title("D. Marginal Value of Cash: $p'(w)$")
    ax.set_xlabel("cash-capital ratio: $w = W/K$")

    plt.show()


if __name__ == "__main__":
    # Set up Parameter, Boundary, and Solver
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.15,  # random guess for s_max
    )
    solver = Solver(p=parameter, boundary=boundary, guess_policy=True)
    # Check for initialization
    pp(solver)
    # Direct solve without boundary search
    # pp(solver.solve())
    # Search for the correct v_left value
    # pp(solver.search_boundary())
    # Search for the correct s_max value using bisection
    pp(
        solver.bisection_search(
            boundary_name="s_max",
            low=0.10,
            high=0.20,
            tol=1e-4,
            max_iter=20,
            patience=5,
        )
    )
    # Check results
    pp(solver.boundary)
    pp(solver.solution.df)
    solver.solution.save("src/examples/solution/BCW2011Hedging_solution", fmt="feather")

    plot_results(solver.solution, parameter)
