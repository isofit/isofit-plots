import json
import logging
from datetime import datetime as dtt

import click
import plotly.graph_objects as go

from isoplots.isonice.utils import plots
from isoplots.isonice.utils.wd import Logs


Logger = logging.getLogger(__name__)


def annotate(fig, log, base_y=-0.07, step=-0.02, relative=False):
    """
    Annotates a figure with specific markers from the ISOFIT log

    Parameters
    ----------
    fig : go.Figure
        Figure to annotate
    logs : str
        Path to a logs file to parse for annotations
    base_y : float, default=-0.07
        Starting Y position relative to the paper dimensions of the figure
    step : float, default=-0.02
        Step amount to take for each new annotation so that the strings don't overlap
    relative : bool, default=False
        Uses the relative seconds time instead of the actual timestamps

    Returns
    -------
    fig : go.Figure
        Annotated figure
    """
    Logger.debug(f"Parsing log file: {log}")
    logs = Logs(log)
    logs.read()

    for i, (label, line) in enumerate(logs.markers):
        if relative:
            ts = line["relative_datetime"]
        else:
            # Convert to timestamp
            ts = line["datetime"].timestamp() * 1000

        Logger.debug(f"Annotation added at {ts}: {label!r}")

        # Add the vertical line and the annotation separately
        fig.add_vline(x=ts, line_dash="dash", line_width=1)
        fig.add_annotation(
            x = ts,
            y = base_y + i * step,
            xref = "x",
            yref = "paper",
            text = label,
            showarrow = False,
            font = dict(size=12),
        )

    Logger.debug("Resizing plot so that annotations are visible")

    # Add a bottom margin to allow the annotations to show up
    # Resize the total height of the figure so it doesn't become squished with too many annotations
    height = fig.layout.height
    margin = 20 * i
    fig.update_layout(
        height = height+margin,
        margin = dict(b=margin)
    )

    return fig


def parse(file):
    """
    Parses a resources.jsonl file

    Parameters
    ----------
    file : str
        Resources.jsonl file to parse

    Returns
    -------
    header, data : tuple[dict, dict]
        TODO
    """
    def append(info):
        """
        Helper function to insert line information into the data dict per-PID

        Parameters
        ----------
        info : dict
            Info line
        """
        pid = info["pid"]
        if pid not in data:
            data[pid] = {}

        sub = data[pid]
        for k, v in info.items():
            if k in ("pid", "timestamp"):
                pass
            elif k == "children":
                for child in v:
                    append(child)
            elif isinstance(v, list):
                pass
            else:
                sub.setdefault(k, []).append(v)

        sub.setdefault('datetime', []).append(time)

    with open(file) as f:
        resources = [json.loads(l) for l in f.readlines()]

    descs = resources[0]
    header = resources[1]

    data = {}
    for line in resources[2:]:
        time = dtt.fromtimestamp(line["timestamp"])
        append(line)

    # Use a base datetime to convert the timedelta back to a datetime
    base = dtt.fromisocalendar(1, 1, 1)
    for pid, info in data.items():
        info["name"] = info["name"][0]

        t0 = info["datetime"][0]
        rs = info["relative_seconds"] = []
        rd = info["relative_datetime"] = []
        for dt in info["datetime"]:
            t = dt - t0
            rs.append(t.total_seconds())
            rd.append(base + t)

    # Make the main process a bit easier to find in the dict
    main = data[resources[2]["pid"]]
    data["main"] = main
    main["name"] = "Main Process"

    return descs, header, data


