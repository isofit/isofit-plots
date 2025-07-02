import logging

from nicegui import ui

from isoplots.isonice import WD


Logger = logging.getLogger("Logs")

Name = "Logs"
Icon = "density_small"
Prio = 1
Disabled = True


class Tab:
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
        except:
            Logger.exception(f"Failed to load logs")

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
