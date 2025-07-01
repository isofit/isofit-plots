"""
Usage:
    1. pip install nicegui
    2. python isonice/isofit.py
    3. Acknowledge this is a WORK IN PROGRESS
"""
import json
import logging
import re
import socket
from pathlib import Path
from types import SimpleNamespace

import click
import plotly.express as px
import plotly.graph_objects as go
import xarray as xr

from nicegui import observables, run, ui

from isofit.radiative_transfer import luts

# TODO: This will source from isofit once the PR is accepted
try:
    from isofit.utils.wd import IsofitWD, Loaders
except:
    logging.exception("Failed to load IsofitWD from ISOFIT, using fallback")
    from isoplots.isonice.wd import IsofitWD, Loaders

# Global shared working directory
WD = IsofitWD(".")

dark = ui.dark_mode()
dark.enable()

ui.context.client.content.classes('h-screen')
ui.add_head_html('''
    <style type="text/css">
    .hide-header .ag-header {
        display: none;
    }
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
    # "Name": "/path/to/set"
}


def plotlyColor(i):
    """
    Retrieves a plotly color

    Parameters
    ----------
    i : int
        Index color, wraps if the index exceeds to length of the color list

    Returns
    -------
    str
        Hex color
    """
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

    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        self.active = None # Active row used for image plotting
        self.inputs = [] # Tracks input rows
        self.traces = [] # Tracks annotations
        self.spectras = [] # SpectraPlot objects

        self.files = observables.ObservableList([], on_change=self.setOptions)

        with ui.splitter(value=30).classes("w-full h-full") as splitter:
            with splitter.before:
                with ui.card().classes("w-full") as self.header:
                    with ui.button_group().classes("w-full").props("outline"):

                        ui.button("Reset", on_click=self.resetImage) \
                            .classes("flex-1") \
                            .props("outline") \
                            .tooltip("Removes all annotations and spectra plots")

                        ui.button("Add File", on_click=self.createFileRow) \
                            .classes("flex-1") \
                            .props("outline") \
                            .tooltip("This must be the same X/Y dimensions as the first file")

                        with (ui.dropdown_button("Settings")
                            .classes("flex-1")
                            .props("outline")
                        ):
                            with ui.row().classes("p-4"):
                                with ui.column():
                                    self.r = ui.number(label="Red Band", value=60, on_change=self.createImage, precision=0).props("dense")
                                    self.g = ui.number(label="Green Band", value=40, on_change=self.createImage, precision=0).props("dense")
                                    self.b = ui.number(label="Blue Band", value=30, on_change=self.createImage, precision=0).props("dense")
                                with ui.column():
                                    self.brighten = ui.switch("Brighten Image", value=True, on_change=self.createImage)
                                    self.annoDelClick = ui.switch("Delete via Click", value=False).tooltip("Clicking on annotation points on the image will remove the spectra plot. Alternatively, use the dropdown menu on the top-left corner of the plot")
                                    # self.shareX = ui.switch("Share X axis", value=False)
                                    # self.sharey = ui.switch("Share Y axis", value=False)

                    self.createFileRow(main=True)


                # Generic placeholder figure
                self.setImage(go.Figure())

                with ui.element().classes("relative w-full") as self.column:
                    # Loading overlay
                    with ui.card().classes("absolute inset-0 z-10 flex items-center justify-center bg-white/70") as self.loading:
                        ui.spinner(size='xl')
                    self.loading.visible = False

                    # Plotly figure
                    self.plot = ui.plotly(self.img).classes('w-full h-full')

                # Override the event to delete the source string which crashes the server when the image is too large
                self.plot.on('plotly_click', js_handler="""
                    (event) => {
                        event.points.forEach(point => delete point.data.source);
                        return emitEvent('clickedPoint', event);
                    };
                """)
                ui.on('clickedPoint', self.annotationEvent)
            with splitter.after:
                with ui.card().classes("h-full w-full p-0"):
                    self.scroll = ui.scroll_area().classes("h-full w-full")

    async def setOptions(self, *_):
        """
        Updates each file selection dropdown with the self.files list
        This is called each time the list is updated
        """
        for row in self.inputs:
            row["select"].set_options(self.files)

    def createFileRow(self, main=False):
        """
        Creates a new input row

        Parameters
        ----------
        main : bool, default=False
            The main row (self.inputs[0]) cannot be removed, so the delete button is
            replaced with an info tooltip
        """
        row = {}
        self.inputs.append(row)
        color = plotlyColor(len(self.inputs)-1)

        with self.header:
            with ui.row().classes("w-full"):
                row["colorBtn"] = ui.button(
                    icon = "show_chart",
                    on_click = lambda e: self.setActive(row)
                ).props("dense outline") \
                .classes(f"h-full") \
                .style(f"--q-primary: {color};") \
                .tooltip("Set this data as the image")

                row["select"] = ui.select(
                    options = self.files,
                    label = "Select data file",
                    on_change = lambda e: self.loadFile(e.value, row),
                    new_value_mode = "add-unique",
                ).classes("flex-1").props("dense")

                if main:
                    self.active = row
                    row["colorBtn"].icon = "image"

                    with (ui.button(icon="question_mark")
                        .classes("h-full")
                        .props("dense outline")
                        .style(f"--q-primary: {color};")
                    ):
                        with ui.tooltip():
                            ui.label("This file will be the image plotted below")
                            ui.label("Changes to the settings will use this data")
                            ui.label("Additional files must be the same X/Y/Wavelength shape to plot correctly")
                            ui.label("Some plotting features are only available if certain requirements are met:")
                            ui.label("  - Subtraction, % Difference : Only two data files are loaded")
                            ui.label("  - Average : Two or more data files are loaded")
                else:
                    row["removeBtn"] = ui.button(
                        icon="close",
                        on_click=lambda e: self.delInput(row)
                    ).classes("h-full") \
                    .props("dense outline") \
                    .style(f"--q-primary: {color};") \
                    .tooltip("Remove this data")

    async def delInput(self, row):
        """
        Removes an input row and its data from the spectra plots

        Parameters
        ----------
        row : dict
            Input row to remove
        """
        self.loading.visible = True

        i = self.inputs.index(row)
        self.header.remove(i+1)
        self.inputs.remove(row)

        # Update colors of buttons
        for j, row in enumerate(self.inputs[i:]):
            color = plotlyColor(i+j)
            row["colorBtn"].style(f"--q-primary: {color};")
            row["removeBtn"].style(f"--q-primary: {color};")

        # Update colors of spectra plots
        for spectra in self.spectras:
            await spectra.build()

        self.loading.visible = False

    async def reset(self, *_):
        """
        Resets the tab
        """
        self.scroll.clear()
        self.traces.clear()
        self.spectras.clear()

        self.files.clear()
        self.files += WD.find("rfl", all=True, exc=["hdr", "subs"])
        self.files.sort()

        self.inputs[0]["select"].set_value(self.files[0])

    async def resetImage(self):
        """
        Resets the image, deleting all annotations and spectra plots
        """
        self.scroll.clear()
        self.traces.clear()
        self.spectras.clear()

        await self.createImage()

    def load(self, path):
        """
        TODO

        Parameters
        ----------
        path : str
            Path to data file to load. If the path exists, loads directly; otherwise
            use IsofitWD to find and load
        """
        if Path(path).exists():
            try:
                return Loaders.envi(path)
            except:
                logging.exception("Failed to load envi")
        else:
            try:
                return WD.load(path=path)
            except:
                logging.exception("Failed to load via WD")

    async def loadFile(self, file, row):
        """
        Loads a data file

        Parameters
        ----------
        file : str
            File to load
        row : dict
            Input dict associated with this file
        """
        self.loading.visible = True

        row["file"] = file
        row["data"] = await run.io_bound(self.load, path=file)

        if row["data"] is None:
            print("No data available, returning")
            self.loading.visible = False
            return

        if row == self.inputs[0]:
            self.scroll.clear()
            self.traces.clear()
            self.spectras.clear()

            # Set the limits to the band number inputs
            min = int(row["data"].band.min())
            max = int(row["data"].band.max())
            for opt in {self.r, self.g, self.b}:
                opt.min = min
                opt.max = max

            await self.createImage()
        else:
            for spectra in self.spectras:
                await spectra.build()

            self.loading.visible = False

    async def setActive(self, row):
        """
        Sets the active row which is used for plotting the image

        Parameters
        ----------
        row : dict
            Input row to set as the active row
        """
        self.active = row

        # Update icons
        row["colorBtn"].icon = "image"
        for data in self.inputs:
            if data == row:
                data["colorBtn"].icon = "image"
            else:
                data["colorBtn"].icon = "show_chart"

        await self.createImage()

    async def createImage(self):
        """
        Creates the data for the image and passes it along to the frontend

        This image is always self.inputs[0], ie. the first input
        """
        self.loading.visible = True

        bands = [self.r.value, self.g.value, self.b.value]
        rgb = self.active["data"].sel(band=bands).transpose("y", "x", "band")

        if self.brighten.value:
            rgb /= rgb.max(["x", "y"])

        # Convert to pixel coords for easier pixel selection
        rgb["x"] = range(rgb.x.size)
        rgb["y"] = range(rgb.y.size)

        await self.plotImage(rgb)

        # Re-add any traces that may still exist
        for trace in self.traces:
            self.img.add_trace(trace)
        self.plot.update()

        self.loading.visible = False

    def setImage(self, figure):
        """
        Sets the frontend image's figure

        Parameters
        ----------
        figure : go.Figure

        Returns
        -------

        """
        self.img = figure
        figure.update_layout(
            margin = dict(l=0, r=20, t=0, b=0),
            paper_bgcolor = "rgba(0, 0, 0, 0)",
            showlegend    = False
        )
        if self.plot:
            self.plot.update_figure(figure)

    async def plotImage(self, image):
        """
        Creates image figure to pass to the frontend

        Parameters
        ----------
        image : xarray.Dataset
            Image to plot
        """
        try:
            img = px.imshow(image, template="plotly_dark")
        except Exception as e:
            print(f"Failed to plot spectra image, reason: {e}")
            img = go.Figure()

        self.setImage(img)

    async def addAnotation(self, x, y):
        """
        Adds an annotation point to the image and creates a spectra plot

        Parameters
        ----------
        x : int
            X coordinate
        y : int
            Y coordinate
        """
        i = len(self.img.data)

        trace = go.Scatter(
            x = [x],
            y = [y],
            mode = "markers+text",
            name = f"Spectra {i} @ ({x}, {y})",
            text = [str(i)],
            marker = {"symbol": "circle-open"},
            textposition = "top center",
        )
        self.traces.append(trace)
        self.img.add_trace(trace)
        await self.plotSpectra(i, x, y)

        self.plot.update()

    async def delAnnotation(self, i):
        """
        Deletes an annotation from the image as well as removes the spectra plot
        associated with that point

        Parameters
        ----------
        i : int
            Index of the annotation to remove
        """
        # Remove the annotation from the image
        data = list(self.img.data)
        data.pop(i)
        self.img.data = data

        # Update names and texts
        for trace in self.img.data[i:]:
            pos = int(trace.text[0])
            new = str(pos-1)
            trace.name = re.sub(r"(\d+) @", f"{new} @", trace.name)
            trace.text = [new]

        # Convert to 0-indexed
        i -= 1

        # Remove the corresponding spectra plot
        self.scroll.remove(i)
        self.spectras.pop(i)
        self.traces.pop(i)

        # Update the colors
        for spectra in self.spectras[i:]:
            spectra.updateID(spectra.id - 1)

        self.plot.update()

    async def annotationEvent(self, event):
        """
        Event handler when an image pixel is clicked. If the pixel has an annotation,
        it deletes it. If it doesn't, it adds an annotation.

        Parameters
        ----------
        event : nicegui.events.GenericEventArguments
            Event triggered when the image is clicked
        """
        print(type(event))
        # Images will only ever have 1 point returned
        point = event.args["points"][0]
        data = point["data"]

        # Clicked a pixel on the image
        if data["type"] == "image":
            y, x = point["pointIndex"]
            await self.addAnotation(x, y)

        # Clicked an annotation
        elif self.annoDelClick.value and data["type"] == "scatter":
            i = point["curveNumber"]
            await self.delAnnotation(i)

    async def plotSpectra(self, i, x, y):
        """
        Creates a spectra plot for a pixel

        Parameters
        ----------
        i : int
            Index ID to assign
        x : int
            X coordinate
        y : int
            Y coordinate
        """
        with self.scroll:
            spectra = SpectraPlot(i, x, y, self)
            await spectra.build()

            self.spectras.append(spectra)


class SpectraPlot:
    def __init__(self, id, x, y, parent):
        """
        Plots one or more spectra lines for a given pixel

        Parameters
        ----------
        id : int
            ID of the plot
        x : int
            X coordinate
        y : int
            Y coordinate
        parent : Spectra
            Parent object to refer to for things like close plot or data retrieval
        """
        self.id = id
        self.x = x
        self.y = y
        self.parent = parent

        self.cache = []

        with ui.card().classes("relative w-full p-2"):
            with ui.card().classes("absolute inset-0 z-20 flex items-center justify-center bg-white/70") as self.loading:
                ui.spinner(size='xl')
            self.loading.visible = False

            # Dropdown button in top-left corner
            with ui.button(icon="more_horiz", on_click=self.updateOptions).classes("absolute top-0 left-0 z-10").props("outline dense"):
                with ui.menu() as menu:
                    ui.menu_item("Close plot", on_click=self.close)
                    self.trim = ui.switch("Remove Minimums", value=True, on_change=self.build)
                    self.styles = ui.radio(
                        options=["Separate", "Average", "Subtract", "% Difference"],
                        value="Separate",
                        on_change=self.styleChanged
                    ).classes('flex flex-col p-1')#.props("disable")

            # Plotly chart
            blank = go.Figure(go.Scatter())
            self.plot = ui.plotly(blank).classes("w-full")

    def updateID(self, id=None):
        """
        Updates the plot title with the color assigned per the ID

        Parameters
        ----------
        id : int, default=None
            Optionally set the ID
        """
        if id is not None:
            self.id = id

        self.plot.figure.update_layout(
            title={
                "text": f"Spectra {self.id} @ ({self.x}, {self.y})",
                "font": {
                    "color": plotlyColor(self.id)
                }
            }
        )

        self.plot.update()

    async def updateOptions(self):
        """
        Enables/disables radio options depending on the number of input files available

        This is called every time the dropdown is opened so that it is always up to
        date
        """
        script = f'''
        const radioGroup = document.getElementById("c{self.styles.id}");
        const radios = radioGroup.querySelectorAll('[role="radio"]');
        '''
        for i, style in enumerate(self.styles.options):
            if self.isStyleValid(style):
                script += f'''
                radios[{i}].setAttribute('aria-disabled', 'false');
                radios[{i}].classList.remove('disabled');
                '''
            else:
                script += f'''
                radios[{i}].setAttribute('aria-disabled', 'true');
                radios[{i}].classList.add('disabled');
                '''

        ui.run_javascript(script)

    async def close(self):
        """
        Closes this plot
        """
        await self.parent.delAnnotation(self.id)

    async def build(self):
        """
        Retrieves the loaded data from the parent, selects this spectra's pixel, and
        prepares the data for plotting
        """
        self.cache.clear()

        for row in self.parent.inputs:
            if (data := row.get("data")) is not None:
                try:
                    spectra = data.isel(x=self.x, y=self.y)
                    spectra = spectra.rename(wavelength='Wavelength')

                    # Remove minimum values
                    if self.trim.value:
                        spectra = spectra.where(spectra != spectra.min())

                    spectra.name = "Reflectance"
                    df = spectra.to_dataframe()

                    # Only cache these columns (sometimes fwhm tags along)
                    df = df[["Wavelength", "Reflectance"]]

                    self.cache.append(df)
                except Exception as e:
                    print(f"Failed to create a spectra plot for {row['file']}, reason: {e}")

        await self.draw()

    def calcStyle(self):
        """
        Performs the calculations for the style options available

        Returns
        -------
        list
            The list of dataframes prepared for plotting
        """
        style = self.styles.value

        if style == "Separate":
            return self.cache

        calc = self.cache[0].copy()
        rfls = [df["Reflectance"] for df in self.cache]

        if style == "Subtract":
            calc["Reflectance"] = rfls[0] - rfls[1]

        elif style == "% Difference":
            a = rfls[0]
            b = rfls[1]

            calc["Reflectance"] = (a - b).abs() / ((a + b) / 2) * 100

        elif style == "Average":
            calc["Reflectance"] = sum(rfls) / len(rfls)

        return [calc]

    async def draw(self):
        """
        Plots the data with the set style
        """
        self.loading.visible = True

        data = self.calcStyle()

        fig = go.Figure()
        for i, df in enumerate(data):
            fig.add_trace(
                trace = px.line(df,
                    x = 'Wavelength',
                    y = 'Reflectance',
                ).data[0]
            )

        for i, trace in enumerate(fig.data):
            trace.line.color = plotlyColor(i)

        fig.update_layout(
            height = 300,
            margin = dict(l=0, r=0, t=30, b=0),
            template = "plotly_dark",
            paper_bgcolor = "rgba(0, 0, 0, 0)"
        )

        self.plot.update_figure(fig)

        self.updateID()

        self.loading.visible = False

    def isStyleValid(self, style):
        """
        Checks if a selected style is valid given the data available

        Parameters
        ----------
        style : str
            Style mode to check validity
        """
        if style != "Separate":
            count = len(self.cache)
            if count < 2:
                return False
            if style in {"Subtract", "% Difference"} and count != 2:
                return False

        return True

    async def styleChanged(self, style):
        """
        Intercepts the radio style change to check if the style is a valid option
        If not, discards the change

        Parameters
        ----------
        style : nicegui.events.ValueChangeEventArguments
            Event triggered by the `styles` ui.radio
        """
        if not self.isStyleValid(style.value):
            return self.styles.set_value("Separate")
        await self.draw()


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
        configs = WD.find("config/.json", all=True)
        self.select.set_options(configs, value=configs[0])
        # if isofit:
        #     self.isofit = isofit
        #     configs = isofit.find("config/.json", all=True)
        #     self.select.set_options(configs, value=configs[0])

    def loadConfig(self, event):
        # data = self.isofit.load(path=event.value)
        data = WD.load(path=event.value)
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
            "select": None,
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

    async def load(self, file):
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
        if (lut := await self.load(file)) is None:
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

        if (lut := await self.load(file)) is None:
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
        except Exception as e:
            print(f"Failed to plot {quant}[{dim}], reason: {e}")
            return self.blank
        finally:
            self.loading.visible = False

    async def updateUI(self):
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
        self.files += WD.find("lut/.nc", all=True)
        self.files.sort()


def toNiceGUITree(tree, *, path=None, nodes=None):
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
        toNiceGUITree(tree, path=".", nodes=nodes[-1]["children"])
    else:
        for file in tree:
            if isinstance(file, dict):
                for subdir, files in file.items():
                    nodes.append({
                        "id"      : f"{path}/{subdir.name}",
                        "label"   : subdir.name,
                        "desc"    : subdir.info,
                        "children": []
                    })
                    toNiceGUITree(files,
                        path  = nodes[-1]["id"],
                        nodes = nodes[-1]["children"]
                    )
            else:
                nodes.append({
                    "id"   : f"{path}/{file.name}",
                    "label": file.name,
                    "desc" : file.info
                })
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
            setWD = lambda e: self.search.set_value(WORKING_DIRS[e.sender.text])
            with ui.row():
                for name, path in WORKING_DIRS.items():
                    if not Path(path).exists():
                        print(f"Path not found: {path}")
                        continue
                    ui.button(name, on_click=setWD)

        with ui.row().classes("w-full items-center"):
            with ui.button("Set as Working Directory",
                on_click = self.setWD
            ).classes("w-[15%]"):
                with ui.tooltip():
                    ui.label("Set this path as the active working directory")
                    ui.label("This will recursively search for ISOFIT products")
                    ui.label("Only do this on known directories as this is an expensive operation")
                    ui.label("Executing this on protected or excessively deep directories may crash this program's server")

            self.search = ui.input("Search",
                on_change = self.glob
            ).classes("w-[83%]")

        self.preview = ui.column().classes("w-full")

        self.filter = ui.input("filter").classes("w-full")
        self.filter.visible = False
        self.directoryTree = ui.scroll_area().classes("w-full h-full")

    async def glob(self, path):
        """
        Globs the filesystem at the current search path, placing directories before
        files

        Parameters
        ----------
        path : ValueChangeEventArguments
            Event when the search string changes
        """
        self.preview.clear()
        with self.preview:
            ui.spinner('dots', size='xl')

        path = Path(path.value)
        if not path.exists():
            glob = path.parent.glob(f"{path.name}*")
        else:
            glob = path.glob("*")

        dirs = []
        files = []
        for file in glob:
            if file.is_dir():
                dirs.append(file.name)
            else:
                files.append(file.name)

        data = [
            {"path": ".."}
        ] + [
            {"path": f"{d}/"}
            for d in sorted(dirs)
        ] + [
            {"path": f}
            for f in sorted(files)
        ]

        self.preview.clear()
        with self.preview:
            if data:
                ui.aggrid({
                    "columnDefs": [
                        {"field": "path"}
                    ],
                    "rowData": data
                }, theme="balham-dark") \
                .classes("hide-header") \
                .on('cellClicked',
                    lambda event: self.appendSearch(event.args["value"])
                )
            else:
                ui.icon("report_problem").tooltip("An error has occurred")

    def appendSearch(self, path):
        """
        Appends a string to the current search string

        Parameters
        ----------
        path : str
            Path to append
        """
        current = Path(self.search.value)
        if not current.exists():
            current = current.parent
        new = (current / path).resolve()

        self.search.set_value(str(new))

    async def reset(self, isofit=None):
        ...

    async def setWD(self):
        """
        Sets the global IsofitWD object
        """
        self.directoryTree.clear()
        with self.directoryTree:
            ui.spinner('dots', size='xl')

        WD.reset(self.search.value, recursive=True)
        self.parent.isofit = WD

        self.parent.toggleTabs(all=True)

        # Recursively get the tree structure of the directory
        data = WD.getTree(info=True)
        data = toNiceGUITree(data)
        data[0]["label"] = str(WD.path)

        # Set the output directory tree
        self.directoryTree.clear()
        with self.directoryTree:
            if data:
                # ui.label("Click on an output file below to jump to an interactive component for that file [Work in Progress]")
                # ui.label("Detected paths:")

                self.tree = EnhancedTree(data, on_select=lambda e: self.navToFile(e)) \
                .classes("border h-full w-full") \
                .props("no-transition dense")

                self.tree.expand(["root"])
                self.tree.add_slot('default-header', '''
                    <span :props="props">{{ props.node.label }}</strong></span>
                ''')
                self.tree.add_slot('default-body', '''
                    <span :props="props">{{ props.node.desc }}</span>
                ''')

                self.filter.visible = True
                self.filter.bind_value_to(self.tree, "filter")
            else:
                ui.icon("report_problem").tooltip("An error has occurred")

    def navToFile(self, event):
        """
        TODO

        Parameters
        ----------
        event
        """
        name = event.value

        # Find the source node clicked
        if node := self.tree.findNode(name):
            if "children" in node:
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

        # for name, valid in self.valid.items():
        #     if all is not None:
        #         valid = all
        #
        #     tab = self.pnls[name]
        #     btn = self.btns[name]
        #     if valid:
        #         btn.enable()
        #         tab.enable()
        #         tab.classes(remove="disabled")
        #     else:
        #         btn.disable()
        #         tab.disable()
        #         tab.classes(add="disabled")


GUI = Tabs()


def portAvail(port: int) -> bool:
    """
    checks if a port is available

    Parameters
    ----------
    port : int
        Port to check

    Returns
    -------
    bool
        True if available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0


def checkPorts(start : int, end : int = 100) -> None:
    """
    Checks for an open port between the start and end range

    Parameters
    ----------
    start : int
        Starting port
    end : int
        Offset end from the starting point to check in range of
    """
    if not portAvail(start):
        for port in range(start+1, start+end):
            print(f"Checking {port}")
            if portAvail(port):
                print(f"Port {start} is already in use, recommend using --port {port}")
                break
        else:
            print(f"All ports between {start}-{start+end} are in use")


def launch(path=".", check=False, **kwargs):
    """
    Launches the NiceGUI server

    Parameters
    ----------
    path : str, default=None
        Optional path to initialize with
    check : bool, default=False
        Check for an open port, may delay startup
    **kwargs : dict
        Additional key-word arguments passed directly to ui.run
    """
    if check:
        print("Checking ports")
        checkPorts(kwargs.get("port", 8080))

    if path:
        print(f"Setting path: {path}")
        GUI.tabs["setup"].search.set_value(path)

    print("Launching")
    ui.run(**kwargs)


@click.command()
@click.option("-p", "--path", default=".", help="Working directory to initially load with")
@click.option("-c", "--check", default=False, is_flag=True, help="Checks for an open port up to 100 after the given port. May cause a delay in startup")
@click.option("--port", type=int, default=8080, help="Port to use. Defaults to 8080")
@click.option("-r", "--reload", default=False, is_flag=True, help="Enable hot-reloading -- only available if executing the browser.py script directly")
def cli(**kwargs):
    """
    Launches the NiceGUI browser server
    """
    launch(**kwargs)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    cli()

# When executing directly via Python, NiceGUI spawns the page in a separate process
# Click doesn't work in this, so launch directly -- inherits from the first call
elif __name__ == "__mp_main__":
    logging.basicConfig(level="DEBUG")
    launch()
