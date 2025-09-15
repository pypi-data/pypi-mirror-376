
from hjb_solver import *

# 1. Define your model parameters
@struct.dataclass(frozen=True)
class Parameter(AbstractParameter):
    r: float = 0.06         # Risk-free rate
    delta: float = 0.1007   # Rate of depreciation  
    mu: float = 0.18        # Productivity drift
    sigma: float = 0.09     # Productivity volatility
    theta: float = 1.5      # Adjustment cost parameter
    lambda_: float = 0.01   # Cash carrying cost
    l: float = 0.9          # Liquidation value

# 2. Define your policy variables
class PolicyDict(AbstractPolicyDict):
    investment: Array       # Investment rate

# 3. Define boundary conditions with dependencies
@dataclass
class Boundary(AbstractBoundary[Parameter]):
    def independent_boundary(self):
        return {"v_left": self.p.l}  # Liquidation value at left boundary
  
    def dependent_boundary(self):
        if self.s_max is None:
            raise ValueError("s_max must be provided.")
  
        # Complex payout boundary calculation
        sqrt_term = (
            self.p.r + self.p.delta + (self.s_max + 1) / self.p.theta
        ) ** 2 - (2 / self.p.theta) * (
            self.p.mu + (self.p.r + self.p.delta - self.p.lambda_) * self.s_max
            + (self.s_max + 1) ** 2 / (2 * self.p.theta)
        )
  
        v_right = self.p.theta * (
            (self.p.r + self.p.delta + (self.s_max + 1) / self.p.theta)
            - sqrt_term ** 0.5
        )
  
        return {"v_right": v_right}, {"s_max"}  # v_right depends on s_max

# 4. Implement your solver with endogenous boundary
class Solver(AbstractSolver[Parameter, PolicyDict]):
    def initialize_policy(self):
        # Start with frictionless optimal investment
        inv_fb = (
            self.p.r + self.p.delta - (
                (self.p.r + self.p.delta) ** 2 
                - 2 * (self.p.mu - (self.p.r + self.p.delta)) / self.p.theta
            ) ** 0.5
        )
        return PolicyDict(investment=jnp.full_like(self.s, inv_fb))
  
    def update_policy(self, v, dv, d2v, s, p):
        # First-order condition: 1 + θi = (V - sV')/V'
        investment = (1 / p.theta) * (v / dv - s - 1)
        return PolicyDict(investment=investment)
  
    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, p):
        inv = policy["investment"]
  
        # HJB equation for firm value with investment and cash management
        capital_evolution = (inv - p.delta) * (v - s * dv)
        cash_flow = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
        uncertainty = 0.5 * p.sigma**2 * d2v
        discount = -p.r * v
  
        return capital_evolution + cash_flow + uncertainty + discount
  
    def bisection_boundary_error(self, solution):
        # Target: smooth pasting condition V''(s_max) = 0
        return solution.boundary_derivative.d2v_right

# 5. Solve with endogenous boundary optimization
parameter = Parameter()
boundary = Boundary(p=parameter, s_min=0.0, s_max=0.22)  # Initial guess for payout boundary
solver = Solver(p=parameter, boundary=boundary, guess_policy=True)

# Find optimal payout boundary using bisection search
info = solver.bisection_search(
    boundary_name="s_max",
    low=0.1,
    high=0.3,
)

pp(info)

# 6. Analyze results
solution = solver.solution
pp(solution.df)
