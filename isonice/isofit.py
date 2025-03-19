"""
Usage:
    1. Replace the WORKING_DIR var with a path to an isofit output directory
    2. pip install nicegui
    3. python isonice/isofit.py
    4. Acknowledge this is a WORK IN PROGRESS
"""
import logging
import re
from pathlib import Path
from types import SimpleNamespace
from functools import partial

import plotly.express as px
import xarray as xr

WORKING_DIR = "/Users/jamesmo/projects/isofit/research/jemit"
#%

class IsofitLogs:
    colours = {
        "DEBUG"    : "grey",
        "INFO"     : "cyan",
        "WARNING"  : "yellow",
        "ERROR"    : "red",
        "EXCEPTION": "magenta"
    }

    selected = {}
    filtered = None

    def __init__(self, file):
        self.file  = file
        self.stats = []

        self.parse()
        self.extract()

    def parse(self):
        with open(self.file) as file:
            lines = file.readlines()

        self.lvls = set()
        content = []
        for line in lines:
            if (find := re.findall(r"(\w+):(\S+) \|\| (\S+) \| (.*)", line)):
                [find] = find
                level = find[0]
                self.lvls.add(level)

                source = find[2]
                content.append({
                    "timestamp": find[1],
                    "level"    : level,
                    "message"  : find[3]
                })
            elif (find := re.findall(r"(\w+):(\S+) \|\|\|? (.*)", line)):
                [find] = find
                level = find[0]
                self.lvls.add(level)

                content.append({
                    "timestamp": find[1],
                    "level"    : level,
                    "message"  : find[2]
                })
            else:
                content[-1]["message"] += f"\n{line.strip()}"

        self.parsed = content

        lvls = sorted(self.lvls, key=lambda l: getattr(logging, l))
        self.selected = {lvl: True for lvl in lvls}
        # self.selected = self.lvls

        return content

    def extract(self):
        """
        Extracts useful information from the processed logs
        """
        stats = SimpleNamespace()

        for i, line in enumerate(self.parsed):
            message = line["message"]

            if message == "Run ISOFIT initial guess":
                stats.name = "Presolve"

            if message == "Running ISOFIT with full LUT":
                stats.name = "Full Solution"

            if message == "Analytical line inference":
                stats.name = "Analytical Line"

            if (find := re.findall(r"Beginning (\d+) inversions", message)):
                stats.total = find[0]

            if message == "Inversions completed": # V2
                line = content[i+1]["message"]
                find = re.findall(r"(\S+) (\S+)", line.replace(',', ''))

                stats.data = {val: key for key, val in find}

                self.stats.append(stats)

                # Reset the stats object
                stats = SimpleNamespace()

            if "Analytical line inversions complete" in message or "Inversions complete" in message:
                find = re.findall(r"(\d+\.\d+s?) (\S+)", message.replace(',', ''))

                stats.data = {val: key for key, val in find}

                self.stats.append(stats)

                # Reset the stats object
                stats = SimpleNamespace()

    def filter(self):
        """
        Filters the content per the `selected` list
        """
        self.filtered = []
        for c in self.parsed:
            if self.selected[c["level"]]:
                self.filtered.append(c)

        return self.filtered

    def reconstruct(self):
        """
        Reconstructs the content dicts into a string for writing to the log
        """
        if not self.filtered:
            self.filter()

        padding = len(max(self.lvls)) + 1

        lines = []
        for c in self.filtered:
            color = self.colours[c["level"]]
            level = c["level"].ljust(padding)
            # level = f"[{color}]{level}[/]"
            # level = f"<span style='color:{color}'>{level}</>"

            ts = ''
            # if 'Timestamps' in self.selected:
            ts = c['timestamp'] + ' '

            lines.append([
                ts,
                level, color,
                c['message']
            ])

        self.lines = lines

        return lines

    def toggle(self, level, value=None):
        """
        Sets a level's visibility then calls filter and reconstruct

        Parameters
        ----------
        level : str
        value : bool, default=None
        """
        if level not in self.selected:
            raise AttributeError(f"Level not available: {level}")

        if value is None:
            value = not self.selected[level]

        self.selected[level] = value

        self.filter()
        self.reconstruct()


