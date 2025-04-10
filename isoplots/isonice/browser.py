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

from nicegui import run, ui

from isofit.radiative_transfer import luts

# TODO: This will source from isofit once the PR is accepted
try:
    from isofit.utils.wd import IsofitWD
except:
    from isoplots.isonice.wd import IsofitWD

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
    "NEON": "/Users/jamesmo/projects/isofit/research/NEON.bak/output/NIS01_20210403_173647/",
    "emit": "/Users/jamesmo/projects/isofit/research/jemit/",
    "Pasadena": "/Users/jamesmo/projects/isofit/extras/examples/20171108_Pasadena"
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
            opts = [f"{self.isofit.output.name}_rfl"]

            if opts != self.opts:
                self.opts = opts

                # Always default to the full RFL data
                self.select.set_options(opts, value=opts[0])
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

def blankFig(fkw={}, lkw={}):
    lkw = {
        "margin": dict(l=0, r=20, t=0, b=0),
        "paper_bgcolor": "rgba(0, 0, 0, 0)",
        "showlegend": False,
        "template": "plotly_dark",
    } | lkw

    fig = go.Figure(**fkw)
    fig.update_layout(**lkw)

    return fig

#%%

def multiplot(figs=[], height=300):
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
        print(type(plot))
        for trace in plot.data:
            fig.add_trace(trace, row=i+1, col=1)

    return fig

#%%

