import logging

from nicegui import ui

from isoplots.isonice import WD


Logger = logging.getLogger("Configs")

Name = "Configs"
Icon = "settings"
Prio = 1
Disabled = True


class Tab:
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
