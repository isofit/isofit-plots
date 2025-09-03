import logging

import plotly.express as px
import plotly.graph_objects as go
import xarray as xr


Logger = logging.getLogger(__name__)


def blank():
    """
    Creates a blank plotly figure with an empty scatter trace so that it renders
    the plot in the GUI. Without the scatter, the plot will be invisible

    Returns
    -------
    go.Figure
        Blank plotly figure
    """
    return go.Figure(go.Scatter())


def plotlyColor(i):
    """
    Retrieves a plotly color for a given index

    Parameters
    ----------
    i : int
        Index color, wraps if the index exceeds to length of the color list

    Returns
    -------
    str
        Hex color
    """
    c = px.colors.qualitative.Plotly
    return c[i % len(c)]


def multiplot(figs=[], height=300, sharex="all", sharey="all", dark=True):
    """
    Creates a multi plot object that shares X and Y axes

    Parameters
    ----------
    figs : list[go.Figure]
        List of subplots to add
    height : int, default=300
        Height of each subplot
    sharex : TODO, default="all"
        Plotly figure .set_subplots parameter shared_xaxes
    sharey : TODO, default="all"
        Plotly figure .set_subplots parameter shared_yaxes
    dark : bool, default=True
        Sets the plotly template to dark

    Returns
    -------
    fig : go.Figure
        Plotly figure with one or more subplots
    """
    # Ensure at least one figure is set
    if not figs:
        figs = [go.Figure()]

    titles = [fig.layout.title.text for fig in figs]
    spacing = 0.01 # Minimal spacing when no titles are present
    topMargin = 0
    if titles:
        topMargin = 20 # Needed so the top plot's title is shown
        spacing = 0.1 / len(titles)

    fig = go.Figure()
    fig.set_subplots(
        rows = len(figs),
        cols = 1,
        shared_xaxes = sharex,
        shared_yaxes = sharey,
        subplot_titles = titles,
        vertical_spacing = spacing,
    )

    if dark:
        fig.update_layout(
            template = "plotly_dark",
            paper_bgcolor = "rgba(0, 0, 0, 0)",
        )

    fig.update_layout(
        margin = dict(l=0, r=20, t=topMargin, b=0),
        height = height*len(figs),
    )

    for i, plot in enumerate(figs):
        for trace in plot.data:
            fig.add_trace(trace, row=i+1, col=1)

    return fig
