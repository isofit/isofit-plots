"""
Usage:
    1. pip install nicegui
    2. python isonice/isofit.py
    3. Acknowledge this is a WORK IN PROGRESS
"""

import json
import logging
import re

from asyncio import create_task
from pathlib import Path

import click
from nicegui import (
    app,
    run,
    ui
)

from isoplots.isonice import Config
from isoplots.isonice.tabs import Tabs


Logger = logging.getLogger("App")


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


GUI = Tabs()
app.on_startup(GUI.resetTabs)


def launch(path=".", config=None, check=False, **kwargs):
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
        Logger.info("Checking ports")
        checkPorts(kwargs.get("port", 8080))

    if path:
        Logger.info(f"Setting path: {path}")
        GUI.tabs["Setup"].search.set_value(path)

    if config is None:
        config = Path(__file__).parent / "static" / "paths.ini"

    if Path(config).exists():
        Logger.info(f"Reading config: {config}")
        Config.read(config)

        GUI.tabs["Setup"].addPathButtons()

    Logger.info("Launching")
    ui.run(**kwargs)


@click.command()
@click.option("-p", "--path", default=".", help="Working directory to initially load with")
@click.option("-c", "--config", help="")
@click.option("--check", default=False, is_flag=True, help="Checks for an open port up to 100 after the given port. May cause a delay in startup")
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
