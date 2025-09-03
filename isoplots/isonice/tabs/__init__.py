import importlib
import logging
import pkgutil
from asyncio import create_task

from nicegui import (
    app,
    ui
)

from isoplots.isonice import WD
from isoplots.isonice.utils.resources import Resources


Logger = logging.getLogger(__name__)

# Auto-discover tab modules
Modules = {
    name: importlib.import_module(f".{name}", __spec__.name)
    for imp, name, _ in pkgutil.iter_modules(__path__)
}

# Sort by module priority, remove if the `Disabled` attribute is set
Modules = {
    Modules[name].Name: Modules[name]
    for name in sorted(Modules, key=lambda name: Modules[name].Prio)
    if not getattr(Modules[name], "Disabled", False)
}


class Tabs:
    disabled = False

    def __init__(self):
        """
        """
        self.buttons = {}
        self.reset = {}
        self.tabs = {}

        with ui.splitter(value=5).classes("w-full h-full") as splitter:
            with splitter.before:
                with ui.tabs().props('vertical').classes('w-full flex-1') as tabs:
                    for name, mod in Modules.items():
                        self.buttons[name] = ui.tab(name, icon=mod.Icon)

                # This will stick to the bottom
                with ui.element('div').classes('w-full flex-1'):
                    self.res = Resources()
                    self.res.start()
                    app.on_shutdown(self.res.stop)

            with splitter.after:
                default = self.buttons[list(self.buttons)[0]]
                with ui.tab_panels(tabs, value=default, on_change=self.tabSelected).classes('w-full h-full'):
                    for name, btn in self.buttons.items():
                        with ui.tab_panel(btn):
                            # Initialize the Tab objects from each module
                            self.tabs[name] = Modules[name].Tab(self)

    async def tabSelected(self, event):
        """
        Awaits the tab.reset task upon selection
        """
        await self.tabs[event.value].resetTask

    def resetTabs(self):
        """
        Resets all tabs by cancelling any running task and restarting
        """
        for tab, obj in self.tabs.items():
            if hasattr(obj, "resetTask"):
                obj.resetTask.cancel()
            obj.resetTask = create_task(obj.reset())

    def toggleTabs(self):
        """
        Toggles the disabled class of the tab buttons
        """
        for name in self.tabs:
            btn = self.buttons[name]

            if self.disabled:
                btn.enable()
            else:
                btn.disable()

        self.disabled = not self.disabled
