import logging
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import xarray as xr
from nicegui import (
    observables,
    run,
    ui
)

from isoplots.isonice import (
    WD,
    Loaders
)
from isoplots.isonice.utils import plots
from isoplots.isonice.utils.enhancedinput import EnhancedInput


Logger = logging.getLogger(__name__)

Name = "Spectra"
Icon = "show_chart"
Prio = 2


class Spectra:
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
            self.plot = ui.plotly(plots.blank()).classes("w-full")

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
                    "color": plots.plotlyColor(self.id)
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
                except:
                    Logger.exception(f"Failed to create a spectra plot for {row['file']}")

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
            trace.line.color = plots.plotlyColor(i)

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


class Tab:
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
        self.spectras = [] # Spectra objects

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

                with ui.element().classes("relative w-full") as self.column:
                    # Loading overlay
                    with ui.card().classes("absolute inset-0 z-10 flex items-center justify-center bg-white/70") as self.loading:
                        ui.spinner(size='xl')
                    self.loading.visible = False

                    # Plotly figure
                    self.plot = ui.plotly(go.Figure()).classes('w-full h-full')

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
        color = plots.plotlyColor(len(self.inputs)-1)

        with self.header:
            with ui.row().classes("w-full"):
                row["colorBtn"] = ui.button(
                    icon = "show_chart",
                    on_click = lambda e: self.setActive(row)
                ).props("dense outline") \
                .classes(f"h-full") \
                .style(f"--q-primary: {color};") \
                .tooltip("Set this data as the image")

                row["select"] = EnhancedInput(
                    label = "Select data file",
                    options = self.files,
                    default = "Options",
                    on_change = lambda path: self.loadFile(path, row),
                ).classes("flex-1")

                if main:
                    self.active = row
                    row["colorBtn"].icon = "image"

                    with (ui.button(icon="question_mark")
                        .classes("h-full")
                        .props("dense outline")
                        .style(f"--q-primary: {color};")
                    ):
                        with ui.tooltip():
                            ui.label("Click on the button to the left of each file input to select that data to be the image plot")
                            ui.label("Changes to the settings will use this data")
                            ui.label("Additional files must be the same X/Y/Wavelength shape to plot correctly. There are no enforcement of this, however")
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
            color = plots.plotlyColor(i+j)
            row["colorBtn"].style(f"--q-primary: {color};")
            row["removeBtn"].style(f"--q-primary: {color};")

        # Update colors of spectra plots
        for spectra in self.spectras:
            await spectra.build()

        await self.setActive(self.inputs[0])

        self.loading.visible = False

    async def reset(self):
        """
        Resets the tab
        """
        self.scroll.clear()
        self.traces.clear()
        self.spectras.clear()

        self.files.clear()
        self.files += await run.io_bound(WD.find, "rfl", all=True, exc=["hdr", "subs"])
        self.files.sort()

        if self.files:
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
        Logger.debug(f"Loading {path}")
        if Path(path).exists():
            try:
                return Loaders.envi(path)
            except:
                Logger.exception("Failed to load envi")
        else:
            try:
                return WD.load(path=path)
            except:
                Logger.exception("Failed to load via WD")

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
        # No change, no action
        if file == row.get("file"):
            return

        self.loading.visible = True

        data = await run.io_bound(self.load, path=file)

        if data is None:
            Logger.error("No data available, returning")

            # Reset to the last value if set
            if file := row.get("file"):
                row["select"].set_value(file)

            row["select"].set_error(f"Failed to load file, check logs: {file}")

            self.loading.visible = False
            return

        row["file"] = file
        row["data"] = data

        if row == self.active:
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

    def buildImage(self):
        """
        """
        fig = go.Figure()

        if self.active:
            try:
                bands = [self.r.value, self.g.value, self.b.value]
                rgb = self.active["data"].sel(band=bands).transpose("y", "x", "band")

                lower, upper = 2, 98
                if self.brighten.value:
                    lower, upper = 10, 90

                # Stretch and clip
                vmin = np.nanpercentile(rgb, lower, axis=(1, 0))
                vmax = np.nanpercentile(rgb, upper, axis=(1, 0))
                rgb = (rgb - vmin) / (vmax - vmin)
                rgb = rgb.clip(0, 1)

                # Convert to pixel coords for easier pixel selection
                rgb["x"] = range(rgb.x.size)
                rgb["y"] = range(rgb.y.size)

                fig = px.imshow(rgb, template="plotly_dark")
            except:
                Logger.exception(f"Failed to plot spectra image")

        for trace in self.traces:
            fig.add_trace(trace)

        fig.update_layout(
            margin = dict(l=0, r=20, t=0, b=0),
            showlegend = False,
            paper_bgcolor = "rgba(0, 0, 0, 0)",
        )

        return fig

    async def createImage(self):
        """
        Creates the data for the image and passes it along to the frontend

        This image is always self.inputs[0], ie. the first input
        """
        self.loading.visible = True

        self.img = await run.io_bound(self.buildImage)
        self.plot.update_figure(self.img)

        self.loading.visible = False

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
            spectra = Spectra(i, x, y, self)
            await spectra.build()

            self.spectras.append(spectra)
