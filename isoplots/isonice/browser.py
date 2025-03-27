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
    # "emit": "/Users/jamesmo/projects/isofit/research/jemit/"
}


def plotlyColor(i):
    c = px.colors.qualitative.Plotly
    return c[i % len(c)]


IsofitFiles = {
    "config": {
        "desc": "Configuration JSON files",
        "files": {
            # Presolve
            "*_h2o.json": "TODO",
            "*_h2o.json.tmpl": "TODO",
            "*_h2o_tpl.json": "TODO",
            # Full
            "*_isofit.json": "TODO",
            "*_isofit.json.tmpl": "TODO",
            "*_modtran_tpl.json": "TODO",
        },
    },
    "data": {
        "desc": "TODO",
        "files": {
            "channelized_uncertainty.txt": "TODO",
            "model_discrepancy.mat": "TODO",
            "surface.mat": "TODO",
            "wavelengths.txt": "TODO"
        },
    },
    "lut_h2o": {
        "desc": "TODO",
        "files": {
            "6S.lut.nc": "LUT produced by the SixS radiative transfer model for sRTMnet",
            "lut.nc": "Look-Up-Table for the radiative transfer model",
            "sRTMnet.predicts.nc": "Output predicts of sRTMnet"
        },
    },
    "lut_full": {
        "desc": "TODO",
        "files": {
            "6S.lut.nc": "LUT produced by the SixS radiative transfer model for sRTMnet",
            "lut.nc": "Look-Up-Table for the radiative transfer model",
            "sRTMnet.predicts.nc": "Output predicts of sRTMnet"
        },
    },
    "output": {
        "desc": "TODO",
        "files": {
            # Presolve
            "*_subs_atm": "TODO",
            "*_subs_h2o": "TODO",
            "*_subs_rfl": "TODO",
            "*_subs_state": "TODO",
            "*_subs_uncert": "TODO",
            # Full
            "*_atm_interp": "TODO",
            "*_rfl": "TODO",
            "*_lbl": "TODO",
            "*_uncert": "TODO",
        }
    }
}


