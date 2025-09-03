import json
import logging
import os
from asyncio import sleep
from pathlib import Path

from nicegui import (
    run,
    ui
)

from isoplots.isonice import (
    Config,
    WD
)
from isoplots.isonice.utils.enhancedinput import EnhancedInput

Logger = logging.getLogger(__name__)

Name = "Setup"
Icon = "home"
Prio = 0


def toNiceGUITree(tree=None, *, path=None, nodes=None):
    """
    Recursively converts an IsofitWD tree (with info) into a NiceGUI-compatible data
    structure for the tree component

    Parameters
    ----------
    tree : dict, default=None
        Tree object created by IsofitWD.getTree(info=True)
    nodes : list, default=None
        Converted nodes for the tree component, this likely should be left as the
        default

    Returns
    -------
    nodes : list
        Converted nodes for the tree component
    """
    if tree is None:
        tree = WD.getTree(info=True)

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


class Tab:
    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : Tabs
            Parent tabs object, for back-reference
        """
        self.parent = parent

        with ui.row().classes("w-full items-center"):
            with ui.button(
                icon = "settings_suggest",
                on_click = self.setWD

            ).props("outline dense").classes("h-full"):
                with ui.tooltip():
                    ui.label("Set this path as the active working directory")
                    ui.label("This will recursively search for ISOFIT products")
                    ui.label("Only do this on known directories as this can be an expensive operation")

            self.search = EnhancedInput(
                label = "Search",
                animated = False
            ).classes("flex-grow")

        self.preview = ui.column().classes("w-full")

        self.filter = ui.input("filter").classes("w-full")
        self.filter.visible = False
        self.directoryTree = ui.scroll_area().classes("w-full h-full")
        self.stepper()

    def addConfigPaths(self):
        """
        Adds paths from the config to the EnhancedInput options tab
        """
        if "Paths" in Config:
            self.search.set_options(Config["Paths"].values())
            self.search.set_tab("Options")

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

    def stepper(self):
        """
        Leverages a NiceGUI Stepper to provide loading information

        Returns
        -------
        stepper : ui.stepper
            Stepper object
        """
        self.directoryTree.clear()
        with self.directoryTree:
            with ui.stepper().props("vertical").classes("w-full") as stepper:
                with ui.step(f"Setting path"):
                    with ui.row():
                        ui.label("Select a path above and hit the")
                        ui.icon("settings_suggest", size="sm")
                        ui.label("button to get started")
                    ui.label("Having an active working directory simplifies many of the UI features")
                    ui.label("Alternatively, select tabs on the left and manually input products")
                    ui.label("While processing a path, the tabs will be disabled to protect against thread race conditions")
                with ui.step("Recursively searching for ISOFIT products"):
                    ui.skeleton().classes("w-full")
                    ui.label("Depending on the depth of the chosen directory, this may take a moment")
                with ui.step("Building directory tree"):
                    ui.skeleton().classes("w-full")
                    ui.label("This typically takes the longest to parse the directory tree into a readable format")
                    ui.label("Please be patient, there is no progress indicator but it is working")
                    ui.label("If this takes more than two minutes, please open an issue on the repository with a copy of your terminal logs")
                with ui.step("Rendering UI"):
                    ui.skeleton().classes("w-full")

        return stepper

    async def reset(self):
        """
        """
        self.addConfigPaths()

    async def setWD(self):
        """
        Sets the global IsofitWD object
        """
        # Disable buttons while loading
        self.parent.toggleTabs()

        path = self.search.value
        self.filter.visible = False

        stepper = self.stepper()
        stepper.next() # Setting path, done

        await run.io_bound(WD.reset, path, recursive=True)

        # Set the path as the working directory for the overall Python instance
        os.chdir(path)

        self.parent.resetTabs()
        stepper.next() # Recursively search, done

        data = await run.io_bound(toNiceGUITree)
        data[0]["label"] = str(WD.path)
        stepper.next() # Building tree, done

        # Makes the UI feel more responsive by giving a slight pause after the last step
        await sleep(0.5)

        # Re-enable the tabs
        self.parent.toggleTabs()

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
                    Logger.error("Cannot load files on the base")
