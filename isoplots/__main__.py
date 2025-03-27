import os
from types import SimpleNamespace

import click

import isoplots


@click.command()
@click.option("-p", "--path", help="Path to an ISOFIT output directory to load initially")
def browser(path):
    """
    Starts up the browser GUI. Will attempt to detect if the user is in an ISOFIT
    output directory and, if so, auto-load
    """
    from isoplots.isonice.browser import ui, GUI

    if path is None:
        path = os.getcwd()
    GUI.directory.set_value(path)

    ui.run(reload=False)


class CLI(click.MultiCommand):
    """
    Lazy loads the plotting modules so that this can be a subcommand of the isofit CLI
    as well as allow the plotting modules to be dependent on isofit
    """
    def list_commands(self, ctx):
        from isoplots.plots import Modules

        Modules["browser"] = SimpleNamespace(cli=browser)

        return Modules

    def get_command(self, ctx, name):
        from isoplots.plots import Modules

        Modules["browser"] = SimpleNamespace(cli=browser)

        if name in Modules:
            return Modules[name].cli

cli = CLI(name="plot", help="ISOFIT Plotting Utilities")


if __name__ == "__main__":
    cli()
