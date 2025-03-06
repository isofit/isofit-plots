import click
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.patches import Rectangle


def findInterestingPixels(data):
    """
    Finds the [x, y] pairs for interesting pixels in the scene. These are the min, avg,
    and max valued pixels along the RGB bands.

    Parameters
    ----------
    data : xr.DataArray
        Data with an `x` and `y` dimensions

    Returns
    -------
    pixels : list[list[int, int]]
        [x, y] pairs of pixels
    """
    pixels = []

    pixel = data.where(data == data.quantile(0.), drop=True).squeeze()
    pixels.append([int(pixel.x.data), int(pixel.y)])

    pixel = data.where(data == data.quantile(.5), drop=True)
    pixels.append([int(pixel.x), int(pixel.y)])

    pixel = data.where(data == data.quantile(1.), drop=True)
    pixels.append([int(pixel.x), int(pixel.y)])

    return pixels


def plotSpectra(ax, data, pixel, removeMin=True, hideX=False, annotate=None, name=None, color=None):
    """
    Plots a reflectance spectra for a given pixel

    Parameters
    ----------
    ax : matplotlib ax
        Ax to plot on
    data :
        ISOFIT reflectance data
    pixel : list[int, int]
        X, Y pixel coordinates
    removeMin : bool, default=True
        Removes the min values
    hideX : bool, default=False
        Hides the X axis label and ticks
    annotate : matplotlib ax
        Image ax to create an annotation on
    name : str, default=None
        Name of the pixel for annotation purposes
    color : str, default=None
        Color to use for annotation
    """
    sel = dict(zip(['x', 'y'], pixel))
    data = data.isel(sel)

    if removeMin:
        data = data.where(data != data.min(), np.nan)

    if annotate:
        name = name or len(annotate.patches) + 1

    ax.plot(data)
    ax.set_ylabel("Reflectance")
    ax.set_xlabel("Wavelength")

    ax.set_title(f"Spectra at {pixel}")
    if name:
        ax.set_title(f"Spectra {name} at {pixel}")

    if hideX:
        ax.get_xaxis().set_visible(False)

    if annotate:
        rect = Rectangle(pixel, 1, 1, linewidth=1, edgecolor=color, facecolor='none')
        annotate.add_patch(rect)

        if pixel[1] == 0:
            pixel[1] += 2
        pixel[1] -= 1
        annotate.annotate(name, pixel, color=color, fontsize=16)


def plot(file, output=None, title=None, terminal=False):
    """\
    Plots the image of an ISOFIT reflectance file along with three interesting spectra

    \b
    Parameters
    ----------
    file : str
        Path to the input ISOFIT _rfl file
    output : str, default=None
        Path to output file to save plots to, eg. ./spectra.png
    title : str, default=None
        Optional title to set
    """
    ds = xr.open_dataset(file, engine='rasterio')
    da = ds.band_data

    # Retrieve the RGB subset
    rgb = da.isel(band=[60, 40, 30]).transpose('y', 'x', 'band')
    rgb /= rgb.max(['x', 'y']) # Brightens image

    # Convert to pixel coords for easier plotting
    rgb['x'] = range(rgb.x.size)
    rgb['y'] = range(rgb.y.size)

    # Retrieve the pixels that will be plotted
    pixels = findInterestingPixels(rgb.mean('band'))

    fig = plt.figure(figsize=(30, 10))
    grid = gridspec.GridSpec(ncols=2, nrows=3, wspace=-0.1, hspace=0.2)

    if title:
        fig.suptitle(title, fontsize=32)

    # Plot the RGB data as an image
    img = fig.add_subplot(grid[:, 0])
    img.imshow(rgb)
    img.set_title("RGB of RFL")

    # Now plot three interesting spectras
    plotSpectra(fig.add_subplot(grid[0, 1]),
        data  = da,
        pixel = pixels[0],
        hideX = True,
        annotate = img,
        color = (1, 1, 0),
    )

    plotSpectra(fig.add_subplot(grid[1, 1]),
        data  = da,
        pixel = pixels[1],
        hideX = True,
        annotate = img,
        color = (0, 1, 0),
    )

    plotSpectra(fig.add_subplot(grid[2, 1]),
        data  = da,
        pixel = pixels[2],
        annotate = img,
        color = (1, 0, 1),
    )

    if output:
        plt.savefig(output, dpi=200, bbox_inches='tight')
        print(f"Wrote to: {output}")

    if terminal:
        plotext.from_matplotlib(fig)
        plotext.show()


@click.command(name="spectra", no_args_is_help=True, help=plot.__doc__)
@click.argument("file")
@click.option("-t", "--title")
@click.option("-o", "--output")
def cli(**kwargs):
    print("Plotting spectra")

    plot(**kwargs)

    print("Finished")


if __name__ == "__main__":
    cli()
