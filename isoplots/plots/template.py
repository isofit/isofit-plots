"""
This is a template for constructing new plotting functions and attaching them to the
CLI. Copy the file and remove the comments to get started.
"""
import click


# This can be renamed but be sure to propagate that name elsewhere
def plot(file, flag=False):
    """\
    Description of your plot

    \b
    Parameters
    ----------
    file : str
        Path to the input file
    flag : bool, default=False
        Enable/disable some functionality
    """
    print(file, flag)

# The name must be unique as this is what will show as the subcommand on the CLI
# Note the help param points to the function docstring so it is copied
@click.command(name="template", no_args_is_help=True, help=plot.__doc__)
@click.argument("file")                     # Arguments are required, positional inputs
@click.option("-f", "--flag", is_flag=True) # Default values on options should be set as default values in the plotting function as well for consistency
def cli(**kwargs):                          # Do not rename this function
    print("Plotting template")

    plot(**kwargs)

    print("Finished")

# Enable this script to be called directly
if __name__ == "__main__":
    cli()
