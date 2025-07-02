import logging
import re
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import xarray as xr
from nicegui import (
    observables,
    run,
    ui
)

from isofit.radiative_transfer import luts
from isoplots.isonice import (
    WD,
    utils
)


Logger = logging.getLogger("LUTs")

Name = "LUTs"
Icon = "ssid_chart"
Prio = 2


class MultiPlotLUT:
    """
    Handles the construction and management of a single LUT plotting card in the LUTs
    tab
    """
    def __init__(self, parent, files=None, cache=None):
        """
        Parameters
        ----------
        parent : LUT
            Parent LUT class that hosts this object
        files : list, default=None
            Shared NiceGUI observables for the files options, otherwise will be an
            independent list
        cache : dict, default=None
            Shared cache dict if provided, otherwise creates one for this object
        """
        self.parent = parent

        if files is None:
            files = observables.ObservableList([], on_change=self.setOptions)
        self.files = files

        if cache is None:
            cache = {}
        self.cache = cache

        self.main = self.new
        self.plots = [self.main]

        # Defaults
        self.quant = None
        self.dim = "None"

        with ui.card().classes("w-full border"):
            with ui.column().classes("w-full"):
                with ui.row().classes("w-full items-center") as self.header:
                    self.main["select"] = ui.select(
                        label = "LUT File",
                        options = self.files,
                        multiple = False, # TODO?
                        new_value_mode = "add-unique",
                        on_change = lambda e: self.changeFile(e.value)
                    ).classes("w-[56%]").props('use-chips')

                    self.quants = ui.select(
                        label = "Select a LUT quantity",
                        options = [],
                        on_change = lambda e: self.changeQuant(e.value)
                    ).classes("w-[15%]")
                    self.quants.disable()

                    self.dims = ui.select(
                        label = "Select a LUT dimension",
                        options = [],
                        on_change = lambda e: self.changeDim(e.value)
                    ).classes("w-[15%]")
                    self.dims.disable()

                    ui.button(
                        icon = "question_mark",
                        # on_click = lambda: self.deleteSubplot(plot),
                    ).props("outline round") \
                    .classes("ml-auto") \
                    .tooltip("Select a LUT file or provide a path to a LUT file to load the quantities. Then select a quantity to load the dimensions. Finally, select a dimension to plot.")

                    ui.button(
                        icon = "add",
                        on_click = self.createSubplot,
                    ).props("outline round") \
                    .classes("ml-auto") \
                    .tooltip("Add subplot. This will share X and Y axes as well as quantity and dimension with the main plot")

                    ui.button(
                        icon = "close",
                        on_click = lambda: parent.deletePlot(self)
                    ).props("outline round") \
                    .classes("ml-auto") \
                    .tooltip("Removes this entire plot group")

                # Relative wrapper to control layering
                with ui.element().classes("relative w-full") as self.column:
                    # Loading overlay
                    with ui.card().classes("absolute inset-0 z-10 flex items-center justify-center bg-white/70") as self.loading:
                        ui.spinner(size='xl')
                    self.loading.visible = False

                    # Plotly figure
                    self.ui = ui.plotly(utils.multiplot()).classes("w-full")

    @property
    def new(self):
        """
        Creates a dict with default values to be used for a new plot

        Returns
        -------
        dict
            Default values for a new plot
        """
        return {
            "plot": utils.blank(),
            "lut": None,
            "select": None,
        }

    def load(self, file):
        """
        Loads a LUT dataset and stores it in the cache

        Parameters
        ----------
        file : str
            Path to a LUT file to load. If the path does not exist, will attempt to
            find it under the WD

        Returns
        -------
        xr.Dataset
            Loaded LUT dataset
        """
        self.loading.visible = True

        Logger.debug(f"Loading path: {file}")
        if file not in self.cache:
            if Path(file).exists():
                try:
                    self.cache[file] = luts.load(file).unstack()
                except Exception as e:
                    Logger.exception(f"Failed to load via luts.py")
            else:
                try:
                    self.cache[file] = WD.load(path=file).unstack()
                except Exception as e:
                    Logger.exception(f"Failed to load via WD")

        self.loading.visible = False

        return self.cache.get(file)

    def setOptions(self, *_):
        """
        Updates each file selection dropdown with the self.files list
        This is called each time the list is updated
        """
        for plot in self.plots:
            plot["select"].set_options(self.files)

    async def createSubplot(self):
        """
        Adds a new subplot to the figure
        """
        plot = self.new
        self.plots.append(plot)

        with self.header:
            with ui.row().classes("w-full items-center"):
                plot["select"] = ui.select(
                    label = f"LUT File for Plot {len(self.plots)}",
                    options = self.files,
                    new_value_mode = "add-unique",
                    on_change = lambda e: self.updateSubplot(plot, file=e.value)
                ).classes("w-[96%]")

                ui.button(
                    icon = "close",
                    on_click = lambda: self.deleteSubplot(plot),
                ).props("outline round").tooltip("Remove subplot").classes("ml-auto")

        # Shift to bottom of the card
        # self.ui.move(target_index=-1)

        # Update the figure with a blank
        await self.updateUI()

    async def updateSubplot(self, plot, file):
        """
        Updates a subplot with a new LUT input

        Parameters
        ----------
        plot : dict
            Plot data dict
        file : str
            LUT file to load
        """
        lut = await run.io_bound(self.load, file)
        if lut is None:
            return

        plot["lut"] = lut
        plot["plot"] = await self.plot(
            lut   = plot["lut"],
            quant = self.quant,
            dim   = self.dim
        )
        await self.updateUI()

    async def deleteSubplot(self, plot):
        """
        Deletes a subplot and removes it from the UI

        Parameters
        ----------
        plot : dict
            Plot data dict
        """
        i = self.plots.index(plot)
        self.header.remove(i+5) # 5 to skip the primary header components
        self.plots.pop(i)

        await self.updateUI()

        # Update labels for consistency
        for i, plot in enumerate(self.plots[1:]):
            plot["select"].props(f'label="LUT File for Plot {i+2}"')

    async def changeFile(self, file):
        """
        Changes the primary LUT dataset and updates the quantities list

        Parameters
        ----------
        file : str
            Path to LUT file to load
        """
        self.quants.disable()
        self.dims.disable()

        lut = await run.io_bound(self.load, file)
        if lut is None:
            return

        self.main["lut"] = lut

        # Update the quantities list
        plottable = set(lut) - set(lut.drop_dims("wl"))
        if plottable:
            self.quants.set_options(sorted(plottable))
            self.quants.enable()

        # Reset the quant selection
        self.quants.set_value(None)

    async def changeQuant(self, quant):
        """
        Changes the selected quantity from the active main LUT file and updates the
        dimensions list

        Parameters
        ----------
        quant : str
            Quantity of the LUT to plot
        """
        self.quant = quant

        lut = self.main["lut"]

        # Discover the available dims
        dims = []
        if quant in lut:
            dims = set(lut[quant].dims) - {"wl",}

        # Set them as the options, including "None" to average over all dims
        self.dims.set_options(["None"] + sorted(dims))

        if dims:
            self.dims.enable()
        else:
            self.dims.disable()

        # Attempt to re-plot with the last chosen dim
        if self.dim != self.dims.value:
            self.dims.set_value(self.dim)
        else:
            await self.changeDim(self.dim)

    async def changeDim(self, dim):
        """
        Changes the plotting dimension

        Parameters
        ----------
        dim : str
            Dimension to plot along. All other dimensions will be squeezed to the mean
        """
        self.dim = dim

        # Update all plots
        for plot in self.plots:
            plot["plot"] = await self.plot(
                lut   = plot["lut"],
                quant = self.quant,
                dim   = self.dim
            )

        await self.updateUI()

    async def plot(self, lut, quant, dim):
        """
        Attempts to create a LUT plot. If it fails, returns a blank figure

        Parameters
        ----------
        lut : xr.Dataset
            LUT data object
        quant : str
            Quantity to select
        dim : str
            Dimension to plot along. All other dimensions will be averaged

        Returns
        -------
        go.Figure
            Either the plotted figure or a blank if it failed
        """
        self.loading.visible = True

        try:
            data = lut[quant]
            dims = set(data.coords) - {"wl", dim}

            if dims:
                mean = data.mean(dims, skipna=True)
                data = mean.rename(wl="Wavelength")

                # Split each value of the dim into its own variable
                if dim != "None":
                    data = data.to_dataset(dim)

            df = data.to_dataframe()

            return px.line(df,
                template = "plotly_dark",
                labels = {"variable": str(dim)}
            )
        except:
            Logger.exception(f"Failed to plot {quant}[{dim}]")
            return utils.blank()
        finally:
            self.loading.visible = False

    async def updateUI(self):
        """
        Updates the GUI with a newly constructed multi-plot figure
        """
        plots = [plot["plot"] for plot in self.plots]
        fig = utils.multiplot(plots)
        self.ui.update_figure(fig)


