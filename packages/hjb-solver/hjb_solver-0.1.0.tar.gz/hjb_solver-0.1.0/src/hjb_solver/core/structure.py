from hjb_solver.config import *
from hjb_solver.core.abstraction import AbstractBoundary, D, P
from hjb_solver.imports import *
from hjb_solver.utils import *


@dataclass
class BoundaryDerivative:
    """
    Container for boundary derivative values used in PDE solvers.

    Attributes
    ----------
        dv_left (float):
            First derivative at the left boundary (v'(x_left)).
        d2v_left (float):
            Second derivative at the left boundary (v''(x_left)).
        dv_right (float):
            First derivative at the right boundary (v'(x_right)).
        d2v_right (float):
            Second derivative at the right boundary (v''(x_right)).
    """

    dv_left: float
    d2v_left: float
    dv_right: float
    d2v_right: float

    def as_dict(self) -> dict:
        """
        Convert the BoundaryDerivative instance to a dictionary.

        Returns
        -------
        dict
            A dictionary representation of the BoundaryDerivative instance.
        """
        return asdict(self)

    def __getitem__(self, key: str) -> float:
        """
        Allow dictionary-like access to BoundaryDerivative attributes.

        Parameters
        ----------
        key : str
            The attribute name to access.

        Returns
        -------
        float
            The value of the specified attribute.

        Raises
        ------
        KeyError
            If the specified key does not correspond to any attribute.
        """
        if key in self.as_dict():
            return getattr(self, key)
        else:
            raise KeyError(f"{key} is not a valid attribute of BoundaryDerivative.")


@dataclass
class Info:
    """
    Container for solver result information.

    Attributes
    ----------
    converged : bool
        Whether the solver converged.
    iterations : int
        Number of iterations performed. Must be non-negative.
    final_error : float | str
        Final error reported by the solver.
    message : str
        Additional information about the solver run.
    time : float | str
        Time taken for the solver run.

    Notes
    -----
    - Fields are validated and coerced to appropriate types in __post_init__.
    - Use as_dict() to obtain a plain dictionary representation.
    """

    converged: bool
    iterations: int
    final_error: float | str
    message: str
    time: float | str

    def __post_init__(self):
        ...
        # if isinstance(self.time, float):
        #     self.time = f"{self.time:.3f}s"

    def as_dict(self) -> dict:
        """
        Return a dictionary representation of the Info instance.
        """
        return asdict(self)


@dataclass
class Solution(Generic[P, D]):
    """
    Container for the solution of the HJB equation.

    Attributes
    ----------
    p : Parameter
        The parameters used in the HJB equation.
    boundary : Boundary[Parameter]
        The boundary conditions for the HJB equation.
    boundary_derivative : BoundaryDerivative
        The derivatives at the boundaries.
    s : Float[Array, "N"]
        The grid points for the state variable.
    v : Float[Array, "N"]
        The value function evaluated at the grid points.
    dv : Float[Array, "N"]
        The first derivative of the value function at the grid points.
    d2v : Float[Array, "N"]
        The second derivative of the value function at the grid points.
    policy : D
        The optimal policy derived from the solution.
    number : int
        The number of grid points (size of the solution).
    interval : float
        The grid spacing (step size).
    df : DataFrame
        A DataFrame containing the solution and policy for easy analysis.
    variables : list[str]
        List of variable names in the DataFrame.
    """

    p: P = field(repr=False)
    boundary: AbstractBoundary[P] = field(repr=True)
    boundary_derivative: BoundaryDerivative = field(repr=True)

    s: Float[Array, "N"] = field(repr=False)
    v: Float[Array, "N"] = field(repr=False)
    dv: Float[Array, "N"] = field(repr=False)
    d2v: Float[Array, "N"] = field(repr=False)
    policy: D = field(repr=False)

    number: int = field(init=False, repr=True)
    interval: float = field(init=False, repr=True)
    df: pd.DataFrame = field(init=False, repr=False)
    variables: list[str] = field(init=False, repr=True)

    def __post_init__(self):
        self.number = self.s.size
        self.s_min, self.s_max, self.v_left, self.v_right = self.boundary.get_boundary()
        self.interval = (self.s_max - self.s_min) / (self.number - 1)
        self.df = pd.DataFrame(
            {
                "s": self.s,
                "v": self.v,
                "dv": self.dv,
                "d2v": self.d2v,
                **{k: v for k, v in self.policy.items()},
            }
        )
        self.variables = list(self.df.columns)

    def save(self, file: str | Path) -> Path:
        """
        Save the solution to disk.

        The file format is inferred from the file extension:
          - .feather -> Feather (pyarrow required)
          - .csv     -> CSV
          - .xlsx / .xls -> Excel

        Parameters
        ----------
        file : str | Path
            Target file path. The format is determined from the file suffix.

        Returns
        -------
        Path
            The path to the written file.

        Raises
        ------
        ValueError
            If no extension is provided or an unsupported extension is used.
        RuntimeError
            If writing the file fails.
        """
        file_path = Path(file)
        suffix = file_path.suffix.lower()

        if suffix == "":
            raise ValueError("No file extension provided. Please include one of: .feather, .csv, .xlsx, .xls")

        ext_map = {
            ".feather": "feather",
            ".csv": "csv",
            ".xlsx": "excel",
            ".xls": "excel",
        }

        if suffix not in ext_map:
            raise ValueError(f"Unsupported file extension: {suffix!r}. Supported: {tuple(ext_map.keys())}")

        fmt = ext_map[suffix]

        # ensure parent directory exists
        if file_path.parent and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if fmt == "feather":
                self.df.reset_index(drop=True).to_feather(file_path)
            elif fmt == "csv":
                self.df.to_csv(file_path, index=False)
            else:  # excel
                self.df.to_excel(file_path, index=False)
        except Exception as exc:
            raise RuntimeError(f"Failed to save solution to {file_path!s}: {exc}") from exc

        return file_path
