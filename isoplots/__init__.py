import importlib.metadata

__version__ = importlib.metadata.version(__package__ or __name__)

import logging
logging.getLogger("rasterio").setLevel(logging.ERROR)
logging.getLogger("h5py").setLevel(logging.ERROR)
logging.getLogger("numexpr").setLevel(logging.ERROR)

import matplotlib.pyplot as plt
plt.set_loglevel("warning")

import numpy as np
np.random.seed(0)

from .__main__ import cli