class MultiPlotLUT:
    """
    Handles the construction and management of a single LUT plotting card in the LUTs
    tab
    """
    isofit = None

    def b__init__(self, files=None, cache=None):
        """
        Parameters
        ----------
        files : list, default=None
            Shared NiceGUI observables for the files options, otherwise will be an
            independent list
        cache : dict, default=None
            Shared cache dict if provided, otherwise creates one for this object
        """
        if files is None:
            files = observables.ObservableList([], on_change=self.setOptions)
        self.files = files

        if cache is None:
            cache = {}
        self.cache = cache

        self.selects = []
        self.plots = [self.blank]
        self.luts = [None]

        with ui.card().classes("w-full border"):
            with ui.column().classes("w-full") as self.column:
                with ui.row().classes("w-full"):
                    select = ui.select(
                        label = "LUT File",
                        options = self.files,
                        multiple = False, # TODO?
                        new_value_mode = "add-unique",
                        on_change = lambda e: self.changeFile(e.value)
                    ).classes("w-1/4").props('use-chips')
                    self.selects.append(select)

                    self.quants = ui.select(
                        label = "Select a LUT quantity",
                        options = [],
                        on_change = lambda e: self.changeQuant(e.value)
                    ).classes("w-1/4")
                    self.quants.disable()

                    self.dims = ui.select(
                        label = "Select a LUT dimension",
                        options = [],
                        on_change = lambda e: self.changeDim(e.value)
                    ).classes("w-1/4")
                    self.dims.disable()

                    ui.button("Add Subplot",
                        on_click = lambda: self.createSubplot()
                    ).props("outline")

                self.ui = ui.plotly(multiplot()).classes("w-full")

    def __init__(self, files=None, cache=None):
        """
        Parameters
        ----------
        files : list, default=None
            Shared NiceGUI observables for the files options, otherwise will be an
            independent list
        cache : dict, default=None
            Shared cache dict if provided, otherwise creates one for this object
        """
        if files is None:
            files = observables.ObservableList([], on_change=self.setOptions)
        self.files = files

        if cache is None:
            cache = {}
        self.cache = cache

        self.main = self.new
        self.plots = [self.main]

        with ui.card().classes("w-full border"):
            with ui.column().classes("w-full") as self.column:
                with ui.row().classes("w-full"):
                    self.main["select"] = ui.select(
                        label = "LUT File",
                        options = self.files,
                        multiple = False, # TODO?
                        new_value_mode = "add-unique",
                        on_change = lambda e: self.changeFile(e.value)
                    ).classes("w-1/4").props('use-chips')
                    # self.selects.append(select)

                    self.quants = ui.select(
                        label = "Select a LUT quantity",
                        options = [],
                        on_change = lambda e: self.changeQuant(e.value)
                    ).classes("w-1/4")
                    self.quants.disable()

                    self.dims = ui.select(
                        label = "Select a LUT dimension",
                        options = [],
                        on_change = lambda e: self.changeDim(e.value)
                    ).classes("w-1/4")
                    self.dims.disable()

                    ui.button("Add Subplot",
                        on_click = lambda: self.createSubplot()
                    ).props("outline")

                self.ui = ui.plotly(multiplot()).classes("w-full")

    def _setOptions(self, event=None):
        print("local setOptions")
        for select in self.selects:
            select.set_options(self.files)

    def setOptions(self, event=None):
        print("local setOptions")
        for plot in self.plots:
            plot["select"].set_options(self.files)

    @property
    def new(self):
        return {
            "plot": self.blank,
            "lut": None,
            "select": None
        }

    def _createSubplot(self):
        i = len(self.plots)
        self.plots.append(self.blank)
        self.luts.append(None)

        with self.column:
            with ui.row().classes("w-full"):
                select = ui.select(
                    label = f"LUT File for Plot {i+1}",
                    options = self.files,
                    new_value_mode = "add-unique",
                    on_change = lambda e: self.updateSubplot(i, file=e.value)
                ).classes("w-4/5")
                self.selects.append(select)

                ui.button("Remove",
                    on_click = lambda: self.deleteSubplot(i)
                ).props("outline")

        # Shift to bottom of the card
        self.ui.move(target_index=-1)

        self.updateUI()

    def createSubplot(self):
        plot = self.new
        self.plots.append(plot)

        with self.column:
            with ui.row().classes("w-full"):
                plot["select"] = ui.select(
                    label = f"LUT File for Plot {len(self.plots)}",
                    options = self.files,
                    new_value_mode = "add-unique",
                    on_change = lambda e: self.updateSubplot(plot, file=e.value)
                ).classes("w-4/5")

                ui.button("Remove",
                    on_click = lambda: self.deleteSubplot(plot)
                ).props("outline")

        # Shift to bottom of the card
        self.ui.move(target_index=-1)

        # Update the figure with a blank
        self.updateUI()

    def deleteSubplot(self, plot):
        i = self.plots.index(plot)
        self.column.remove(i)
        self.plots.pop(i)
        self.updateUI()

        # Update labels for consistency
        for i, plot in enumerate(self.plots[1:]):
            plot["select"].props(f'label="LUT File for Plot {i+2}"')

    def updateSubplot(self, plot, file):
        if (lut := self.load(file)) is None:
            return

        plot["lut"] = lut
        plot["plot"] = self.plot(
            lut   = plot["lut"],
            quant = self.quant,
            dim   = self.dim
        )
        self.updateUI()

    def _updateSubplot(self, i, file):
        if (lut := self.load(file)) is None:
            return

        self.luts[i] = lut
        self.plots[i] = self.plot(
            lut   = self.luts[i],
            quant = self.quant,
            dim   = self.dim
        )
        self.updateUI()

    def load(self, file):
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
                    self.cache[file] = self.isofit.load(path=file).unstack()
                except Exception as e:
                    print(f"Failed to load, reason: {e}")

        return self.cache.get(file)

    def update(self, isofit=None):
        if isofit:
            self.isofit = isofit

    def _updateUI(self):
        """
        Updates the GUI with a newly constructed multi-plot figure
        """
        fig = multiplot(self.plots)
        self.ui.update_figure(fig)

    def updateUI(self):
        """
        Updates the GUI with a newly constructed multi-plot figure
        """
        plots = [plot["plot"] for plot in self.plots]
        fig = multiplot(plots)
        self.ui.update_figure(fig)

    def changeFile(self, file):
        if (lut := self.load(file)) is None:
            return

        self.main["lut"] = lut
        # self.luts[0] = lut

        plottable = set(lut) - set(lut.drop_dims("wl"))
        if plottable:
            self.quants.set_options(list(plottable))
            self.quants.enable()

        self.quants.set_value(None)

    def changeQuant(self, quant=None):
        print("changeQuantities", quant)
        self.quant = quant

        # lut = self.luts[0]
        lut = self.main["lut"]
        dims = set(lut[quant].dims) - {"wl",}

        self.dims.set_options(list(dims))
        if dims:
            self.dims.enable()
        else:
            self.dims.disable()
            self.changeDim()

    def changeDim(self, dim=None):
        print("changeDimensions", dim)
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
            print(lut)
            return self.blank

    @property
    @staticmethod
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

from nicegui import observables

