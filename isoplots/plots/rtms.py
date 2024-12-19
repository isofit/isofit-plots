from pathlib import Path

import click
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import plotext

from isofit.radiative_transfer import luts


DefaultVariables = [
    'rhoatm', 'sphalb', 'transm_down_dir',
    'transm_down_dif', 'transm_up_dir', 'transm_up_dif'
]
LegendTitles = {
    "H2OSTR": "Water Vapor\n[g cm$^{-1}$]",
    "AOT550": "Aerosol Optical Depth",
    "AERFRAC_2": "Aerosol Optical Depth",
    "observer_altitude_km": "[km]",
    "surface_elevation_km": "[km]",
    "solar_zenith": "[deg]",
}
CMap = plt.get_cmap('coolwarm')


def plot(unstacked, dim, variables, fig, grid, row, name):
    """
    Plots the variables for each unique value of a given dimension

    Parameters
    ----------
    unstacked : xr.DataArray
        Unstacked LUT
    dim : str
        Dimension that's being plotted
    variables : list[str]
        Variables to plot
    fig : matplotlib.figure.Figure
        Current active figure
    grid : matplotlib.gridspec.GridSpec
        GridSpec to use
    row : int
        Row to plot on
    name : str
        Name to prepend to plot titles
    """
    # Dimensions to take the mean on
    dims = set(unstacked.coords) - {dim, "wl"}

    for i, var in enumerate(variables):
        ax = fig.add_subplot(grid[row, i])
        ax.set_xlabel('Wavelength [nm]')
        ax.set_title(f"{name}: {var}")

        data = unstacked[var]
        size = data[dim].size

        for j in range(size):
            sel = data.isel({dim: j}).mean(dims, skipna=True)
            ax.plot(sel.wl, sel, c=CMap(j/size), linewidth=1, label=float(sel[dim]))

        if i == 0 and row == 0:
            ax.legend(title=LegendTitles.get(dim))


def getBadMask(rtm, cmp=None):
    """
    Creates a mask of the bad points

    Parameters
    ----------
    rtm : xr.Dataset
        Input RTM
    cmp : xr.Dataset, default=None
        Comparison RTM

    Returns
    -------
    bad : xr.DataArray
        Mask along the point dimension that are bad
    """
    bad = np.zeros(rtm.point.size, dtype=bool)

    if "surface_elevation_km" in rtm and "observer_altitude_km" in rtm:
        bad |= rtm.surface_elevation_km >= rtm.observer_altitude_km

    if cmp:
        bad |= (cmp.transm_down_dif > 10).any("wl")

    return bad


def RTMs(file,
    compare=None,
    variables=DefaultVariables,
    input_name="Input",
    compare_name="Compare",
    output=None,
    terminal=False,
    ):
    """\
    Plots RTMs

    \b
    Parameters
    ----------
    file : str
        Path to the input LUT NetCDF
    compare : str, default=None
        Secondary LUT NetCDF to compare with
    variables : list[str], default=['rhoatm', 'sphalb', 'transm_down_dir', 'transm_down_dif', 'transm_up_dir', 'transm_up_dif']
        LUT variables to plot
    input_name : str, default="Input"
        Name to assign for the input LUT
    compare_name : str, default="Compare"
        Name to assign for the comparison LUT
    output : str, default=None
        Path to output directory to save plots to
    terminal : bool, default=False
        Converts the matplotlib figure to plotext to be plotted into a terminal
    """
    print(f"Loading {file}")
    rtm = luts.load(file)

    cmp = None
    if compare:
        print(f"Loading {compare}")
        cmp = luts.load(compare)

        if not (rtm.point == cmp.point).all():
            print("Points do not match between the input and comparison NetCDFs")
            return

    for var in variables:
        if var not in rtm:
            print(f"Could not find {var!r} in {file}")
            return
        if cmp and var not in cmp:
            print(f"Could not find {var!r} in {compare}")
            return

    bad = getBadMask(rtm, cmp)
    if bad.any():
        print(f"{bad.sum().data} points were detected as bad, dropping them")
        print(f"Indices: {np.argwhere(bad.data).ravel()}")
        rtm = rtm.sel(point=~bad)
        if cmp:
            cmp = cmp.sel(point=~bad)

    # Unstack to make plotting easier
    u_rtm = rtm.unstack()
    if cmp:
        u_cmp = cmp.unstack()

    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)

    dims = set(u_rtm.coords) - {"wl"}
    for dim in dims:
        fig = plt.figure(figsize=(30, 10))
        grid = gridspec.GridSpec(ncols=len(variables), nrows=2 if cmp else 1, wspace=0.2, hspace=0.2)
        fig.suptitle(dim, fontsize=32)

        plot(u_rtm, dim, variables, fig, grid, 0, input_name)
        if cmp:
            plot(u_cmp, dim, variables, fig, grid, 1, compare_name)

        if output:
            file = output / f"{dim}.png"
            plt.savefig(file, dpi=200, bbox_inches='tight')
            print(f"Wrote to: {file}")

        if terminal:
            plotext.from_matplotlib(fig)
            plotext.show()


@click.command(name="RTMs", no_args_is_help=True, help=RTMs.__doc__)
@click.argument("file")
@click.option("-c", "--compare")
@click.option("-v", "--variables", multiple=True, default=DefaultVariables)
@click.option("-in", "--input-name", default="Input")
@click.option("-cn", "--compare-name", default="Compare")
@click.option("-o", "--output")
@click.option("-t", "--terminal", is_flag=True)
def cli(**kwargs):
    print("Plotting RTMs")

    RTMs(**kwargs)

    print("Finished")


if __name__ == "__main__":
    cli()
