from hjb_solver.imports import *
from hjb_solver.utils import *
from hjb_solver.config import *


@struct.dataclass(frozen=True)
class AbstractParameter(ABC):
    """
    Abstract base class for model parameters.

    This class serves as a base for immutable, hashable parameter containers
    required by JAX (e.g. for use with static_argnames). Subclasses must be
    decorated with `@struct.dataclass(frozen=True)` and should declare all
    model parameters as class attributes with default values.

    Parameters
    ----------
    (Define all model parameters in subclasses as annotated class attributes.)
        Example:
        ```python
        @struct.dataclass(frozen=True) # This decorator is required
        class Parameters(AbstractParameter):
            r: float = 0.05
            g: float = 0.02
            gamma: float = 0.2
            ... # other parameters
        ```

    Notes
    -----
    - Do not add mutable fields or methods that modify instance state.
    - Derived-parameter methods may be added in subclasses, but they must not
      mutate the instance to preserve immutability and JAX compatibility.
    """

    pass


P = TypeVar("P", bound=AbstractParameter)


@dataclass
class AbstractBoundary(Generic[P], ABC):
    """
    Boundaries for the state variable `s` and value `v`.

    This dataclass stores a parameter container `p` and
    the boundary values (`s_min`, `s_max`, `v_left`, `v_right`).

    Boundary values may be provided either by passing them to the constructor or
    by setting them in a subclass `independent_boundary` and `dependent_boundary` implementation.

    Parameters
    ----------
    p : P
        Model parameters (subclass of AbstractParameter).
    s_min : float
        Minimum state variable boundary.
    s_max : float
        Maximum state variable boundary.
    v_left : float
        Value function at the left boundary (s_min).
    v_right : float
        Value function at the right boundary (s_max).

    Notes
    -----
    - All four boundary values must be numeric (int|float) when validated.
    - s_min and s_max will be converted to float and validated that s_min < s_max.
    """

    p: P = field(repr=False)
    s_min: Optional[float] = None
    s_max: Optional[float] = None
    v_left: Optional[float] = None
    v_right: Optional[float] = None

    independent: set[Literal["s_min", "s_max", "v_left", "v_right"]] = field(
        init=False, repr=False
    )
    dependent: set[Literal["s_min", "s_max", "v_left", "v_right"]] = field(
        init=False, repr=False
    )
    required_boundary: set[Literal["s_min", "s_max", "v_left", "v_right"]] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        # Set independent boundary values
        independent = self.independent_boundary()
        for name in ("s_min", "s_max", "v_left", "v_right"):
            val = getattr(self, name)
            if val is not None:
                if name in independent:
                    raise ValueError(
                        f"Boundary value '{name}' was provided to constructor "
                        "but also set in independent_boundary(). "
                        "\nProvide boundary values either via constructor or "
                        "in independent_boundary(), not both."
                    )
                else:
                    independent[name] = val
        # Set dependent boundary values
        dependent, self.required_boundary = self.dependent_boundary()
        for name in independent:
            if name in dependent:
                raise ValueError(
                    f"Boundary value '{name}' was provided repeatedly, "
                    "please check constructor, independent_boundary() and dependent_boundary()."
                )
        # Apply all boundary values
        for name, value in {**independent, **dependent}.items():
            setattr(self, name, float(value))
        self.independent = set(independent.keys())
        self.dependent = set(dependent.keys())
        self.required_boundary = set(self.required_boundary)
        # Validate all boundaries are set and consistent
        self.validate_boundaries()

    def independent_boundary(
        self,
    ) -> dict[Literal["s_min", "s_max", "v_left", "v_right"], float]:
        """
        This method can be overridden in subclasses to set `independent` boundary values.

        Independent boundaries are those that can be set without any other boundary values.

        However, `self.p` (model parameters) may still be used to calculate the independent boundaries.

        The default implementation returns an empty dictionary, meaning no independent boundaries are set.

        The implementation should return a dictionary mapping boundary names to their values.

        Only include boundaries that can be set independently.
        Leave other boundaries to be set in `dependent_boundary()`.

        Returns
        -------
        dict[Literal["s_min", "s_max", "v_left", "v_right"], float]:
        """
        return {}

    def dependent_boundary(
        self,
    ) -> tuple[
        dict[Literal["s_min", "s_max", "v_left", "v_right"], float],
        set[Literal["s_min", "s_max", "v_left", "v_right"]],
    ]:
        """
        This method can be overridden in subclasses to set `dependent` boundary values.

        Dependent boundaries are those that depend on other boundary values.

        This method is called after `self.independent_boundary()`,
        so all independent boundaries will have been set by this point.

        The default implementation returns an empty dictionary and an empty set, meaning no dependent boundaries are set.

        The implementation should return a tuple:
        - A dictionary mapping boundary names to their values.
        - A set of independent boundary names that are required to be set.

        Returns
        -------
        tuple[
            dict[Literal["s_min", "s_max", "v_left", "v_right"], float],\n
            set[Literal["s_min", "s_max", "v_left", "v_right"]],
        ]
        """
        return {}, set()

    def update_boundary(
        self,
        name: Literal["s_min", "s_max", "v_left", "v_right"],
        value: float,
    ):
        """
        This method updates a single boundary value in-place.
        """
        if name in self.independent:
            setattr(self, name, float(value))
            if name in self.required_boundary:
                for name, value in self.dependent_boundary()[0].items():
                    setattr(self, name, float(value))

    def update_boundaries(
        self,
        boundary_dict: dict[Literal["s_min", "s_max", "v_left", "v_right"], float],
    ):
        """
        This method updates multiple boundary values in-place.
        """
        for name, value in boundary_dict.items():
            self.update_boundary(name=name, value=value)
        self.validate_boundaries()
        return self.get_boundary()

    def validate_boundaries(self) -> None:
        """
        Validate and normalize boundary attributes in-place.

        Raises
        ------
        TypeError
            If any boundary value is not numeric.
        ValueError
            If s_min is not strictly less than s_max.
        """
        for name in ("s_min", "s_max", "v_left", "v_right"):
            val = getattr(self, name)
            if val is None:
                raise ValueError(f"Boundary value '{name}' must be set.")

        if self.s_min >= self.s_max:  # pyright: ignore[reportOperatorIssue]
            raise ValueError("s_min must be strictly less than s_max.")

    def get_boundary(self) -> tuple[float, float, float, float]:
        """
        Return validated boundary tuple (s_min, s_max, v_left, v_right).

        Validation is performed before returning, so callers can rely on the
        returned values being numeric floats and satisfying s_min < s_max.
        """
        # self.validate_boundaries()
        return (self.s_min, self.s_max, self.v_left, self.v_right)  # type: ignore[return-value]


class AbstractPolicyDict(TypedDict):
    """
    Base TypedDict for policy variables.

    Subclass this to declare concrete policy keys and their types, for example:
    ```python
    class PolicyDict(AbstractPolicyDict):
        investment: Array # Just keep the type as Array
        consumption: Array
    ```

    Notes
    - This class is intended for static type checking.
    - Do not instantiate AbstractPolicyDict directly — declare a subclass instead.
    - Keep value types as Array for JAX compatibility.
    """

    ...


D = TypeVar("D", bound=AbstractPolicyDict)