class IsofitOutput:
    logs = None
    lvls = None
    keys = ("rfl", "atm", "lbl", "h2o", "uncert")

    def __init__(self, path, kind=None):
        self.kind = kind
        self.data = {}

        self.path = Path(path)

        if not self.path.exists():
            raise AttributeError(f"Path does not exist: {self.path}")

        self.out = self.path / "output"

        if not self.out.exists():
            raise AttributeError(f"Output path does not exist: {self.out}")

        self.name = next(self.out.rglob("*")).name.split("_")[0]

        if kind is None:
            self.subs = IsofitOutput(path, "_subs_")
            self.full = IsofitOutput(path, "_")

    def __getitem__(self, key):
        return getattr(self, key)

    def __getattr__(self, key):
        if key not in self.keys:
            raise AttributeError(f"Key must be one of: {self.keys}")

        if self.kind != "_subs_":
            if key == "atm":
                key = "atm_interp"

        return self.load(key)

    def load(self, key):
        if self.kind is None:
            return self.full[key]

        if key in self.data:
            return self.data[key]

        file = self.out / (self.name + self.kind + key)
        if not file.exists():
            print(f"File does not exist: {file}")
            return

        self.data[key] = xr.open_dataset(file, engine="rasterio", lock=False)

        return self.data[key]

    def parseLogs(self, file=None):
        if file:
            self.logs = IsofitLogs(file)
        else:
            if not self.logs:
                files = list(self.path.rglob("*.log"))
                if files:
                    self.logs = IsofitLogs(files[0])
                else:
                    print("No log file found")
                    return

    def rgb(self, r=60, g=40, b=30):
        """
        Returns the RGB data of the RFL product

        Parameters
        ----------
        r : int, default=60
            Red band
        g : int, default=40
            Green band
        b : int, default=30
            Blue band

        Returns
        -------
        xr.DataArray
        """
        data = self.rfl.band_data

        # Retrieve the RGB subset
        rgb = data.sel(band=[r, g, b]).transpose('y', 'x', 'band')
        rgb /= rgb.max(['x', 'y']) # Brightens image

        # Convert to pixel coords for easier plotting
        rgb['x'] = range(rgb.x.size)
        rgb['y'] = range(rgb.y.size)

        return rgb

from nicegui import ui

isofit = IsofitOutput(WORKING_DIR)
isofit.parseLogs()
isofit.logs.reconstruct()
#%%

# rgb = isofit.rgb()
# rgb = rgb[:10, :10]
# fig = px.imshow(rgb)
# fig.update_layout(
#     margin = dict(l=0, r=0, t=0, b=0),
#     plot_bgcolor = "rgba(0, 0, 0, 0)",
#     paper_bgcolor = "rgba(0, 0, 0, 0)",
#     showlegend=True
# )
#
# fig.add_trace(go.Scatter(
#     x=[1],
#     y=[1],
#     mode="markers+text",
#     name=f"A",
#     text=[str(100)],
#     textposition="top center"
# ))
# fig.add_trace(go.Scatter(
#     x=[2],
#     y=[2],
#     mode="markers+text",
#     name=f"B",
#     text=[str(200)],
#     textposition="top center"
# ))
# fig.add_trace(go.Scatter(
#     x=[3],
#     y=[3],
#     mode="markers+text",
#     name=f"C",
#     text=[str(300)],
# ))
# fig

#%%


def populateLevels():
    def toggle(event):
        isofit.logs.toggle(event.sender.text, event.value)
        print(isofit.logs.selected)
        populateLogs()

    levels.clear()
    for level, value in isofit.logs.selected.items():
        ui.switch(level, value=value, on_change=toggle)

def populateLogs():
    logs.clear()
    with logs:
        for (ts, lvl, color, msg) in isofit.logs.lines:
            with ui.row():
                ui.label(ts).classes("text-orange")
                ui.label(lvl).classes(f"text-{color}")
                ui.label(msg)


# with ui.tabs().classes('w-full') as tabs:
#     logTab = ui.tab('Logs')
#     spectraTab = ui.tab('Spectra')
#
# with ui.tab_panels(tabs, value=logTab).classes('w-full'):
#     with ui.tab_panel(logTab):
#         with ui.column().classes("h-screen w-full"):
#             with ui.expansion('Settings & Stats').classes('w-full'):
#                 with ui.column().classes("border") as levels:
#                     populateLevels()
#                 # ui.label("testo")
#
#             with ui.element().classes("nicegui-log h-full") as logs:
#                 populateLogs()
#                 # pass
#
#             # with ui.element().classes("nicegui-log h-full"):
#             #     for (ts, lvl, color, msg) in logLines:
#             #         with ui.row():
#             #             ui.label(ts).classes("text-orange")
#             #             ui.label(lvl).classes(f"text-{color}")
#             #             ui.label(msg)
#
#     with ui.tab_panel(spectraTab):
#         ui.label("WIP")

