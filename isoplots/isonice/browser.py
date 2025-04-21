"""
Usage:
    1. pip install nicegui
    2. python isonice/isofit.py
    3. Acknowledge this is a WORK IN PROGRESS
"""
import json
import logging
import re
from pathlib import Path
from types import SimpleNamespace

import plotly.express as px
import plotly.graph_objects as go
import xarray as xr

from nicegui import observables, run, ui

from isofit.radiative_transfer import luts

# TODO: This will source from isofit once the PR is accepted
try:
    from isofit.utils.wd import IsofitWD
except:
    from isoplots.isonice.wd import IsofitWD

# Global shared working directory
WD = IsofitWD(".")

dark = ui.dark_mode()
dark.enable()

ui.context.client.content.classes('h-screen')
ui.add_head_html('''
    <style type="text/css">
    .nicegui-content {
        padding: 0;
    }
    .flex-grow .q-field__control {
        height: 100%;
    }
    .jse-theme-dark {
      --jse-theme: dark;

      /* over all fonts, sizes, and colors */
      --jse-theme-color: #2f6dd0;
      --jse-theme-color-highlight: #467cd2;
      --jse-background-color: #1e1e1e;
      --jse-text-color: #d4d4d4;
      --jse-text-color-inverse: #4d4d4d;

      /* main, menu, modal */
      --jse-main-border: 1px solid #4f4f4f;
      --jse-menu-color: #fff;
      --jse-modal-background: #2f2f2f;
      --jse-modal-overlay-background: rgba(0, 0, 0, 0.5);
      --jse-modal-code-background: #2f2f2f;

      /* tooltip in text mode */
      --jse-tooltip-color: var(--jse-text-color);
      --jse-tooltip-background: #4b4b4b;
      --jse-tooltip-border: 1px solid #737373;
      --jse-tooltip-action-button-color: inherit;
      --jse-tooltip-action-button-background: #737373;

      /* panels: navigation bar, gutter, search box */
      --jse-panel-background: #333333;
      --jse-panel-background-border: 1px solid #464646;
      --jse-panel-color: var(--jse-text-color);
      --jse-panel-color-readonly: #737373;
      --jse-panel-border: 1px solid #3c3c3c;
      --jse-panel-button-color-highlight: #e5e5e5;
      --jse-panel-button-background-highlight: #464646;

      /* navigation-bar */
      --jse-navigation-bar-background: #656565;
      --jse-navigation-bar-background-highlight: #7e7e7e;
      --jse-navigation-bar-dropdown-color: var(--jse-text-color);

      /* context menu */
      --jse-context-menu-background: #4b4b4b;
      --jse-context-menu-background-highlight: #595959;
      --jse-context-menu-separator-color: #595959;
      --jse-context-menu-color: var(--jse-text-color);
      --jse-context-menu-pointer-background: #737373;
      --jse-context-menu-pointer-background-highlight: #818181;
      --jse-context-menu-pointer-color: var(--jse-context-menu-color);

      /* contents: json key and values */
      --jse-key-color: #9cdcfe;
      --jse-value-color: var(--jse-text-color);
      --jse-value-color-number: #b5cea8;
      --jse-value-color-boolean: #569cd6;
      --jse-value-color-null: #569cd6;
      --jse-value-color-string: #ce9178;
      --jse-value-color-url: #ce9178;
      --jse-delimiter-color: #949494;
      --jse-edit-outline: 2px solid var(--jse-text-color);

      /* contents: selected or hovered */
      --jse-selection-background-color: #464646;
      --jse-selection-background-inactive-color: #333333;
      --jse-hover-background-color: #343434;
      --jse-active-line-background-color: rgba(255, 255, 255, 0.06);
      --jse-search-match-background-color: #343434;

      /* contents: section of collapsed items in an array */
      --jse-collapsed-items-background-color: #333333;
      --jse-collapsed-items-selected-background-color: #565656;
      --jse-collapsed-items-link-color: #b2b2b2;
      --jse-collapsed-items-link-color-highlight: #ec8477;

      /* contents: highlighting of search results */
      --jse-search-match-color: #724c27;
      --jse-search-match-outline: 1px solid #966535;
      --jse-search-match-active-color: #9f6c39;
      --jse-search-match-active-outline: 1px solid #bb7f43;

      /* contents: inline tags inside the JSON document */
      --jse-tag-background: #444444;
      --jse-tag-color: #bdbdbd;

      /* contents: table */
      --jse-table-header-background: #333333;
      --jse-table-header-background-highlight: #424242;
      --jse-table-row-odd-background: rgba(255, 255, 255, 0.1);

      /* controls in modals: inputs, buttons, and `a` */
      --jse-input-background: #3d3d3d;
      --jse-input-border: var(--jse-main-border);
      --jse-button-background: #808080;
      --jse-button-background-highlight: #7a7a7a;
      --jse-button-color: #e0e0e0;
      --jse-button-secondary-background: #494949;
      --jse-button-secondary-background-highlight: #5d5d5d;
      --jse-button-secondary-background-disabled: #9d9d9d;
      --jse-button-secondary-color: var(--jse-text-color);
      --jse-a-color: #55abff;
      --jse-a-color-highlight: #4387c9;

      /* svelte-select */
      --jse-svelte-select-background: #3d3d3d;
      --jse-svelte-select-border: 1px solid #4f4f4f;
      --list-background: #3d3d3d;
      --item-hover-bg: #505050;
      --multi-item-bg: #5b5b5b;
      --input-color: #d4d4d4;
      --multi-clear-bg: #8a8a8a;
      --multi-item-clear-icon-color: #d4d4d4;
      --multi-item-outline: 1px solid #696969;
      --list-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.4);

      /* color picker */
      --jse-color-picker-background: #656565;
      --jse-color-picker-border-box-shadow: #8c8c8c 0 0 0 1px;
    }

    </style>
''')

