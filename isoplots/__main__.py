import click

import isoplots


class CLI(click.MultiCommand):
    """
    Lazy loads the plotting modules so that this can be a subcommand of the isofit CLI
    as well as allow the plotting modules to be dependent on isofit
    """
    def list_commands(self, ctx):
        from isoplots.plots import Modules

        return Modules

    def get_command(self, ctx, name):
        from isoplots.plots import Modules

        if name in Modules:
            return Modules[name].cli

cli = CLI(name="plot", help="ISOFIT Plotting Utilities")


if __name__ == "__main__":
    cli()
