import os
from types import SimpleNamespace

import click

import isoplots


class LazyIsonice:
    def __getattr__(self, key):
        from isoplots.isonice import app

        return getattr(app, key)


class CLI(click.MultiCommand):
    """
    Lazy loads the plotting modules so that this can be a subcommand of the isofit CLI
    as well as allow the plotting modules to be dependent on isofit
    """
    def _load_modules(self):
        from isoplots.plots import Modules

        Modules["browser"] = LazyIsonice()

        return Modules

    def list_commands(self, ctx):
        return self._load_modules()

    def get_command(self, ctx, name):
        modules = self._load_modules()
        if name in modules:
            return modules[name].cli

cli = CLI(name="plot", help="ISOFIT Plotting Utilities")


if __name__ == "__main__":
    cli()