# Optional hard-coded output directories which will be added as buttons to quickly switch/load them
WORKING_DIRS = {
    # "NEON": "/Users/jamesmo/projects/isofit/research/NEON.bak/output/NIS01_20210403_173647/",
    # "emit": "/Users/jamesmo/projects/isofit/research/jemit/",
    # "Pasadena": "/Users/jamesmo/projects/isofit/extras/examples/20171108_Pasadena",
    # "Test6": "/Users/jamesmo/Downloads/firefox/Test6"
}


def plotlyColor(i):
    c = px.colors.qualitative.Plotly
    return c[i % len(c)]


class Logs:
    colors = {
        "DEBUG"    : "grey",
        "INFO"     : "cyan",
        "WARNING"  : "yellow",
        "ERROR"    : "red",
        "EXCEPTION": "magenta"
    }

    logs = None

    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        with ui.column().classes("h-screen w-full"):
            with ui.expansion("Settings & Stats", value=True).classes("w-full"):
                ui.chip(
                    "Logs are loaded on-demand as they can cause the UI to lag. It is recommended to toggle off each option when done.",
                    icon  = "warning",
                    color = "yellow"
                ).props('outline square')

                self.levels = ui.card().classes("border")

            self.lines = ui.element().classes("nicegui-log h-full")

    async def reset(self, isofit=None):
        self.lines.clear()
        self.levels.clear()

        if isofit:
            self.logs = isofit.logs

        try:
            self.logs.parse()
            self.logs.filter(None)
            self.logs.build()

            self.populateLogs()
            self.populateLevels()
        except Exception as e:
            print(f"Failed to load logs: {e}")
            self.logs = None
            with self.lines:
                ui.chip(
                    "No log file found or could not parse. If it is outside of the directory, place it somewhere inside with the extension .log",
                    icon  = "error",
                    color = "red"
                ).classes("w-full")

    def toggle(self, event):
        self.logs.toggle(event.sender.text, event.value)
        self.logs.build()
        self.populateLogs()

    def populateLevels(self):
        self.levels.clear()
        with self.levels:
            for key, value in self.logs.format.items():
                ui.switch(key, value=value, on_change=self.toggle)
            for level, value in self.logs.selected.items():
                ui.switch(level, value=value, on_change=self.toggle)

    def populateLogs(self):
        self.lines.clear()
        with self.lines:
            for (ts, lvl, msg) in self.logs.lines:
                # color = self.logs.colors[lvl]
                color = self.colors.get(lvl.strip(), "white")
                with ui.row():
                    ui.label(ts).classes("text-orange")
                    ui.label(lvl).classes(f"text-{color}")
                    ui.label(msg)


