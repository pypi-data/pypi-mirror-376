from .geometry3D import Geometry3D
from .geometry2D import Geometry2D
from .boundary_conditions import BoundaryConditions
from .visualizer import plot2D,movie2D
from .fourier import Fourier

import jax


jax.config.update("jax_enable_x64",True)
jax.config.update("jax_log_compiles",0)

__version__ = "1.0.6"