class LUTs:
    blank = property(lambda self: go.Figure(go.Scatter()))

    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        self.cards = []
        self.data = {}
        self.luts = {}
        self.cache = {}

        self.dropdowns = []
        self.files = []
        self.files = observables.ObservableList([], on_change=self.setOptions)
        with ui.scroll_area().classes("h-full w-full") as self.scroll:
            self.addCardBtn = ui.button("Add New Independent Plot", on_click=self.createCard).classes("w-full").props("outline")

        self.createCard()

    def setOptions(self, event):
        print("global setOptions")
        # for card in self.cards:
        #     card["fileOpts"].set_options(self.files)
        for card in self.cards:
            card.setOptions()

    async def reset(self, isofit=None):
        """
        Resets the tab with a new IsofitWD object

        Parameters
        ----------
        isofit : IsofitWD, default=None
            Working Isofit Directory object
        """
        self.files.clear()
        if isofit is not None:
            self.isofit = isofit

            self.luts = {name: obj for name, obj in isofit.dirs.items() if isinstance(obj, isofit.classes["lut"])}
            for name, lut in self.luts.items():
                self.files += [
                    f"{name}/{file}"
                    for file in lut.find("lut", all=True)
                ]
            for card in self.cards:
                card.isofit = isofit
            #     card["fileOpts"].set_options(self.files)

    def load(self, file):
        if file not in self.luts:
            if Path(file).exists():
                print(f"Loading given LUT: {file}")
                try:
                    self.luts[file] = luts.load(file).unstack()
                except Exception as e:
                    print(f"Failed to load, reason: {e}")
            else:
                print(f"Loading LUT from WD: {file}")
                try:
                    self.luts[file] = self.isofit.load(path=file).unstack()
                except Exception as e:
                    print(f"Failed to load, reason: {e}")

        return self.luts.get(file)

    def changeFile(self, value, card):
        # new = set([value]) # TODO: When changing back to multiple=True, remove []
        print("changeFile", value)
        if (lut := self.load(value)) is None:
            return

        card["lut"] = lut

        plottable = set(lut) - set(lut.drop_dims("wl"))
        if plottable:
            card["quantOpts"].set_options(list(plottable))
            card['quantOpts'].enable()

        card["quantOpts"].set_value(None)

        # card["data"] = {}
        # sel = card.setdefault("selected", set())

        # add = new - sel
        # for file in add:
        #     self.load(file)

        # remove = sel - new
        # TODO

        # for file in new:
        #     if file in self.data:
        #         lut = self.data[file]
        #
        #         card.setdefault("luts", {})[file] = lut
        #
        #         plottable = set(lut) - set(lut.drop_dims("wl"))
        #         card["quantOpts"].set_options(list(plottable))
        #         # card["quantOpts"].visible = True
        #         card['quantOpts'].enable()
        # card.setdefault("luts", {})[file] = lut

    def changeQuantities(self, value, card):
        print("changeQuantities", value)
        card["quant"] = value

        # dims = []
        # for file, lut in card["luts"].items():
        #     if value in lut:
        #         dims = set(lut[value].dims) - {"wl",}
        dims = set(card["lut"][value].dims) - {"wl",}

        card["dimOpts"].set_options(list(dims))
        if dims:
            # card["dimOpts"].visible = True
            card['dimOpts'].enable()
        else:
            card['dimOpts'].disable()
            self.changeDimensions(None, card)

    def changeDimensions(self, value, card):
        print("changeDimensions", value)
        card["dim"] = value

        card["plots"][0] = self.plot(
            lut = card["lut"],
            quant = card["quant"],
            dim = card["dim"]
        )

        # if card["quant"]:
        #     card["plots"][0] = self.plot(
        #         lut = card["lut"],
        #         quant = card["quant"],
        #         dim = card["dim"]
        #     )
        # else:
        #     card["plots"][0] = self.blank

        self.updatePlot(card)

        # Update subplots as well
        # for

    def plot(self, lut, quant, dim):
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
            print(lut)
            return self.blank

    def updateCardPlot(self, card, i, file=None):
        if file:
            if (lut := self.load(file)) is None:
                return

            card["plots"][i] = self.plot(
                lut = lut,
                quant = card["quant"],
                dim = card["dim"]
            )
            self.updatePlot(card)

    def updatePlot(self, card):
        fig = multiplot(card["plots"])
        card["plot"].update_figure(fig)

    def createCardPlot(self, card):
        plots = card.setdefault("plots", [])

        i = len(plots)
        plots.append(self.blank)
        card["plot"].update_figure(multiplot(plots))

        with card["column"]:
            # self.addCardBtn.move(target_index=-1)
            ui.select(
                label = f"LUT File for Plot {i+1}",
                options = self.files,
                new_value_mode = "add-unique",
                on_change = lambda e: self.updateCardPlot(card, i, file=e.value)
            ).classes("w-full")

        # Shift to bottom of the card
        card["plot"].move(target_index=-1)

            # with ui.row().classes("w-full"):
            #     ui.select(
            #         label = "LUT File",
            #         options = self.files,
            #         multiple = False, # TODO
            #         new_value_mode = "add-unique",
            #         on_change = lambda e: self.updateCardPlot(card, i, file=e.value)
            #     ).classes("w-full")

            # fig = blankFig(height=350)
            # plot = ui.plotly(fig).classes('w-full')
            # plots.append(plot)

            # multi = make_subplots(rows=2, cols=1, shared_xaxes=True, shared_yaxes=True)
            # for trace in fig.data:
            #     multi.add_trace(trace, row=1, col=1)
            # for trace in fig.data:
            #     multi.add_trace(trace, row=2, col=1)
            # multi

    def _createCard(self):
        self.cards.append({})
        card = self.cards[-1]

        with self.scroll:
            with ui.card().classes("w-full border"):
                with ui.column().classes("w-full") as card["column"]:
                    with ui.row().classes("w-full"):
                        card['fileOpts'] = ui.select(
                            label = "LUT File",
                            options = self.files,
                            multiple = False, # TODO
                            new_value_mode = "add-unique",
                            on_change = lambda e: self.changeFile(e.value, card)
                        ).classes("w-1/4").props('use-chips')

                        card['quantOpts'] = ui.select(
                            label = "Select a LUT quantity",
                            options = [],
                            on_change = lambda e: self.changeQuantities(e.value, card)
                        ).classes("w-1/4")
                        # card['quantOpts'].visible = False
                        card['quantOpts'].disable()

                        card['dimOpts'] = ui.select(
                            label = "Select a LUT dimension",
                            options = [],
                            on_change = lambda e: self.changeDimensions(e.value, card)
                        ).classes("w-1/4")
                        # card['dimOpts'].visible = False
                        card['dimOpts'].disable()

                        # ui.button(icon="restart_alt").props('outline round').classes('shadow-lg')
                        # ui.button(icon="close").props('outline round').classes('shadow-lg')
                        ui.button("Add Subplot",
                            on_click = lambda: self.createCardPlot(card)
                        ).props("outline")

                    # fig = blankFig(lkw={"height": 350})
                    fig = multiplot()
                    card["plot"] = ui.plotly(fig).classes("w-full")
                    card["plots"] = [self.blank]
                    # card["plot"].on("plotly_relayout", lambda e: self.relayout(card, e))

        self.addCardBtn.move(target_index=-1)

    def createCard(self):
        # self.cards.append({})
        # card = self.cards[-1]

        with self.scroll:
            card = MultiPlotLUT(files=self.files, cache=self.cache)
            self.cards.append(card)

        self.addCardBtn.move(target_index=-1)

    def relayout(self, card, event):
        plots = card.get("plots", [])
        # for i in range(len(plots)):
        #     self.updateCardPlot(card, i)
        plot = card["plot"]
        fig = plot.figure
        # print(fig.layout.xaxis.range)
        # print(fig.layout.yaxis.range)


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
    def branches(self):
        """
        Returns branch nodes, no leaves

        Yields
        ------
        branch : dict
            A branch node
        """
        for branch in self.props["nodes"]:
            if "children" in branch:
                yield branch

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
            for branch in self.branches:
                if path := self.getPath(id, branch=branch):
                    return path

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
            for branch in self.branches:
                if node := self.findNode(id, branch=branch):
                    return node

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
            for branch in self.branches:
                if siblings := self.findSiblings(id, branch=branch):
                    return siblings

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

        isofit = IsofitWD(value)
        self.parent.isofit = isofit
        # if not self.isofit.dirs:
        #     return "Could not parse as a valid ISOFIT output directory"

        self.parent.toggleTabs(all=True)

        # Set the output directory tree
        with self.directoryTree:
            data = isofit.getTree(info=True)
            data = toNiceGUITree(data)

            ui.label("Click on an output file below to jump to an interactive component for that file [Work in Progress]")
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
        node = self.tree.findNode(name)

        if "children" in node:
            # siblings = findSiblings(root)
            siblings = self.tree.findSiblings(name)

            self.tree.collapse(siblings)
            self.tree.expand([name])
        else:
            # Get the string path to the node
            path = self.tree.getPath(name)

            print(path)


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