ui.add_head_html('''
    <style type="text/css">
        .nicegui-content {
            padding: 0;
        }
    </style>
''')
import plotly.graph_objects as go
from pprint import pprint

def tabSpectra():
    spectra.clear()
    with spectra:
        def inspect(event):
            print("EVENT "+"="*50)
            # pprint(event.args)

            # Images will only ever have 1 point returned
            point = event.args['points'][0]
            data = point['data']

            if data['type'] == "image":
                i = len(fig.data)
                y, x = point['pointIndex']
                print(f"Point {i}: ({x}, {y})")

                fig.add_trace(go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers+text",
                    name=f"Spectra {i} @ ({x}, {y})",
                    text=[str(i)],
                    textposition="top center"
                ))

            # elif data['type'] == "scatter":
            #     print("Marker")
            #     i = point['curveNumber']
            #     fig.data[i].visible = False

            plot.update()


        rgb = isofit.rgb()
        rgb = rgb[:, :]
        fig = px.imshow(rgb)
        fig.update_layout(
            margin = dict(l=0, r=0, t=0, b=0),
            plot_bgcolor = "rgba(0, 0, 0, 0)",
            paper_bgcolor = "rgba(0, 0, 0, 0)",
            showlegend=True
        )

        plot = ui.plotly(fig).classes('w-25 h-25')

        # Override the event to delete the source string which crashes the server when the image is too large
        plot.on('plotly_click', js_handler="""
            (event) => {
                event.points.forEach(point => delete point.data.source);
                return emitEvent('clickedPoint', event);
            };
        """)
        ui.on('clickedPoint', inspect)

        def test(event):
            print("New EVENT " + "="*50)
            # pprint(event.args)
            data = event.args

            traces = zip(data['1'], data['0']['visible'])
            for i, visibility in traces:
                print(i, visibility)

                # Toggled off
                if visibility == "legendonly":
                    ...

                # Toggled on
                else:
                    ...

        # plot.on('plotly_selected', test)
        # plot.on('plotly_selecting', test)
        # plot.on('plotly_legenddoubleclick', test)
        # plot.on('plotly_legendclick', js_handler="""
        #     (event) => {
        #         //delete event.data[0].source;
        #         delete event.fullLayout;
        #         delete event.fullData;
        #         console.log(event);
        #         return emitEvent('selectedLegend', event);
        #     };
        # """)

        # Default plotly_legendclick is broken as of 3/19/25
        # Just trigger Python to figure it out, no event data
        # plot.on('plotly_legendclick', js_handler="(event) => emitEvent('updateSelected', true);")
        # ui.on('updateSelected', test)

        plot.on("plotly_restyle", test)



tabs = {}
# with ui.splitter(value=5).classes('w-full h-full') as splitter:
#
#     with splitter.before:
#         with ui.tabs().props('vertical').classes('w-full') as tabsObj:
#             tabs["setup"]   = ui.tab('Setup', icon='home')
#             tabs["logs"]    = ui.tab('Logs', icon='density_small')
#             tabs["spectra"] = ui.tab('Spectra', icon='show_chart')
#
#     with splitter.after:
#         with ui.tab_panels(tabsObj, value=tabs["spectra"]).classes('w-full'):
#
#             with ui.tab_panel(tabs["setup"]):
#                 ui.label("SETUP")
#
#             with ui.tab_panel(tabs["logs"]) as tab:
#                 tab.disable()
#                 tabs["logs"].classes("disabled")
                # with ui.column().classes("h-screen w-full"):
                #     with ui.expansion('Settings & Stats').classes('w-full'):
                #         with ui.column().classes("border") as levels:
                #             populateLevels()
                #
                #     with ui.element().classes("nicegui-log h-full") as logs:
                #         populateLogs()
#
#             with ui.tab_panel(tabs["spectra"]) as spectra:
#                 tabSpectra()