class Spectra:
    plot = None
    data = None
    opts = None

    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        with ui.splitter(value=30).classes("w-full h-full") as splitter:
            with splitter.before:
                with ui.card().classes("w-full border"):
                    with ui.row().classes("w-full"):
                        ui.button("Reset", on_click=self.reset).classes("w-20 h-full")
                        self.select = ui.select([], label="Select data file", on_change=self.changeFile).classes("w-60")
                        with ui.icon("info", size="md").classes("w-20 h-full"):
                            with ui.tooltip():
                                ui.label("Choose a file on the left to plot the RGB image below")
                                ui.label("Click on the image to plot spectra on the right")
                                ui.label("Click on the same point again to delete it")
                                ui.label("Some files may not be compatible")

                # Generic placeholder figure
                self.setImage(go.Figure())

                self.plot = ui.plotly(self.img).classes('w-full h-full')

                # Override the event to delete the source string which crashes the server when the image is too large
                self.plot.on('plotly_click', js_handler="""
                    (event) => {
                        event.points.forEach(point => delete point.data.source);
                        return emitEvent('clickedPoint', event);
                    };
                """)
                ui.on('clickedPoint', self.addAnotation)
            with splitter.after:
                self.spectras = ui.scroll_area().classes("h-full w-full border")

    async def reset(self, isofit=None):
        # if isofit and isofit.data:
        #     self.data = isofit.data
        if isofit:
            self.isofit = isofit

        if self.isofit:
            self.spectras.clear()

            # opts = [file.name for file in self.data.getOutputs()]
            # opts = [f"{self.data.name}_rfl"]
            # opts = [f"{self.isofit.output.name}_rfl"]
            opts = WD.output.find("rfl", exc="subs", all=True)

            if opts != self.opts:
                self.opts = opts

                # Always default to the full RFL data
                # self.select.set_options(opts, value=opts[0])
                self.select.set_options(opts)
                if opts:
                    self.select.set_value(opts[0])
            else:
                self.plotImage(self.rgb)

    async def changeFile(self, event):
        file = event.value
        # data = self.data.load(name=file)
        # data = await run.io_bound(self.data.load, name=file)
        # if "_subs" in file:
        #     self.rgb = await run.io_bound(self.data.subs.rgb)
        # else:
        # self.rgb = await run.io_bound(self.data.full.rgb)
        self.rgb = await run.io_bound(self.isofit.output.rgb)
        self.rfl = await run.io_bound(self.isofit.output.load, path=event.value)

        self.plotImage(self.rgb)

    def setImage(self, figure):
        self.img = figure
        figure.update_layout(
            margin = dict(l=0, r=20, t=0, b=0),
            # plot_bgcolor  = "rgba(0, 0, 0, 0)",
            paper_bgcolor = "rgba(0, 0, 0, 0)",
            showlegend    = False
        )
        if self.plot:
            self.plot.update_figure(figure)

    def plotImage(self, rgb):
        # rgb = await run.io_bound(self.data.rgb)
        try:
            img = px.imshow(rgb, template="plotly_dark")
        except Exception as e:
            print(f"Failed to plot spectra image, reason: {e}")
            img = go.Figure()

        self.setImage(img)

    def addAnotation(self, event):
        # Images will only ever have 1 point returned
        point = event.args['points'][0]
        data = point['data']

        if data['type'] == "image":
            i = len(self.img.data)
            y, x = point['pointIndex']

            self.img.add_trace(go.Scatter(
                x = [x],
                y = [y],
                mode = "markers+text",
                name = f"Spectra {i} @ ({x}, {y})",
                text = [str(i)],
                marker = {"symbol": "circle-open"},
                textposition = "top center",
            ))
            self.plotSpectra(i, x, y)

        elif data['type'] == "scatter":
            i = point['curveNumber']

            data = list(self.img.data)
            data.pop(i)
            self.img.data = data

            # Update names and texts
            for trace in self.img.data[i:]:
                pos = int(trace.text[0])
                new = str(pos-1)
                trace.name = re.sub(r"(\d+) @", f"{new} @", trace.name)
                trace.text = [new]

            # Remove the corresponding spectra plot
            self.spectras.remove(i-1)

            # Update titles and colors
            for i, spectra in enumerate(self.spectras):
                i += 1 # Always +1 because 0 is the image data
                trace = data[i]
                spectra.figure.update_layout(
                    title = {
                        'text': trace.name
                    }
                )
                spectra.figure.update_traces(
                    line = {
                        'color': plotlyColor(i)
                    }
                )
                spectra.update()

        self.plot.update()

    def plotSpectra(self, i, x, y):
        with self.spectras:
            spectra = self.rfl.isel(x=x, y=y)
            # spectra = spectra.rename(band_data='Reflectance', wavelength='Wavelength')
            spectra.name = "Reflectance"
            spectra = spectra.rename(wavelength='Wavelength')
            spectra = spectra.where(spectra != spectra.min())
            # data = spectra.Reflectance
            df = spectra.to_dataframe()

            # Remove min values

            fig = px.line(df,
                x = 'Wavelength',
                y = 'Reflectance',
                height   = 300,
                template = "plotly_dark",
                title = f"Spectra {i} @ ({x}, {y})",
                # color = Colors[i % len(Colors)]
            )
            fig.update_layout(
                margin = dict(l=0, r=0, t=30, b=0),
                # plot_bgcolor  = "rgba(0, 0, 0, 0)",
                paper_bgcolor = "rgba(0, 0, 0, 0)",
                # showlegend    = True
            )
            fig.update_traces(
                line = {
                    'color': plotlyColor(i)
                }
            )

            plot = ui.plotly(fig).classes("w-full")


