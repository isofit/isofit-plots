import importlib.metadata

__version__ = importlib.metadata.version(__package__ or __name__)

import numpy as np

np.random.seed(0)

from .__main__ import cli
