import logging
import os
import re
from copy    import deepcopy
from pathlib import Path
from types   import SimpleNamespace

import numpy  as np
import xarray as xr
from textual_plotext import PlotextPlot

from textual.app        import App
from textual.containers import Container
from textual.message    import Message
from textual.reactive   import reactive
from textual.widgets    import (
    Footer,
    Header,
    TabbedContent,
    TabPane,
    Input,
    RichLog,
    DataTable,
    SelectionList,
    Collapsible
)


# LOG = "run.log"
LOG = None

# RFL = "output/emit20220820t131606_rfl"
RFL = None


class IsofitLogs(RichLog):
    file = reactive("")
    selected = reactive([])

    levelPad = 0
    colours  = {
        "DEBUG"    : "bright_black",
        "INFO"     : "blue",
        "WARNING"  : "yellow",
        "ERROR"    : "red",
        "EXCEPTION": "magenta"
    }

    class Stats(Message):
        """
        Reports extracted stats
        """
        name  = None
        total = None
        data  = None

    class Levels(Message):
        """
        Reports the levels available in the log file
        """
        def __init__(self, levels):
            self.levels = sorted(levels, key=lambda lvl: getattr(logging, lvl))
            super().__init__()

    def __init__(self, file, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file = file

    def watch_file(self, old, new):
        """
        Reacts when `file` is changed
        """
        if os.path.exists(new):
            self.file = new

            with open(new) as file:
                self.parse_v1(file.readlines())

    def watch_selected(self, old, new):
        """
        """
        self.clear()
        self.write(f"[bold]Showing logs from: {self.file}\n")

        content = self.filter(self.parsed)
        content = self.reconstruct(content)
        for line in content:
            self.write(line)

    def parse_v1(self, lines):
        lvls = set()
        content = []
        for line in lines:
            if (find := re.findall(r"(\w+):(\S+) \|\| (\S+) \| (.*)", line)):
                [find] = find
                level = find[0]
                lvls.add(level)

                source = find[2]
                content.append({
                    "timestamp": find[1],
                    "level"    : level,
                    "message"  : find[3]
                })
            elif (find := re.findall(r"(\w+):(\S+) \|\|\|? (.*)", line)):
                [find] = find
                level = find[0]
                lvls.add(level)

                content.append({
                    "timestamp": find[1],
                    "level"    : level,
                    "message"  : find[2]
                })
            else:
                content[-1]["message"] += f"\n{line.strip()}"

        self.levelPad = len(max(lvls))
        self.parsed = content
        self.extract_v1(content)
        self.post_message(self.Levels(lvls))
        self.selected = lvls

        return content

    def parse_v2(self, lines):
        """
        Parses an ISOFIT log file into a dictionary
        """
        lvls = set()
        content = []

        for line in lines:
            split = line.split("|")
            if len(split) == 4:
                level = split[1].strip()

                lvls.add(level)
                self.levelPad = max(self.levelPad, len(level))

                source = split[2].strip().split(':')

                content.append({
                    'timestamp': split[0].strip(),
                    'level'    : level,
                    'message'  : split[3].strip(),
                    'source'   : {
                        'file' : source[0],
                        'func' : source[1],
                        'line' : source[2]
                    }
                })
            else:
                content[-1]['message'] += '\n' + split[0].strip()

        self.parsed = content
        self.extract_v2(content)
        self.post_message(self.Levels(lvls))
        self.selected = lvls

        return content

    def extract_v1(self, content):
        """
        Extracts useful information from the processed logs
        """
        stats = self.Stats()

        for i, line in enumerate(content):
            message = line["message"]

            if message == "Run ISOFIT initial guess":
                stats.name = "Presolve"

            if message == "Running ISOFIT with full LUT":
                stats.name = "Full Solution"

            if message == "Analytical line inference":
                stats.name = "Analytical Line"

            if (find := re.findall(r"Beginning (\d+) inversions", message)):
                stats.total = find[0]

            if message == "Inversions completed":
                line = content[i+1]["message"]
                find = re.findall(r"(\S+) (\S+)", line.replace(',', ''))

                stats.data = {val: key for key, val in find}

                self.post_message(stats)

                # Reset the stats object
                stats = self.Stats()

            if "Analytical line inversions complete" in message or "Inversions complete" in message:
                find = re.findall(r"(\d+\.\d+s?) (\S+)", message.replace(',', ''))

                stats.data = {val: key for key, val in find}

                self.post_message(stats)

                # Reset the stats object
                stats = self.Stats()

    def extract_v2(self, content):
        """
        Extracts useful information from the processed logs
        """
        stats = self.Stats()

        for i, line in enumerate(content):
            message = line["message"]

            if message == "Run ISOFIT initial guess":
                stats.name = "Presolve"

            if message == "Running ISOFIT with full LUT":
                stats.name = "Full Solution"

            if message == "Analytical line inference":
                stats.name = "Analytical Line"

            if (find := re.findall(r"Beginning (\d+) inversions", message)):
                stats.total = find[0]

            if message == "Inversions completed":
                line = content[i+1]["message"]
                find = re.findall(r"(\S+) (\S+)", line.replace(',', ''))

                stats.data = {val: key for key, val in find}

                self.post_message(stats)

                # Reset the stats object
                stats = self.Stats()

            if "Analytical line inversions complete" in message:
                find = re.findall(r"(\d+\.\d+s?) (\S+)", message.replace(',', ''))

                stats.data = {val: key for key, val in find}

                self.post_message(stats)

                # Reset the stats object
                stats = self.Stats()

    def filter(self, content):
        """
        Filters the content per the `selected` list
        """
        filtered = []
        for c in content:
            if c['level'] in self.selected:
                filtered.append(c)

        return filtered

    def reconstruct(self, content):
        """
        Reconstructs the content dicts into a string for writing to the log
        """
        lines = []
        for c in content:
            color = self.colours[c['level']]
            level = c['level'].ljust(self.levelPad)
            level = f"[{color}]{level}[/]"

            ts = ''
            if 'Timestamps' in self.selected:
                ts = c['timestamp'] + ' '

            lines.append(
                f"{ts}{level} {c['message']}"
            )

        return lines


class LogController(Container):
    def compose(self):
        self.levels = SelectionList()

        self.stats = DataTable(cursor_type=None)#, zebra_stripes=True)
        self.stats.add_columns("Run", "Inversions", "Time", "Spectra/s", "Spectra/s/core")

        self.logs = IsofitLogs(LOG, highlight=True, markup=True, auto_scroll=False, id="logs")

        with Collapsible(title="Controls & Info", collapsed=False):
            with Container(id="collapse"):
                yield self.levels
                yield self.stats
        yield self.logs

    def on_isofit_logs_levels(self, message):
        """
        Retrieves the levels from a log file to add to the selection list
        """
        self.levels.clear_options()

        levels = ["Timestamps"] + message.levels
        self.logs.selected = levels

        self.levels.add_options([
            (lvl, lvl, True)
            for lvl in levels
        ])

    def on_mount(self):
        self.levels.border_title = "Toggle View"

    def on_isofit_logs_stats(self, message):
        """
        Adds information to the data table
        """
        self.stats.add_row(
            message.name,
            message.total,
            message.data['total'],
            message.data['spectra/s'],
            message.data['spectra/s/core']
        )

    def on_selection_list_selection_toggled(self, message):
        """
        Sets the selected information to show in the logs. `selected` is reactive
        and will update the RichLog when changed
        """
        self.logs.selected = message.selection_list.selected


class Spectra(Container):
    plots = []

    def compose(self):
        ds = xr.open_dataset(RFL, engine='rasterio')
        da = ds.band_data
        self.data = da

        plot = PlotextPlot()
        self.p1 = plot.plt
        yield plot

        plot = PlotextPlot()
        self.p2 = plot.plt
        yield plot

        plot = PlotextPlot()
        self.p3 = plot.plt
        yield plot

    def plot(self, plt, x, y):
        spectra = self.data.isel(x=x, y=y)
        plt.plot(spectra.wavelength.data, spectra.data)
        plt.grid(vertical=True)
        plt.xlabel('Wavelength')
        plt.ylabel('Reflectance')

    def on_mount(self):
        self.plot(self.p1, 20, 20)
        self.plot(self.p2, 30, 30)
        self.plot(self.p3, 40, 40)


class Image(PlotextPlot):
    active = reactive("1")
    colors = {
        "1": (255, 0, 0),
        "2": (0, 255, 0),
        "3": (0, 0, 255)
    }
    preserve = {
        "1": None,
        "2": None,
        "3": None
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ds = xr.open_dataset(RFL, engine='rasterio')
        da = ds.band_data

        self.data = da.mean('band')

    def rgb(self):
        # Retrieve the RGB subset
        rgb = da.isel(band=[60, 40, 30]).transpose('y', 'x', 'band')
        rgb /= rgb.max(['x', 'y']) # Brightens image

        # Convert to pixel coords for easier plotting
        rgb['x'] = range(rgb.x.size)
        rgb['y'] = range(rgb.y.size)

        rgb *= (255.0/rgb.max())

        img = rgb.data.astype(int).tolist()
        img = [[tuple(pixel) for pixel in row] for row in img]

        self.plt.matrix_plot(img, fast=True)

    def meanRFL(self):
        print("Plotting")
        img = self.data * (255 / self.data.max())
        img = [[tuple([int(pixel)] * 3) for pixel in row] for row in img]

        self.original = img
        self.resetImage()
        self.drawImage()

    def resetImage(self):
        self.img = deepcopy(self.original)

    def drawImage(self):
        self.plt.clear_data()
        self.plt.matrix_plot(self.img, fast=True)
        self.refresh()

    def on_mount(self):
        self.meanRFL()
        # self.size.height, self.size.width = self.plt.plotsize()
        self.styles.width = "auto"
        self.styles.width = self.plt.plotsize()[1] + 8

    def on_mouse_down(self, mouse):
        try:
            self.img[mouse.y][mouse.x]
        except:
            return

        for other in self.preserve.values():
            if other and other.x == mouse.x and other.y == mouse.y:
                return

        if (original := self.preserve[self.active]):
            self.img[original.y][original.x] = original.color

        self.preserve[self.active] = SimpleNamespace(
            y = mouse.y,
            x = mouse.x,
            color = self.img[mouse.y][mouse.x]
        )

        self.img[mouse.y][mouse.x] = self.colors[self.active]
        self.drawImage()

        self.post_message(self.PlotSpectra(mouse.x, mouse.y, self.active))

    class PlotSpectra(Message):
        def __init__(self, x, y, active):
            self.x = x
            self.y = y
            self.active = active

            super().__init__()



class ImageContainer(Container):
    active = reactive("1")
    colors = {
        "1": (255, 0, 0),
        "2": (0, 255, 0),
        "3": (0, 0, 255)
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ds = xr.open_dataset(RFL, engine='rasterio')
        da = ds.band_data

        da = da.where(da != da.min(), np.nan)

        self.data = da

    def compose(self):
        self.spectra = {
            "1": PlotextPlot(classes="spectraPlot"),
            "2": PlotextPlot(classes="spectraPlot"),
            "3": PlotextPlot(classes="spectraPlot")
        }
        yield Image(id="DockedImage")
        with Container(id="Spectra"):
            yield self.spectra["1"]
            yield self.spectra["2"]
            yield self.spectra["3"]

    def on_image_plot_spectra(self, message):
        spectra = self.data.isel(x=message.x, y=message.y)

        plot = self.spectra[message.active]
        plt = plot.plt

        plt.clear_data()
        plt.plot(spectra.wavelength.data, spectra.data, color=self.colors[message.active])
        plt.grid(vertical=True)
        plt.xlabel('Wavelength')
        plt.ylabel('Reflectance')

        plot.refresh()

    def watch_active(self, old, new):
        self.spectra[old].styles.border = None
        self.spectra[new].styles.border_left = ("heavy", "yellow")


class ISOFIT(App):
    CSS_PATH = "isofit.tcss"

    def compose(self):
        yield Header()
        yield Footer()

        with TabbedContent():
            if LOG:
                with TabPane("Logs"):
                    yield LogController(id="LogController")
            if RFL:
                with TabPane("Image"):
                    yield ImageContainer()

    def on_key(self, event):
        image = self.query_one(Image)
        cont = self.query_one(ImageContainer)
        if event.key in image.colors:
            image.active = event.key
            cont.active = event.key


app = ISOFIT()

#%%

if __name__ == "__main__":
    assert LOG or RFL, "At least one of LOG or RFL must be defined"
    app.run()

#%%