class Config:
    data = None

    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        with ui.row():
            self.select = ui.select([], label="Select a Configuration", on_change=self.loadConfig)
            ui.switch("Editable", value=False, on_change=self.readOnly).classes("h-full")

        self.editor = ui.json_editor({'content': {'json': {}}, 'readOnly': True}).classes('w-full jse-theme-dark')

    async def reset(self, isofit=None):
        if isofit:
            self.isofit = isofit
            configs = isofit.find("config/.json", all=True)
            self.select.set_options(configs, value=configs[0])

    def loadConfig(self, event):
        data = self.isofit.load(path=event.value)
        self.editor.run_editor_method('updateProps', {'content': {'json': data}})

    def readOnly(self, event):
        self.editor.run_editor_method('updateProps', {'readOnly': not event.value})


#%%

def multiplot(figs=[], height=300):
    """
    Creates a multi plot object that shares X and Y axes

    Parameters
    ----------
    figs : list[go.Figure]
        List of subplots to add
    height : int, default=300
        Height of each subplot

    Returns
    -------
    fig : go.Figure
        Plotly figure with one or more subplots
    """
    # Ensure at least one figure is set
    if not figs:
        figs = [go.Figure()]

    fig = go.Figure()
    fig.set_subplots(
        rows = len(figs),
        cols = 1,
        shared_xaxes = 'all',
        shared_yaxes = 'all',
        vertical_spacing = 0.01
    )
    fig.update_layout(**{
        "margin": dict(l=0, r=20, t=0, b=0),
        "paper_bgcolor": "rgba(0, 0, 0, 0)",
        "template": "plotly_dark",
        "height": height*len(figs),
    })

    for i, plot in enumerate(figs):
        for trace in plot.data:
            # fig.update_layout(legendgroup=f"{i+1}")
            fig.add_trace(trace, row=i+1, col=1)

    # TODO: Get subplots to have their own legends
    # Does not work
    try:
        for i, yaxis in enumerate(fig.select_yaxes()):
            i += 1
            legend_name = f"legend{i}"
            if yaxis.domain is not None:
                fig.update_layout({legend_name: dict(y=yaxis.domain[1], yanchor="top")}, showlegend=True)
                fig.update_traces(row=i, legend=legend_name)
    except:
        pass

    return fig