class Logs:
    def __init__(self, isofit):
        self.isofit = isofit.logs

        with ui.column().classes("h-screen w-full"):
            with ui.expansion('Settings & Stats').classes('w-full'):
                self.levels = ui.column().classes("border")

            self.lines = ui.element().classes("nicegui-log h-full")

        self.reset()

    def reset(self):
        self.populateLevels()
        self.populateLogs()

    def populateLevels(self):
        def toggle(event):
            self.isofit.toggle(event.sender.text, event.value)
            print(self.isofit.selected)
            self.populateLogs()

        self.levels.clear()
        for level, value in self.isofit.selected.items():
            ui.switch(level, value=value, on_change=toggle)

    def populateLogs(self):
        self.lines.clear()
        with self.lines:
            for (ts, lvl, color, msg) in self.isofit.lines:
                with ui.row():
                    ui.label(ts).classes("text-orange")
                    ui.label(lvl).classes(f"text-{color}")
                    ui.label(msg)

class Tabs:
    valid = {
        "setup"  : True,
        "config" : False,
        "logs"   : True,
        "spectra": True,
        "luts"   : True,
    }

    def __init__(self):
        self.isofit = isofit

        with ui.splitter(value=5).classes('w-full h-full') as splitter:
            with splitter.before:
                with ui.tabs().props('vertical').classes('w-full') as self.tabs:
                    self.btns = {
                        "setup"  : ui.tab('Setup', icon='home'),
                        "config" : ui.tab('Config', icon='settings'),
                        "logs"   : ui.tab('Logs', icon='density_small'),
                        "spectra": ui.tab('Spectra', icon='show_chart'),
                        "luts"   : ui.tab('LUTs', icon='ssid_chart'),
                    }
            with splitter.after:
                self.pnls = {}

                with ui.tab_panels(self.tabs, value=self.btns["setup"]).classes('w-full') as self.panels:
                    for name, btn in self.btns.items():
                        with ui.tab_panel(btn) as self.pnls[name]:
                            self[name]()

        self.toggleTabs()

    def toggleTabs(self):
        for name, panel in self.pnls.items():
            tab = self.btns[name]
            if not self.valid[name]:
                panel.disable()
                tab.disable()
                tab.classes(add="disabled")
            else:
                panel.enable()
                tab.enable()
                tab.classes(remove="disabled")

    def __getitem__(self, key):
        return getattr(self, key)

    def setup(self):
        panel = self.pnls["setup"]
        panel.clear()
        with panel:
            ui.label("SETUP")

    def config(self):
        panel = self.pnls["config"]
        panel.clear()
        with panel:
            ui.label("config")

    def logs(self):
        panel = self.pnls["logs"]
        # panel.clear()
        with panel:
            self._logs = Logs(self.isofit)

        #     with ui.column().classes("h-screen w-full"):
        #         with ui.expansion('Settings & Stats').classes('w-full'):
        #             with ui.column().classes("border") as self.logs.levels:
        #                 populateLevels()
        #
        #         with ui.element().classes("nicegui-log h-full") as logs:
        #             populateLogs()

    def spectra(self):
        panel = self.pnls["spectra"]
        panel.clear()
        with panel:
            def addAnotation(event):
                print("EVENT "+"="*50)
                # pprint(event.args)

                # Images will only ever have 1 point returned
                point = event.args['points'][0]
                data = point['data']

                if data['type'] == "image":
                    i = len(fig.data)
                    y, x = point['pointIndex']
                    print(f"Point {i}: ({x}, {y})")

                    fig.add_trace(go.Scatter(
                        x=[x],
                        y=[y],
                        mode="markers+text",
                        name=f"Spectra {i} @ ({x}, {y})",
                        text=[str(i)],
                        textposition="top center"
                    ))

                # elif data['type'] == "scatter":
                #     print("Marker")
                #     i = point['curveNumber']
                #     fig.data[i].visible = False

                plot.update()

            rgb = isofit.rgb()
            rgb = rgb[:, :]
            fig = px.imshow(rgb)
            fig.update_layout(
                margin = dict(l=0, r=0, t=0, b=0),
                plot_bgcolor = "rgba(0, 0, 0, 0)",
                paper_bgcolor = "rgba(0, 0, 0, 0)",
                showlegend=True
            )

            plot = ui.plotly(fig).classes('w-25 h-25')

            # Override the event to delete the source string which crashes the server when the image is too large
            plot.on('plotly_click', js_handler="""
                (event) => {
                    event.points.forEach(point => delete point.data.source);
                    return emitEvent('clickedPoint', event);
                };
            """)
            ui.on('clickedPoint', addAnotation)

    def luts(self):
        panel = self.pnls["luts"]
        panel.clear()
        with panel:
            ui.label("luts")

t = Tabs()


#%%
dark = ui.dark_mode()
dark.enable()

ui.run()
#%%