class Tab:
    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        # Stores MultiPlotLUT objects
        self.plots = []

        # Shared LUT cache
        self.cache = {}

        # Shared file options
        self.files = observables.ObservableList([], on_change=self.setOptions)

        with ui.scroll_area().classes("h-full w-full") as self.scroll:
            self.addPlotBtn = ui.button(
                "Add New Independent Plot",
                on_click = self.asyncCreatePlot
            ).classes("w-full") \
            .props("outline")

        # Create an initial plot
        self.createPlot()

    async def setOptions(self, *_):
        """
        Calls each MultiPlotLUT to set the file options

        This function is called any time the self.files list is updated, such as when
        the WD is changed or a manual input is given
        """
        for plot in self.plots:
            plot.setOptions()

    def createPlot(self):
        """
        Creates a new plot group using the MultiPlotLUT class
        """
        with self.scroll:
            plot = MultiPlotLUT(self, files=self.files, cache=self.cache)
            self.plots.append(plot)

        # Move the button to the bottom
        self.addPlotBtn.move(target_index=-1)

    async def asyncCreatePlot(self):
        """
        Async wrapper for createPlot
        """
        self.createPlot()

    async def deletePlot(self, plot):
        """
        Removes a plot group from the interface permanently

        Parameters
        ----------
        plot : MultiPlotLUT
            Card to be removed
        """
        i = self.plots.index(plot)
        self.scroll.remove(i)
        self.plots.pop(i)

    async def reset(self, *_):
        """
        Resets the the file options when the WD changes
        """
        self.files.clear()
        self.files += await run.io_bound(WD.find, "lut/.nc", all=True)
        self.files.sort()