#%%

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
        self.dim = None

        with ui.card().classes("w-full border"):
            with ui.column().classes("w-full") as self.column:
                with ui.row().classes("w-full items-center"):

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

                self.ui = ui.plotly(multiplot()).classes("w-full")

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
            "plot": self.blank,
            "lut": None,
            "select": None
        }

    @property
    def blank(self):
        """
        Creates a blank plotly figure with an empty scatter trace so that it renders
        the plot in the GUI. Without the scatter, the plot will be invisible

        Returns
        -------
        go.Figure
            Blank plotly figure
        """
        return go.Figure(go.Scatter())

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
        if file not in self.cache:
            if Path(file).exists():
                print(f"Loading given LUT: {file}")
                try:
                    self.cache[file] = luts.load(file).unstack()
                except Exception as e:
                    print(f"Failed to load, reason: {e}")
            else:
                print(f"Loading LUT from WD: {file}")
                try:
                    self.cache[file] = WD.load(path=file).unstack()
                except Exception as e:
                    print(f"Failed to load, reason: {e}")

        return self.cache.get(file)

    def setOptions(self, *_):
        """
        Updates each file selection dropdown with the self.files list
        This is called each time the list is updated
        """
        for plot in self.plots:
            plot["select"].set_options(self.files)

    def createSubplot(self):
        """
        Adds a new subplot to the figure
        """
        plot = self.new
        self.plots.append(plot)

        with self.column:
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
        self.ui.move(target_index=-1)

        # Update the figure with a blank
        self.updateUI()

    def updateSubplot(self, plot, file):
        """
        Updates a subplot with a new LUT input

        Parameters
        ----------
        plot : dict
            Plot data dict
        file : str
            LUT file to load
        """
        if (lut := self.load(file)) is None:
            return

        plot["lut"] = lut
        plot["plot"] = self.plot(
            lut   = plot["lut"],
            quant = self.quant,
            dim   = self.dim
        )
        self.updateUI()

    def deleteSubplot(self, plot):
        """
        Deletes a subplot and removes it from the UI

        Parameters
        ----------
        plot : dict
            Plot data dict
        """
        i = self.plots.index(plot)
        self.column.remove(i)
        self.plots.pop(i)
        self.updateUI()

        # Update labels for consistency
        for i, plot in enumerate(self.plots[1:]):
            plot["select"].props(f'label="LUT File for Plot {i+2}"')

    def changeFile(self, file):
        """
        Changes the primary LUT dataset and updates the quantities list

        Parameters
        ----------
        file : str
            Path to LUT file to load
        """
        self.quants.disable()
        self.dims.disable()

        if (lut := self.load(file)) is None:
            return

        self.main["lut"] = lut

        # Update the quantities list
        plottable = set(lut) - set(lut.drop_dims("wl"))
        if plottable:
            self.quants.set_options(sorted(plottable))
            self.quants.enable()

        # Reset the quant selection
        self.quants.set_value(None)

    def changeQuant(self, quant):
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

        dims = []
        if quant in lut:
            dims = set(lut[quant].dims) - {"wl",}

        self.dims.set_options(sorted(dims))

        if dims:
            self.dims.enable()
        else:
            self.dims.disable()

        # Attempt to re-plot with the last chosen dim
        self.changeDim(self.dim)

    def changeDim(self, dim):
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
            plot["plot"] = self.plot(
                lut   = plot["lut"],
                quant = self.quant,
                dim   = self.dim
            )

        self.updateUI()

    def plot(self, lut, quant, dim):
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
        try:
            data = lut[quant]
            dims = set(data.coords) - {"wl", dim}
            mean = data.mean(dims, skipna=True)
            mean = mean.rename(wl="Wavelength")

            # Split each value of the dim into its own variable
            mean = mean.to_dataset(dim)
            df = mean.to_dataframe()

            return px.line(df,
                template = "plotly_dark",
                labels = {"variable": dim}
            )
        except Exception as e:
            print(f"Failed to plot {quant}[{dim}], reason: {e}")
            return self.blank

    def updateUI(self):
        """
        Updates the GUI with a newly constructed multi-plot figure
        """
        plots = [plot["plot"] for plot in self.plots]
        fig = multiplot(plots)
        self.ui.update_figure(fig)


class LUTs:
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
                on_click = self.createPlot
            ).classes("w-full") \
            .props("outline")

        # Create an initial plot
        self.createPlot()

    def setOptions(self, *_):
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

    def deletePlot(self, plot):
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

        # Retrieve the known LUT files of this WD
        luts = {
            name: obj
            for name, obj in WD.dirs.items()
            if isinstance(obj, WD.classes["lut"])
        }

        for name, lut in luts.items():
            self.files += [
                f"{name}/{file}"
                for file in lut.find("lut", all=True)
            ]

        self.files.sort()


