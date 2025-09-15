import ast
import copy
import inspect
import re
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Literal,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flax import struct
from jax import grad, jacfwd, jit, jvp, lax, value_and_grad, vmap
from jaxtyping import Array, Float
from loguru import logger
from panel_print import pp
from rich import print
from rich.pretty import pprint
from tqdm import tqdm, trange