class IsofitLogs:
    _lvlColors = {
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
        """
        Parses an ISOFIT log file into a dictionary of content that can be used to
        filter and reconstruct lines into different formats

        Returns
        -------
        content : list[dict]
            Parsed content from the log file in the form:
                {
                    "timestamp": str,
                    "level": str,
                    "message": str
                }
        """
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
        self.selected = {"timestamps": True} | {lvl: True for lvl in lvls}
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

    def filter(self, select=0):
        """
        Filters the content per the `selected` dict

        Parameters
        ----------
        select : str | list[str] | None, default=0
            Toggles selections in the `selected` attribute. Options:
            - "all" = Enable all options
            - None  = Disable all options
            - str   = Enable only this option
            - list  = Enable only these options
            - Anything else, such as the default 0, will do nothing and use the current
              selected dict
        """
        if select == "all":
            for key in self.selected:
                self.selected[key] = True
        if select == None:
            for key in self.selected:
                self.selected[key] = False
        if isinstance(select, str):
            for key in self.selected:
                self.selected[key] = False
            if key in self.selected:
                self.selected[key] = True
        if isinstance(select, list):
            for key in self.selected:
                self.selected[key] = False
            for key in select:
                if key in self.selected:
                    self.selected[key] = True

        self.filtered = []
        for c in self.parsed:
            if self.selected[c["level"]]:
                self.filtered.append(c)

        return self.filtered

    def build(self):
        """
        Builds the filtered contents dict into a list of tuples to be used for writing
        to the log. Timestamps can be disabled by setting:
            self.selected["timestamps"] = False

        Returns
        -------
        lines : list[tuple[str, str, str]]
            Returns a list of 3-pair tuples of strings in the form:
                (timestamp, padded level, log message)
            Timestamp will be an empty string if it is not enabled
            The level is right-padded with whitespace to the length of the longest log
            level (eg. "warning", "debug  ")
            This will also be saved in self.lines
        """
        if not self.filtered:
            self.filter()

        # The colors dict uses the padded string for easy lookup
        self.colors = {}

        padding = len(max(self.lvls)) + 1

        lines = []
        for c in self.filtered:
            color = self._lvlColors[c["level"]]
            level = c["level"].ljust(padding)

            self.colors[level] = color

            ts = ''
            if self.selected['timestamps']:
                ts = c['timestamp'] + ' '

            lines.append([
                ts,
                level,
                c['message']
            ])

        self.lines = lines

        return lines

    def toggle(self, level, value=None):
        """
        Sets a level's visibility then calls filter and build

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
        self.build()


class IsofitData:
    keys = ("rfl", "atm", "lbl", "h2o", "uncert", "config")

    def __init__(self, path, kind=None):
        self.kind = kind
        self.data = {}

        self.path = Path(path)

        if not self.path.exists():
            raise AttributeError(f"Path does not exist: {self.path}")

        self.out = self.path / "output"

        if not self.out.exists():
            raise AttributeError(f"Output path does not exist: {self.out}")

        rfl = list(self.out.rglob("*_rfl"))
        if not rfl:
            raise AttributeError("A reflectance file is not found in the output -- is this an incomplete run?")

        self.name = rfl[0].name[:-4].replace("_subs", "")

        if kind is None:
            self.subs = IsofitData(path, "_subs_")
            self.full = IsofitData(path, "_")

    def __getitem__(self, key):
        args = []
        if isinstance(key, tuple):
            key, *args = key

        if key not in self.keys:
            raise AttributeError(f"Key must be one of: {self.keys}, got: {key!r}")

        if self.kind != "_subs_":
            if key == "atm":
                key = "atm_interp"

        return self.load(key, *args)

        # return getattr(self, key, **kwargs)

    def __getattr__(self, key):
        return self[key]

    def __repr__(self):
        return f"<{self.__class__.__name__} kind={self.kind}>"

    def load(self, key=None, name=None, **kwargs):
        if name:
            return self._load_raster(name=name)

        # Passthrough directly to the full run
        if self.kind is None:
            return self.full.load(key=key, **kwargs)

        if key in self.data:
            return self.data[key]

        if key == "config":
            return self._load_config(**kwargs)

        return self._load_raster(key=key)

    def _load_config(self, file=None, tpl=False, tmpl=False):
        """
        Loads a configuration json

        Parameters
        ----------
        file : str, default=None
            Filename to load from the config directory
        tpl : bool, default=False
            Load the modtran config
        tmpl : bool, default=False
            Load the template config

        Returns
        -------
        dict
            Loaded JSON dictionary
        """
        if not file:
            kind = self.kind + "isofit"
            if self.kind == "_subs_":
                kind = "_h2o"
                modtran = "_tpl"

            file = self.name + kind

            if tpl:
                # if kind == "_":
                #     file += "modtran"
                file = file.replace("isofit", "modtran")
                file += "_tpl"
            file += ".json"

            if tmpl:
                file += ".tmpl"

        file = self.path / "config" / file
        if not file.exists():
            print(f"File does not exist: {file}")
            return

        print(f"Loading {file}")
        with open(file, "rb") as f:
            return json.load(f)

    def _load_raster(self, key=None, name=None):
        if name:
            file = self.out / name
        elif key:
            file = self.out / (self.name + self.kind + key)
        else:
            raise AttributeError("Either the key or filename must be given")

        if not file.exists():
            print(f"File does not exist: {file}")
            return

        self.data[key] = xr.open_dataset(file, engine="rasterio", lock=False)

        return self.data[key]

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

    def getConfigs(self):
        path = self.path / "config"
        if self.kind is None:
            files = path.rglob("*.json*")
        elif self.kind == "_subs_":
            files = path.rglob("*_h2o*.json*")
        else:
            files = path.rglob("*_[i,m]*.json*")
        return list(files)

    def getOutputs(self):
        files = []
        for file in self.out.glob("*"):
            if file.suffix:
                continue
            if not self.kind:
                files.append(file)
            elif self.kind == "_":
                if "_subs" not in file.name:
                    files.append(file)
            elif self.kind == "_subs_":
                if "_subs" in file.name:
                    files.append(file)
        return files


class IsofitOutput:
    _dirs = ("config", "data", "input", "lut_full", "lut_h2o", "output")

    def __init__(self, path, invalid=False):
        """
        TODO

        Parameters
        ----------
        path : str
            Path to either an ISOFIT configuration file or an output directory. If a
            config file, will attempt to detect the output directory from it.
        invalid : bool, default=False
            Allow an invalid path. This may be used to initialize an empty object and
            change it via changePath()
        """
        self.dirs = {}
        self.path = Path(path)
        self.data = None
        self._logs = None
        self.logFile = None
        self.invalid = invalid

        if self.path.is_file():
            for parent in self.path.parents:
                dirs = self.findSubdirs(parent)
                if any(dirs.values()):
                    self.path = parent
                    self.dirs = dirs
                    self.data = IsofitData(self.path)
                    break
            else:
                self._error("Could not find a valid working directory given the configuration file")

        elif any((dirs := self.findSubdirs(self.path)).values()):
            self.dirs = dirs
            self.data = IsofitData(self.path)

        else:
            self._error("Could not find a valid working directory")

    def __repr__(self):
        return f"<IsofitOutput: {self.path}>"

    def changePath(self, *args, **kwargs):
        """
        Re-initializes the existing object by simply calling __init__. Useful for
        maintaining a single object that must change working directories

        Parameters
        ----------
        *args : list
            Passthrough arguments
        **kwargs : dict
            Passthrough key-word arguments
        """
        self.__init__(*args, **kwargs)
        return self

    def findSubdirs(self, path):
        return {
            subdir: (path / subdir).exists()
            for subdir in self._dirs
        }

    def makeTree(self):
        tree = []
        for _dir, data in IsofitFiles.items():
            subpath = self.path / _dir
            children = []
            if subpath.exists():
                tree.append({"id": _dir, "desc": data["desc"], "children": children})
                for name, desc in data["files"].items():
                    if files := list(subpath.glob(name)):
                        for file in files:
                            children.append({"id": file.name, "desc": desc})

        return tree

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

    def setLogFile(self, file=None):
        """
        Sets the log file

        Parameters
        ----------
        file : str, default=None
            Filepath to a log file to parse. If None, resets the stored log file and
            will attempt to automatically find one on the next access of the `logs`
            attribute

        Raises
        -------
        FileNotFoundError
            If the provided log file does not exist
        """
        if file:
            if not Path(file).exists():
                return self._error(f"Log file does not exist: {file}")
        self.logFile = file

    @property
    def logs(self):
        if self._logs is None:
            if self.logFile is None:
                files = list(self.path.rglob("*.log"))
                if files:
                    self.logFile = files[0]

            if self.logFile:
                self._logs = IsofitLogs(self.logFile)
            else:
                self._error("No log file found. Please set one via setLogFile()")
        return self._logs

    def _error(self, message):
        if not self.invalid:
            raise FileNotFoundError(message)
        print(message)

#%%

class Logs:
    logs = None

    def __init__(self):
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

        try:
            if isofit and isofit.logs:
                self.logs = isofit.logs
        except:
            self.logs = None
            with self.lines:
                ui.chip(
                    "No log file found. If it is outside of the directory, place it somewhere inside with the extension .log",
                    icon  = "error",
                    color = "red"
                ).classes("w-full")

        if self.logs:
            self.logs.filter(None)
            self.logs.build()

            self.populateLogs()
            self.populateLevels()

    def toggleLevel(self, event):
        self.logs.toggle(event.sender.text, event.value)
        self.populateLogs()

    def populateLevels(self):
        self.levels.clear()
        with self.levels:
            for level, value in self.logs.selected.items():
                ui.switch(level, value=value, on_change=self.toggleLevel)

    def populateLogs(self):
        self.lines.clear()
        with self.lines:
            for (ts, lvl, msg) in self.logs.lines:
                color = self.logs.colors[lvl]
                with ui.row():
                    ui.label(ts).classes("text-orange")
                    ui.label(lvl).classes(f"text-{color}")
                    ui.label(msg)


class Spectra:
    plot = None
    data = None
    opts = None

    def __init__(self):
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
        if isofit and isofit.data:
            self.data = isofit.data

        if self.data:
            self.spectras.clear()

            # opts = [file.name for file in self.data.getOutputs()]
            opts = [f"{self.data.name}_rfl"]

            if opts != self.opts:
                self.opts = opts

                # Always default to the full RFL data
                self.select.set_options(self.opts, value=f"{self.data.name}_rfl")
            else:
                self.plotImage(self.rgb)

    async def changeFile(self, event):
        file = event.value
        # data = self.data.load(name=file)
        # data = await run.io_bound(self.data.load, name=file)
        # if "_subs" in file:
        #     self.rgb = await run.io_bound(self.data.subs.rgb)
        # else:
        self.rgb = await run.io_bound(self.data.full.rgb)

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
            spectra = self.data.rfl.isel(x=x, y=y)
            spectra = spectra.rename(band_data='Reflectance', wavelength='Wavelength')
            spectra = spectra.where(spectra != spectra.min())
            data = spectra.Reflectance
            df = data.to_dataframe()

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

    def __init__(self):
        with ui.row():
            self.select = ui.select([], label="Select a Configuration", on_change=self.loadConfig)
            ui.switch("Editable", value=False, on_change=self.readOnly).classes("h-full")

        self.editor = ui.json_editor({'content': {'json': {}}, 'readOnly': True}).classes('w-full jse-theme-dark')

    async def reset(self, isofit=None):
        if isofit and isofit.data:
            self.data = isofit.data

        if self.data:
            configs = [file.name for file in self.data.getConfigs()]
            self.select.set_options(configs, value=configs[0])

    def loadConfig(self, event):
        data = self.data.load("config", file=event.value)
        self.editor.run_editor_method('updateProps', {'content': {'json': data}})

    def readOnly(self, event):
        self.editor.run_editor_method('updateProps', {'readOnly': not event.value})


class LUTs:
    def __init__(self):
        ...

    async def reset(self, isofit=None):
        ...


class Setup:
    def __init__(self):
        ...

    async def reset(self, isofit=None):
        ...

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
                                if name == "setup":
                                    self[name]()
                                else:
                                    self.tabs[name] = self.tabs[name]()

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

    def __getitem__(self, key):
        return getattr(self, key)

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

    def navToFile(self, name):
        nodes = self.tree.props['nodes']
        headers = [h['id'] for h in nodes]

        if name in headers:
            self.tree.collapse()
            self.tree.expand([name])
            # if name in self.tree.props.get("expanded", []):
            #     self.tree.collapse([name])
            # else:
            #     self.tree.expand([name])
        else:
            for node in nodes:
                for child in node['children']:
                    if child['id'] == name:
                        print(node['id'], name)

    def setIsofit(self, value):
        self.directoryTree.clear()

        # Try to parse the input path
        try:
            self.isofit = IsofitOutput(value)
            # self.isofit.changePath(value)
        except Exception as e:
            # Output to UI the error
            self.toggleTabs(False)
            return str(e)

        self.toggleTabs(True)
        # self.resetTabs()

        # Set the output directory tree
        with self.directoryTree:
            data = self.isofit.makeTree()

            ui.label("Click on an output file below to jump to an interactive component for that file [Work in Progress]")
            # ui.label("Detected paths:")

            self.tree = ui.tree(data, on_select=lambda e: self.navToFile(e.value)).classes("border h-full w-full")
            self.tree.add_slot('default-header', '''
                <span :props="props">{{ props.node.id }}</strong></span>
            ''')
            self.tree.add_slot('default-body', '''
                <span :props="props">{{ props.node.desc }}</span>
            ''')

    def setup(self):
        panel = self.pnls["setup"]
        # panel.clear()
        with panel:
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

            self.directoryTree = ui.column().classes("w-full h-full")

    def config(self):
        def loadConfig(event):
            data = self.isofit.data.load("config", file=event.value)
            editor.run_editor_method('updateProps', {'content': {'json': data}})

        def readOnly(event):
            editor.run_editor_method('updateProps', {'readOnly': not event.value})

        panel = self.pnls["config"]
        panel.clear()

        if self.isofit and self.isofit.data is not None:
            configs = [c.name for c in isofit.data.getConfigs()]

            with panel:
                with ui.row():
                    ui.select(configs, value=configs[0], label="Select a Configuration", on_change=loadConfig)
                    ui.switch("Editable", value=False, on_change=readonly)

                # data = self.isofit.data.load("config", file=configs[0])
                data = {}
                editor = ui.json_editor({'content': {'json': data}, 'readOnly': True}).classes('w-full jse-theme-dark')
                # editor.run_editor_method('updateProps', {'readOnly': True})

    def logs(self):
        panel = self.pnls["logs"]
        # panel.clear()
        with panel:
            self.Logs = Logs()

    def spectra(self):
        panel = self.pnls["spectra"]
        panel.clear()
        with panel:
            self.Spectra = Spectra()

    def luts(self):
        panel = self.pnls["luts"]
        panel.clear()


GUI = Tabs()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
