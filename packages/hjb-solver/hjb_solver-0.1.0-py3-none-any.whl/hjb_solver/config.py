from hjb_solver.imports import *

jax.config.update("jax_enable_x64", True)
try:
    plt.rcParams.update(
        {
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 12,
        }
    )

except RuntimeError:
    print("LaTeX not found, using default font settings.")
