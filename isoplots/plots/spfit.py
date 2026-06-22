"""
Single-Pixel Reflectance Fit plot
"""
import logging
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from isoplots.isonice.utils.wd import IsofitWD

from isofit.core.units import micron_to_nm
from isofit.core.common import resample_spectrum, calculate_resample_matrix

Logger = logging.getLogger(__name__)


def plot_rfl(ax, da, df, wl=None):
    """
    Plots the ISOFIT output reflectance against the field data

    Parameters
    ----------
    ax : matplotlib.axis
        Ax to plot on
    da : xarray.DataArray
        ISOFIT RFL data
    df : pandas.DataFrame
        Field Data CSV
    wl : np.array, default=None
        Wavelengths for the x axis, defaults to the da wavelengths
    """
    ax.plot(wl, da, color="red", label="ISOFIT", linewidth=1)
    ax.plot(wl, df["mean"], color="black", label="Field Data", linewidth=1)

    opts = {"color": "black", "linestyle": "--", "linewidth": 0.5}
    ax.plot(wl, df["mean"] + df["sd"], label="Field Data $\pm 1$ sd", **opts)
    ax.plot(wl, df["mean"] - df["sd"], **opts)

    opts["linestyle"] = ":"
    ax.plot(wl, (vmax := df["mean"] + 2*df["sd"]), label="Field Data $\pm 2$ sd", **opts)
    ax.plot(wl, (vmin := df["mean"] - 2*df["sd"]), **opts)

    vmax = max(da.max(), vmax.max())
    vmin = min(da.min(), vmin.min())
    buffer = (np.abs(vmax) + np.abs(vmin)) / 10

    ax.set_ylim(vmin-buffer, vmax+buffer)
    ax.set_ylabel("HDRF [-]")

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")


def plot_residuals(ax, da, df, wl=None):
    """
    Plots residuals between ISOFIT output reflectance and the field data

    Parameters
    ----------
    ax : matplotlib.axis
        Ax to plot on
    da : xarray.DataArray
        ISOFIT RFL data
    df : pandas.DataFrame
        Field Data CSV
    wl : np.array, default=None
        Wavelengths for the x axis, defaults to the da wavelengths
    """
    if wl is None:
        wl = da.wavelength

    ax.plot(wl, da - df["mean"].head(da.size), color='red', linewidth=1.2)
    ax.axhline(0, color='black', linestyle='-', linewidth=0.8)

    opts = {"color": "black", "linestyle": "--", "linewidth": 0.7, "alpha": 0.7}
    ax.plot(wl, df["sd"], **opts)
    ax.plot(wl, -df["sd"], **opts)

    opts["linestyle"] = ":"
    ax.plot(wl, 2*df["sd"], **opts)
    ax.plot(wl, -2*df["sd"], **opts)

    ax.set_ylim(-0.1, 0.1)
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Residual")

    ax.fill_between(wl, -df["sd"], df["sd"], color="gray", alpha=0.1)

    ax.grid(True, linestyle="--", alpha=0.5)


def plot(path=None, figsize=(8, 8), output=None):
    """
    Plots the reflectance and residuals of the ISOFIT output against field data

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

    assert path.exists(), "Field data example not found, please check the --data input"
    Logger.info(f"Using path: {path}")
    wd = IsofitWD(path)

    Logger.info("Loading ISOFIT output reflectance")
    da = wd.load(find=f"{wd.output.name}_rfl.hdr")
    da = da.squeeze().load()

    Logger.info("Loading field data")
    df = wd.load(find="field_data")

    # Ensure field data is in nanometers and matches isofit wl
    if df.wl[0] < 100.0:
        df.wl = micron_to_nm(df.wl)
    
    # If field data spacing is different we must resample
    spacing_differs = np.abs(df.wl[1] - df.wl[0]) != np.abs(da.wavelength[1] - da.wavelength[0])
    length_differs = len(df.wl) != len(da.wavelength)
    if spacing_differs or length_differs:
        Logger.info(f"Field data wavelengths differ from Isofit run, resampling...")
        df_resampled = pd.DataFrame(data=da["wavelength"], columns=["wl"])
        if "fwhm" in da.coords:
            
            Logger.info(f"Found fwhm, using this to resample spectrum")
            wl_field = df["wl"].values
            wl_isofit = da["wavelength"].values
            fwhm_isofit = da["fwhm"].values

            H = calculate_resample_matrix(wl_field, wl_isofit, fwhm_isofit)
            df_resampled["mean"] = resample_spectrum(
                df["mean"], wl_field, wl_isofit, fwhm_isofit, H=H
            )
            df_resampled["sd"] = resample_spectrum(
                df["sd"], wl_field, wl_isofit, fwhm_isofit, H=H
            )
        else:
            Logger.info(f"Could not find fwhm, using linear interpolation")
            df_resampled["mean"] = interp1d(df["wl"], df["mean"], kind="linear")(
                da.wavelength
            )
            df_resampled["sd"] = interp1d(df["wl"], df["sd"], kind="linear")(
                da.wavelength
            )
        df = df_resampled

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    Logger.info("Plotting reflectance")
    plot_rfl(ax1, da, df, wl=df["wl"])

    Logger.info("Plotting residuals")
    plot_residuals(ax2, da, df, wl=df["wl"])

    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=200, bbox_inches="tight")
        Logger.info(f"Wrote to: {output}")


@click.command(name="spfit", no_args_is_help=True, help=plot.__doc__)
@click.option("-p", "--path", required=True)
@click.option("-fs", "--figsize", type=int, nargs=2)
@click.option("-o", "--output", required=True)
def cli(**kwargs):
    print("Plotting Field Data")

    plot(**kwargs)

    print("Finished")


if __name__ == "__main__":
    cli()
