"""
Single-Pixel Reflectance Fit plot
"""
import logging
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from isoplots.isonice.utils.wd import IsofitWD


Logger = logging.getLogger(__name__)

#%%
def plot_rfl(ax, da, fd, sd):
    """
    Plots the ISOFIT output reflectance against the field data

    Parameters
    ----------
    ax : matplotlib.axis
        Ax to plot on
    da : xarray.DataArray
        ISOFIT RFL data
    fd : np.array
        Field data
    sd : np.array
        Standard deviation of field data
    """
    wl = da.wavelength

    ax.plot(wl, da, color="red", label="ISOFIT", linewidth=1)
    ax.plot(wl, fd, color="black", label="Field Data", linewidth=1)

    opts = {"color": "black", "linestyle": "--", "linewidth": 0.5}
    ax.plot(wl, fd + sd, label="Field Data $\pm 1$ sd", **opts)
    ax.plot(wl, fd - sd, **opts)

    opts["linestyle"] = ":"
    ax.plot(wl, (vmax := fd + 2*sd), label="Field Data $\pm 2$ sd", **opts)
    ax.plot(wl, (vmin := fd - 2*sd), **opts)

    vmax = max(da.max(), vmax.max())
    vmin = min(da.min(), vmin.min())
    buffer = (np.abs(vmax) + np.abs(vmin)) / 10

    ax.set_ylim(vmin-buffer, vmax+buffer)
    ax.set_ylabel("HDRF [-]")

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")


def plot_residuals(ax, da, fd, sd):
    """
    Plots residuals between ISOFIT output reflectance and the field data

    Parameters
    ----------
    ax : matplotlib.axis
        Ax to plot on
    da : xarray.DataArray
        ISOFIT RFL data
    fd : np.array
        Field data
    sd : np.array
        Standard deviation of field data
    """
    wl = da.wavelength

    ax.plot(wl, da - fd, color='red', linewidth=1.2)
    ax.axhline(0, color='black', linestyle='-', linewidth=0.8)

    opts = {"color": "black", "linestyle": "--", "linewidth": 0.7, "alpha": 0.7}
    ax.plot(wl, sd, **opts)
    ax.plot(wl, -sd, **opts)

    opts["linestyle"] = ":"
    ax.plot(wl, 2*sd, **opts)
    ax.plot(wl, -2*sd, **opts)

    ax.set_ylim(-0.1, 0.1)
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Residual")

    ax.fill_between(wl, -sd, sd, color="gray", alpha=0.1)

    ax.grid(True, linestyle="--", alpha=0.5)


def plot(path=None, figsize=(8, 8), output=None):
    """
    Plots the reflectance and residuals of the ISOFIT output on the Lake Mary example
    against the field data

    \b
    Parameters
    ----------
    path : str, default=None
        Path to the single pixel output directory which contains the data/ and output/
        subdirectories
    figsize : tuple[int, int], default=(8, 8)
        Figure size for the matplotlib figure
    output : str, default=None
        Output file to write the plot to, if provided
    """
    path = Path(path).resolve()

    assert path.exists(), "LakeMary example not found, please check the --data input"
    Logger.info(f"Using Lake Mary path: {path}")
    wd = IsofitWD(path)

    Logger.info("Loading ISOFIT output reflectance")
    da = wd.load(find=f"{wd.output.name}_rfl.hdr")
    da = da.squeeze().load()

    Logger.info("Loading field data")
    df = wd.load(find="field_data")
    df = df.head(da.size)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    Logger.info("Plotting reflectance")
    plot_rfl(ax1, da, df["mean"], df["sd"])

    Logger.info("Plotting residuals")
    plot_residuals(ax2, da, df["mean"], df["sd"])

    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=200, bbox_inches="tight")
        Logger.info(f"Wrote to: {output}")


@click.command(name="spfit", no_args_is_help=True, help=plot.__doc__)
@click.option("-p", "--path", required=True)
@click.option("-fs", "--figsize", type=int, nargs=2)
@click.option("-o", "--output", required=True)
def cli(**kwargs):
    print("Plotting Lake Mary")

    plot(**kwargs)

    print("Finished")


if __name__ == "__main__":
    cli()
