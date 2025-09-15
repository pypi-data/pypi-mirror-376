from hjb_solver import *


@struct.dataclass(frozen=True)
class Parameter(AbstractParameter):
    r: float = 0.06
    delta: float = 0.1007
    mu: float = 0.18
    sigma: float = 0.09
    theta: float = 1.5
    lambda_: float = 0.01
    l: float = 0.9


class PolicyDict(AbstractPolicyDict):
    investment: Array


@dataclass
class Boundary(AbstractBoundary[Parameter]):
    def independent_boundary(self):
        return {"v_left": self.p.l}

    def dependent_boundary(self):
        if self.s_max is None:
            raise ValueError("s_max must be provided.")
        sqrt_term_val = (
            self.p.r + self.p.delta + (self.s_max + 1) / self.p.theta
        ) ** 2 - (2 / self.p.theta) * (
            self.p.mu
            + (self.p.r + self.p.delta - self.p.lambda_) * self.s_max
            + (self.s_max + 1) ** 2 / (2 * self.p.theta)
        )
        if sqrt_term_val < 0:
            raise ValueError(
                "Invalid parameters or s_max guess: square root term is negative."
            )
        pwr = self.p.theta * (
            (self.p.r + self.p.delta + (self.s_max + 1) / self.p.theta)
            - (sqrt_term_val) ** 0.5
        )
        return {"v_right": pwr}, {"s_max"}


class Solver(AbstractSolver[Parameter, PolicyDict]):

    def initialize_policy(self):
        inv_first_best = (
            self.p.r
            + self.p.delta
            - (
                (self.p.r + self.p.delta) ** 2
                - 2 * (self.p.mu - (self.p.r + self.p.delta)) / self.p.theta
            )
            ** 0.5
        )
        return PolicyDict(
            investment=jnp.full_like(self.s, inv_first_best),
        )

    def update_policy(self, v: Array, dv: Array, d2v: Array, s: Array, p: Parameter):

        investment = (1 / p.theta) * (v / dv - s - 1)
        return PolicyDict(investment=investment)

    @staticmethod
    def hjb_residual(
        v: Array, dv: Array, d2v: Array, s: Array, policy: PolicyDict, p: Parameter
    ) -> Array:
        inv = policy["investment"]
        term1 = (inv - p.delta) * (v - s * dv)
        term2 = -p.r * v
        term3 = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
        term4 = 0.5 * p.sigma**2 * d2v
        return term1 + term2 + term3 + term4

    def bisection_boundary_error(self, solution):
        error = solution.boundary_derivative.d2v_right
        return error


if __name__ == "__main__":

    parameter = Parameter()
    boundary = Boundary(p=parameter, s_min=0.0, s_max=0.22)
    solver = Solver(p=parameter, boundary=boundary, guess_policy=True)
    # pp(solver.solve())
    pp(
        solver.bisection_search(
            boundary_name="s_max",
            low=0.1,
            high=0.3,
        )
    )
    pp(solver.boundary)
    pp(solver.solution.df)
