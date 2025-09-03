import logging
import socket

import plotly.express as px
import plotly.graph_objects as go
import xarray as xr


Logger = logging.getLogger(__name__)


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