def plot(
    resources: str,
    output: str = None,
    memory: list[str] = ["app", "used"],
    memory_inline: bool = False,
    cpus: list[str] = ["all"],
    cpus_inline: bool = False,
    ignore: list[str] = ['bash', 'sixsV2.1'],
    ignore_append: list[str] = [],
    ignore_remove: list[str] = [],
    reduce_legend: bool = False,
    height: int = 200,
    log: str = None,
    sepFigs: bool = False,
    relative: bool = False,
):
    """
    Plots memory and CPU from a resources.jsonl file

    \b
    Parameters
    ----------
    resources : str
        Resources.jsonl file to parse
    output : str, default=None
        Saves the plots to a file. If the extension is .html, the file will retain
        plotly interactive features
    memory : list of {"app", "used", "avail", "all"}, default=["app", "used"]
        Creates a plot of aggregate memory statistics
    memory_inline : bool, default=False
        If True, adds the aggregate memory inline with the individual memory plot
        False will create it as an independent plot
    cpus : list of {"app", "sys", "all"}, default=["all"]
        Creates a plot of aggregate CPUs statistics
    cpus_inline : bool, default=False
        If True, adds the aggregate CPUs inline with the individual CPUs plot
        False will create it as an independent plot
    ignore : list[str], default=['bash', 'sixsV2.1']
        Ignore processes with these names. Setting this will overwrite the default
    ignore_append : list[str], default=None
        Appends keys to the default ignore list
    ignore_remove : list[str], default=None
        Removes keys from the default ignore list
    reduce_legend : bool, default=False
        Reduces the legend by grouping same-named processes together and gives them the
        same color
    height : int, default=200
        Height of each plot
    log : str, default=None
        Path to a log file to add vertical markers to the plots for significant ISOFIT
        events
    sepFigs : bool, default=False
        Return the list of separate figures instead of the multiplot figure. Useful
        when using this function as a basis to build upon
    relative : bool, default=False
        Uses the relative seconds time instead of the actual timestamps

    \b
    Returns
    -------
    go.Figure
        Multiplot figure containing each requested resource figure in a single column
    """
    Logger.debug(f"Parsing resources file: {resources}")
    descs, header, data = parse(resources)

    time = "datetime"
    if relative:
        time = "relative_datetime"

    # Update the ignore list
    ignore = set(ignore or [])
    ignore.update(ignore_append)
    ignore -= set(ignore_remove)

    # Get unique names if reduce_legend is set
    added = set()
    if reduce_legend:
        names = list(set([p["name"] for p in data.values()]))

    mem = go.Figure().update_layout(title=f"Memory ({header['mem_unit']})")
    cpu = go.Figure().update_layout(title=f"CPU %")

    Logger.info("Generating memory and CPU plots")
    for i, (proc, info) in enumerate(data.items()):
        # Skip the duplicated 'main' key
        if not isinstance(proc, int):
            continue

        # Skip non-important processes
        if (name := info["name"]) in ignore:
            continue

        # Same-named processes should have the same color
        idx = names.index(name) if reduce_legend else i
        color = {
            "legendgroup": idx,
            "line": {"color": plots.plotlyColor(idx)}
        }

        # When returning separate figures, the CPU plot's legend should match the memory's
        # When returning the multiplot, CPU shouldn't have a legend to avoid duplication
        cpuLegend = False
        memLegend = name not in added
        if sepFigs:
            cpuLegend = memLegend

        mem.add_trace(
            go.Scatter(name=info["name"], x=info[time], y=info["mem_total"], showlegend=memLegend, **color)
        )
        cpu.add_trace(
            go.Scatter(name=info["name"], x=info[time], y=info["cpu"], showlegend=cpuLegend, **color)
        )

        # Track that this process name was added to the legend, don't add again
        if reduce_legend:
            added.update([name])

    figs = [mem, cpu]

    main = data["main"]
    if memory:
        traces = []
        if "all" in memory or "app" in memory:
            Logger.debug("Creating app memory trace")
            traces.append(
                go.Scatter(name=f"App Memory Total", x=main[time], y=main["mem_app_total"])
            )
            traces.append(
                go.Scatter(name=f"App Memory Actual", x=main[time], y=main["mem_app_actual"])
            )
            traces.append(
                go.Scatter(name=f"App Memory Shared (Avg)", x=main[time], y=main["mem_app_shared_avg"])
            )
        if "all" in memory or "used" in memory:
            Logger.debug("Creating used memory trace")
            traces.append(
                go.Scatter(name=f"Sys Mem Used", x=main[time], y=main["mem_used"])
            )
        if "all" in memory or "avail" in memory:
            Logger.debug("Creating avail memory trace")
            traces.append(
                go.Scatter(name=f"Sys Mem Avail", x=main[time], y=main["mem_avail"])
            )

        if memory_inline:
            Logger.debug("Adding these traces inline with the memory plot")
            for trace in traces:
                mem.add_trace(trace)
        else:
            Logger.debug("Combining these into an independent figure")
            figs.append(
                go.Figure(data=traces).update_layout(title=f"Aggregate Memory")
            )

    if cpus:
        traces = []
        if "all" in cpus or "app" in cpus:
            Logger.debug("Creating app CPU trace")
            traces.append(
                go.Scatter(name=f"App Average CPU (cores={header['used_cores']})", x=main[time], y=main["cpu_avg"])

            )
        if "all" in cpus or "sys" in cpus:
            Logger.debug("Creating sys CPU trace")
            traces.append(
                go.Scatter(name=f"System Average CPU (cores={header['total_cores']})", x=main[time], y=main["sys_cpu"])
            )

        if cpus_inline:
            Logger.debug("Adding these traces inline with the CPU plot")
            for trace in traces:
                cpu.add_trace(trace)
        else:
            Logger.debug("Combining these into an independent figure")
            figs.append(
                go.Figure(data=traces).update_layout(title=f"Aggregate CPU")
            )

    if sepFigs:
        return figs

    Logger.info(f"Generating a multiplot with {len(figs)} subplots")
    fig = plots.multiplot(figs, sharey=False, dark=False, height=height)

    # if relative:
    fig.update_xaxes(
        tickformat = "%H:%M:%S"
    )

    if log:
        Logger.info("Adding log annotations")
        annotate(fig, log, relative=relative)

    if output:
        if output.endswith(".html"):
            Logger.info(f"Writing to HTML: {output}")
            fig.write_html(output)
        else:
            Logger.info(f"Writing image: {output}")
            fig.write_image(output)

    return fig


@click.command(name="template", no_args_is_help=True, help=plot.__doc__)
@click.argument("resources")
@click.option("-o", "--output")
@click.option("-m", "--memory", type=click.Choice(["app", "used", "avail", "all"]), default=("app", "used"), multiple=True)
@click.option("-mi", "--memory_inline", is_flag=True)
@click.option("-c", "--cpus", type=click.Choice(["app", "sys", "all"]), default=("all",), multiple=True)
@click.option("-ci", "--cpus_inline", is_flag=True)
@click.option("-i", "--ignore", multiple=True)
@click.option("-i+", "--ignore_append", multiple=True)
@click.option("-i-", "--ignore_remove", multiple=True)
@click.option("-el", "--expand_legend", is_flag=True, help="Inverse of reduce_legend")
@click.option("-h", "--height", type=int, default=200)
@click.option("-l", "--log")
@click.option("-r", "--relative", is_flag=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug, **kwargs):
    logging.basicConfig(
        level = "DEBUG" if debug else "INFO",
        format = "%(asctime)s | %(levelname)-5s | %(message)s",
    )

    kwargs["reduce_legend"] = not kwargs.pop("expand_legend")
    plot(**kwargs)


if __name__ == "__main__":
    cli()
