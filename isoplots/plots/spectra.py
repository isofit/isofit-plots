import warnings

import click
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.patches import Rectangle


warnings.simplefilter("ignore")

Colors = {
    0: (1, 0, 0),
    1: (0, 1, 0),
    2: (1, 0, 1)
}


def findInterestingPixels(data, seed=None):
    """
    Finds the [x, y] pairs for interesting pixels in the scene. These are the min, avg,
    and max valued pixels along the RGB bands.

    Parameters
    ----------
    data : xr.DataArray
        Data with an `x` and `y` dimensions
    seed : int, default=None
        Random seed to use for finding interesting pixels. None simply uses the
        quantiles (0, .5, 1)

    Returns
    -------
    pixels : list[list[int, int]]
        [x, y] pairs of pixels
    """
    pixels = []

    flat = data.stack(z=['y', 'x'])
    sort = np.sort(flat)

    total = flat.size
    tenth = int(total * .1)

    # First, mid, and last points
    indices = np.array([0, tenth * 5, -1])
    if seed is not None:
        rng = np.random.default_rng(seed)
        indices[0] += rng.random(1)[0] * tenth # Randomly select between  [ 0%,  10%]
        indices[1] += rng.random(1)[0] * tenth - int(tenth / 2) # between [45%,  55%]
        indices[2] *= rng.random(1)[0] * tenth # Randomly select between  [90%, 100%]

    for index in indices:
        pixel = flat.where(flat == sort[index], drop=True)

        if pixel.size > 1:
            pixel = pixel[0]

        pixels.append([int(pixel.x.data), int(pixel.y)])

    return pixels


def plotSpectra(ax, data, pixel, removeMin=True, hideX=False, annotate=None, name=None, color=None):
    """
    Plots the reflectance spectra for a given pixel

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

    ax.plot(data, color=color)
    ax.set_ylabel("Reflectance")
    ax.set_xlabel("Wavelength")
    ax.grid(axis="x", color="gray", linestyle="--")

    ax.set_title(f"Spectra at {pixel}")
    if name:
        ax.set_title(f"Spectra {name} at {pixel}")

    if hideX:
        ax.set_xlabel(None)
        ax.set_xticklabels([])

    if annotate:
        rect = Rectangle(pixel, 1, 1, linewidth=1, edgecolor=color, facecolor='none')
        annotate.add_patch(rect)

        pixel = list(pixel)
        if pixel[1] == 0:
            pixel[1] += 2
        pixel[1] -= 1
        annotate.annotate(name, pixel, color=color, fontsize=16)


def plot(file, output=None, title=None, pixels=None, seed=None, terminal=False):
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
    seed : int, default=None
        Random seed to use for finding interesting pixels. None simply uses the
        quantiles (0, .5, 1)
    pixels : list[tuple[int, int]]
        Pixels (in x, y coords) to plot. Will only accept the first three pixels in the
        list
    """
    ds = xr.open_dataset(file, engine='rasterio')
    da = ds.band_data

    # Retrieve the RGB subset
    rgb = da.sel(band=[60, 40, 30]).transpose('y', 'x', 'band')
    rgb /= rgb.max(['x', 'y']) # Brightens image

    # Convert to pixel coords for easier plotting
    rgb['x'] = range(rgb.x.size)
    rgb['y'] = range(rgb.y.size)

    # Retrieve the pixels that will be plotted
    if not pixels:
        pixels = findInterestingPixels(rgb.mean('band'), seed)
    pixels = pixels[:3]
    print(f"Interesting pixels using seed {seed}: {pixels}")

    fig = plt.figure(figsize=(30, 10))
    grid = gridspec.GridSpec(ncols=2, nrows=len(pixels), wspace=-0.1, hspace=0.2)

    if title:
        fig.suptitle(title, fontsize=32)

    # Plot the RGB data as an image
    img = fig.add_subplot(grid[:, 0])
    img.imshow(rgb)
    img.set_title("RGB of RFL")

    # Now plot three spectras
    for i, pixel in enumerate(pixels):
        plotSpectra(fig.add_subplot(grid[i, 1]),
            data  = da,
            pixel = pixels[i],
            color = Colors[i],
            hideX = i+1 < len(pixels),
            annotate = img,
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
@click.option("-s", "--seed", type=int)
@click.option("-p", "--pixels", multiple=True, nargs=2, type=int)
def cli(**kwargs):
    print("Plotting spectra")

    plot(**kwargs)

    print("Finished")


if __name__ == "__main__":
    cli()