def toNiceGUITree(tree, *, nodes=None):
    """
    Recursively converts an IsofitWD tree (with info) into a NiceGUI-compatible data
    structure for the tree component

    Parameters
    ----------
    tree : dict
        Tree object created by IsofitWD.getTree(info=True)
    nodes : list, default=None
        Converted nodes for the tree component, this likely should be left as the
        default

    Returns
    -------
    nodes : list
        Converted nodes for the tree component
    """
    if nodes is None:
        nodes = [{"id": "root", "desc": None, "children": []}]
        toNiceGUITree(tree, nodes=nodes[-1]["children"])
    else:
        for info, path in tree.items():
            if isinstance(path, dict):
                nodes.append({"id": info.name, "desc": info.info, "children": []})
                toNiceGUITree(path, nodes=nodes[-1]["children"])
            else:
                for file in path:
                    nodes.append({"id": file.name, "desc": file.info})
    return nodes


class EnhancedTree(ui.tree):
    @property
    def root(self):
        return self.props["nodes"]

    @property
    def branches(self):
        """
        Returns branch nodes, no leaves

        Yields
        ------
        branch : dict
            A branch node
        """
        for branch in self.root:
            if "children" in branch:
                yield branch

    def traverse(self, func, id):
        """
        Traverses the branches applying the given function until a value is found

        Parameters
        ----------
        func : function
            Function to call
        id : str
            ID of the node to find

        Returns
        -------
        any
            If the called function returns a value, returns that value
        """
        for branch in self.branches:
            if value := func(id, branch=branch):
                return value

    def getPath(self, id, *, branch=None):
        """
        Recursively discover the string path to a given node ID

        Parameters
        ----------
        id : str
            ID of the node to find
        branch : dict
            Branch of the tree being worked on

        Returns
        -------
        str
            String path, eg. "configs/topoflux/config.json"
        """
        if branch is None:
            return self.traverse(self.getPath, id)
            # for branch in self.branches:
            #     if path := self.getPath(id, branch=branch):
            #         return path

        for node in branch["children"]:
            if node["id"] == id:
                return id
            elif "children" in node:
                if path := self.getPath(id, branch=node):
                    return f"{node['id']}/{path}"

    def findNode(self, id, *, branch=None):
        """
        Find the source node for a given ID

        Parameters
        ----------
        id : str
            ID of the node to find
        branch : dict
            Branch of the tree being worked on

        Returns
        -------
        str
            String path, eg. "configs/topoflux/config.json"
        """
        if branch is None:
            return self.traverse(self.findNode, id)
            # for branch in self.branches:
            #     if node := self.findNode(id, branch=branch):
            #         return node

        for node in branch["children"]:
            if node["id"] == id:
                return node
            elif "children" in node:
                node = self.findNode(id, branch=node)
                if node:
                    return node

    def findSiblings(self, id, *, branch=None):
        """
        Finds the IDs of the sibling nodes in the tree

        Parameters
        ----------
        id : str
            ID of the node to find
        branch : dict
            Branch of the tree being worked on

        Returns
        -------
        str
            String path, eg. "configs/topoflux/config.json"
        """
        if branch is None:
            return self.traverse(self.findSiblings, id)
            # for branch in self.branches:
            #     if siblings := self.findSiblings(id, branch=branch):
            #         return siblings

        # Get the sibling directories of the source node
        nodes = branch["children"]
        siblings = [node["id"] for node in nodes if "children" in node]

        if id in siblings:
            return siblings

        # Try to find it in some child
        for node in nodes:
            if "children" in node:
                if siblings := self.findSiblings(id, branch=node):
                    return siblings


