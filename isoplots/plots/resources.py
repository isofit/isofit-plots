import json
from datetime import datetime as dtt

import click
import plotly.graph_objects as go

from isoplots.isonice.utils import plots


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

        sub.setdefault('timestamp', []).append(time)

    with open(file) as f:
        resources = [json.loads(l) for l in f.readlines()]

    header = resources[0]
    data = {}
    for line in resources[1:]:
        time = dtt.fromtimestamp(line["timestamp"])
        append(line)

    for pid, info in data.items():
        info["name"] = info["name"][0]

    main = data[resources[1]["pid"]]
    data["main"] = main
    main["name"] = "Main Process"

    return header, data


def plot(
    resources: str,
    output: str = None,
    memory: list[str] = ["all"],
    memory_inline: bool = False,
    cpus: list[str] = ["all"],
    cpus_inline: bool = False,
    ignore: list[str] = ['bash', 'sixsV2.1'],
    ignore_append: list[str] = [],
    ignore_remove: list[str] = [],
    reduce_legend: list[str] = [],
    height = 200,
):
    """
    Plots memory and CPU from a resources.jsonl file

    Parameters
    ----------
    resources : str
        Resources.jsonl file to parse
    output : str, default=None
        Saves the plots to a file. If the extension is .html, the file will retain
        plotly interactive features
    memory : list of {"app", "used", "avail", "all"}, default=["all"]
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
    reduce_legend : bool, default=True
        Reduces the legend by grouping same-named processes together and gives them the
        same color
    height : into, default=300
        Height of each plot

    Returns
    -------
    go.Figure
        Multiplot figure containing each requested resource figure in a single column
    """
    header, data = parse(resources)

    # Update the ignore list
    ignore = set(ignore or [])
    ignore.update(ignore_append)
    ignore -= set(ignore_remove)

    # Get unique names if reduce_legend is set
    added = []
    if reduce_legend:
        names = list(set([p["name"] for p in data.values()]))

    mem = go.Figure().update_layout(title=f"Memory ({header['mem_unit']})")
    cpu = go.Figure().update_layout(title=f"CPU %")

    for i, (proc, info) in enumerate(data.items()):
        # Skip the duplicated 'main' key
        if not isinstance(proc, int):
            continue

        # Skip non-important processes
        if (name := info["name"]) in ignore:
            continue

        idx = names.index(name) if reduce_legend else i
        color = {
            "legendgroup": idx,
            "line": {"color": plots.plotlyColor(idx)}
        }

        mem.add_trace(
            go.Scatter(name=info["name"], x=info["timestamp"], y=info["mem"], showlegend=name not in added, **color)
        )
        cpu.add_trace(
            go.Scatter(name=info["name"], x=info["timestamp"], y=info["cpu"], showlegend=False, **color)
        )

        if reduce_legend:
            added.append(name)

    figs = [mem, cpu]

    main = data["main"]
    if memory:
        traces = []
        if "all" in memory or "app" in memory:
            traces.append(
                go.Scatter(name=f"App Memory", x=main["timestamp"], y=main["mem_app"])
            )
        if "all" in memory or "used" in memory:
            traces.append(
                go.Scatter(name=f"Sys Mem Used", x=main["timestamp"], y=main["mem_used"])
            )
        if "all" in memory or "avail" in memory:
            traces.append(
                go.Scatter(name=f"Sys Mem Avail", x=main["timestamp"], y=main["mem_avail"])
            )

        if memory_inline:
            for trace in traces:
                mem.add_trace(trace)
        else:
            figs.append(
                go.Figure(data=traces).update_layout(title=f"Aggregate Memory")
            )

    if cpus:
        traces = []
        if "all" in cpus or "app" in cpus:
            traces.append(
                go.Scatter(name=f"App Average CPU (cores={header['used_cores']})", x=main["timestamp"], y=main["cpu_avg"])

            )
        if "all" in cpus or "sys" in cpus:
            traces.append(
                go.Scatter(name=f"System Average CPU (cores={header['total_cores']})", x=main["timestamp"], y=main["sys_cpu"])
            )

        if cpus_inline:
            for trace in traces:
                cpu.add_trace(trace)
        else:
            figs.append(
                go.Figure(data=traces).update_layout(title=f"Aggregate CPU")
            )

    fig = plots.multiplot(figs, sharey=False, dark=False, height=height)
    if output:
        if output.endswith(".html"):
            print(f"Writing to HTML: {output}")
            fig.write_html(output)
        else:
            print(f"Writing image: {output}")
            fig.write_image(output)

    return fig


@click.command(name="template", no_args_is_help=True, help=plot.__doc__)
@click.argument("resources")
@click.option("-o", "--output")
@click.option("-m", "--memory", type=click.Choice(["app", "used", "avail", "all"]), default=("all",), multiple=True)
@click.option("-mi", "--memory_inline", is_flag=True)
@click.option("-c", "--cpus", type=click.Choice(["app", "sys", "all"]), default=("all",), multiple=True)
@click.option("-ci", "--cpus_inline", is_flag=True)
@click.option("-i", "--ignore", multiple=True)
@click.option("-i+", "--ignore_append", multiple=True)
@click.option("-i-", "--ignore_remove", multiple=True)
@click.option("-r", "--reduce_legend", is_flag=True)
@click.option("-h", "--height", type=int, default=300)
def cli(**kwargs):
    plot(**kwargs)


if __name__ == "__main__":
    cli()
