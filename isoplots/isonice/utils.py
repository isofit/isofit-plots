import logging
import socket

import plotly.express as px
import plotly.graph_objects as go
import xarray as xr


Logger = logging.getLogger("App")


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


def multiplot(figs=[], height=300):
    """
    Creates a multi plot object that shares X and Y axes

    Parameters
    ----------
    figs : list[go.Figure]
        List of subplots to add
    height : int, default=300
        Height of each subplot

    Returns
    -------
    fig : go.Figure
        Plotly figure with one or more subplots
    """
    # Ensure at least one figure is set
    if not figs:
        figs = [go.Figure()]

    fig = go.Figure()
    fig.set_subplots(
        rows = len(figs),
        cols = 1,
        shared_xaxes = 'all',
        shared_yaxes = 'all',
        vertical_spacing = 0.01
    )
    fig.update_layout(**{
        "margin": dict(l=0, r=20, t=0, b=0),
        "paper_bgcolor": "rgba(0, 0, 0, 0)",
        "template": "plotly_dark",
        "height": height*len(figs),
    })

    for i, plot in enumerate(figs):
        for trace in plot.data:
            # fig.update_layout(legendgroup=f"{i+1}")
            fig.add_trace(trace, row=i+1, col=1)

    # TODO: Get subplots to have their own legends
    # Does not work
    # try:
    #     for i, yaxis in enumerate(fig.select_yaxes()):
    #         i += 1
    #         legend_name = f"legend{i}"
    #         if yaxis.domain is not None:
    #             fig.update_layout({legend_name: dict(y=yaxis.domain[1], yanchor="top")}, showlegend=True)
    #             fig.update_traces(row=i, legend=legend_name)
    # except:
    #     pass

    return fig


def portAvail(port: int) -> bool:
    """
    checks if a port is available

    Parameters
    ----------
    port : int
        Port to check

    Returns
    -------
    bool
        True if available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0


def checkPorts(start: int, end: int = 100) -> None:
    """
    Checks for an open port between the start and end range

    Parameters
    ----------
    start : int
        Starting port
    end : int
        Offset end from the starting point to check in range of
    """
    if not portAvail(start):
        for port in range(start+1, start+end):
            Logger.info(f"Checking {port}")
            if portAvail(port):
                Logger.warning(f"Port {start} is already in use, recommend using --port {port}")
                break
        else:
            Logger.error(f"All ports between {start}-{start+end} are in use")