class Setup:
    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        if WORKING_DIRS:
            setWD = lambda e: self.directory.set_value(WORKING_DIRS[e.sender.text])
            with ui.row():
                for name, path in WORKING_DIRS.items():
                    if not Path(path).exists():
                        print(f"Path not found: {path}")
                        continue
                    ui.button(name, on_click=setWD)

        self.directory = ui.input("Working Directory or Configuration JSON",
            validation = self.setIsofit,
        ).classes("w-full")

        self.directoryTree = ui.scroll_area().classes("w-full h-full")

    async def reset(self, isofit=None):
        ...

    def setIsofit(self, value):
        self.directoryTree.clear()

        # Try to parse the input path
        # try:
        #     isofit = IsofitOutput(value)
        #     self.parent.isofit = isofit
        #     # self.isofit.changePath(value)
        # except Exception as e:
        #     # Output to UI the error
        #     self.parent.toggleTabs(all=False)
        #     return str(e)
        WD.reset(value)
        isofit = IsofitWD(value)
        self.parent.isofit = isofit
        # if not self.isofit.dirs:
        #     return "Could not parse as a valid ISOFIT output directory"

        self.parent.toggleTabs(all=True)

        # Set the output directory tree
        with self.directoryTree:
            data = isofit.getTree(info=True)
            data = toNiceGUITree(data)

            # ui.label("Click on an output file below to jump to an interactive component for that file [Work in Progress]")
            # ui.label("Detected paths:")

            self.tree = EnhancedTree(data, on_select=lambda e: self.navToFile(e)).classes("border h-full w-full")
            self.tree.expand(["root"])
            self.tree.add_slot('default-header', '''
                <span :props="props">{{ props.node.id }}</strong></span>
            ''')
            self.tree.add_slot('default-body', '''
                <span :props="props">{{ props.node.desc }}</span>
            ''')

    def navToFile(self, event):
        """
        TODO

        Parameters
        ----------
        event
        """
        name = event.value

        # Find the source node clicked
        # node = self.tree.findNode(name)

        if node := self.tree.findNode(name):
            if "children" in node:
                # siblings = findSiblings(root)
                siblings = self.tree.findSiblings(name)

                self.tree.collapse(siblings)
                self.tree.expand([name])
            else:
                # Get the string path to the node
                path = Path(self.tree.getPath(name))

                if len(path.parents) > 1:
                    dir = path.parents[-2]
                    path = path.relative_to(dir)

                    # self.parent.navToFile(dir, path)
                else:
                    print("Cannot load files on the base")

#%%

class Tabs:
    isofit = None

    default = "setup"
    valid = {
        "config" : False,
        "logs"   : False,
        "spectra": False,
        "luts"   : False,
    }
    tabs = {
        "setup"  : Setup,
        "config" : Config,
        "logs"   : Logs,
        "spectra": Spectra,
        "luts"   : LUTs,
    }
    reset = {}

    def __init__(self):
        with ui.dialog() as self.loading:
            # self.loading.on("click", lambda _: ...)
            ui.spinner(size="lg")

        with ui.splitter(value=5).classes("w-full h-full") as splitter:
            with splitter.before:
                with ui.tabs().props('vertical').classes('w-full h-full') as tabs:
                    self.btns = {
                        "setup"  : ui.tab('setup',   icon='home'),
                        "config" : ui.tab('config',  icon='settings'),
                        "logs"   : ui.tab('logs',    icon='density_small'),
                        "spectra": ui.tab('spectra', icon='show_chart'),
                        "luts"   : ui.tab('luts',    icon='ssid_chart'),
                    }
            with splitter.after:
                self.pnls = {}

                with ui.tab_panels(tabs, value=self.btns[self.default], on_change=self.tabSelected).classes('w-full h-full') as self.panels:
                    with self.panels:
                        for name, btn in self.btns.items():
                            with ui.tab_panel(btn) as self.pnls[name]:
                                # Initialize the objects
                                self.tabs[name] = self.tabs[name](self)

        self.toggleTabs()

    async def tabSelected(self, event):
        self.loading.open()

        tab = event.value
        if self.reset[tab]:
            self.reset[tab] = False
            await self.tabs[tab].reset(self.isofit)

        self.loading.close()

    def resetTabs(self):
        for tab in self.tabs:
            self.reset[tab] = True

    def toggleTabs(self, all=None):
        """
        Enables/Disables a tab if it is set as valid or not
        """
        # Tabs are always reset when this function is called
        self.resetTabs()

        for name, valid in self.valid.items():
            if all is not None:
                valid = all

            tab = self.pnls[name]
            btn = self.btns[name]
            if valid:
                btn.enable()
                tab.enable()
                tab.classes(remove="disabled")
            else:
                btn.disable()
                tab.disable()
                tab.classes(add="disabled")


GUI = Tabs()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run()

#%%
# wd = IsofitWD("/Users/jamesmo/projects/isofit/research/jemit/")
# wd = IsofitWD("/Users/jamesmo/Downloads/firefox/Test6")
# wd.output.files
#
# wd.output.find("rfl", exc="subs", all=True)
