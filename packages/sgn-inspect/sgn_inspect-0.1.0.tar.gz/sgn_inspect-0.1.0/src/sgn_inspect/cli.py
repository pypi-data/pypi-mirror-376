# Copyright (C) 2025 Patrick Godwin
#
# This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# <https://mozilla.org/MPL/2.0/>.
#
# SPDX-License-Identifier: MPL-2.0

import sys
from collections import defaultdict
from importlib import metadata
from typing import Annotated

from rich.console import Console
from rich.table import Table
from typer import Argument, Exit, Typer

from .registry import ElementInfo, discover_elements

if sys.version_info < (3, 11):
    import importlib_metadata as metadata
else:
    from importlib import metadata


app = Typer(help="Show information about SGN elements and plugins")
console = Console()


@app.command()
def show(
    name: Annotated[
        str | None,
        Argument(
            metavar="[ELEMENT | PLUGIN]",
            help="If specified, an element or plugin name. Otherwise list all elements",
        ),
    ] = None,
) -> None:
    """Show available SGN elements or information about a plugin or element."""
    elements = discover_elements()
    if name:
        elements_by_plugin: dict[str, dict[str, ElementInfo]] = defaultdict(dict)
        for info in elements.values():
            elements_by_plugin[info.plugin][info.name] = info
        if name in elements_by_plugin:
            # display per-plugin information
            plugin_elements = elements_by_plugin[name]
            _display_plugin_info(plugin_elements)
        elif name in elements:
            # display element information
            info = elements[name]
            _display_element_info(info)
        else:
            console.print("no such element or plugin")
            Exit(code=1)
    else:
        _display_all_element_info(elements)


def _display_all_element_info(elements: dict[str, ElementInfo]) -> None:
    """Display information for all available elements."""
    table = Table("Element", "Plugin", "Type", "Module", "Description")
    for info in sorted(elements.values()):
        table.add_row(
            info.name,
            info.plugin,
            str(info.kind),
            info.module,
            info.short_description,
        )
    console.print(table)


def _display_element_info(info: ElementInfo) -> None:
    """Display information for a single element."""
    table = Table(show_header=False)
    table.add_row("Element", info.name)
    table.add_row("Plugin", info.plugin)
    table.add_row("Type", str(info.kind))
    table.add_row("Module", info.module)
    console.print(table)

    console.print()
    console.print(info.description)


def _display_plugin_info(elements: dict[str, ElementInfo]) -> None:
    """Display information for a single plugin."""
    element = next(iter(elements.values()))
    library = element.module.split(".")[0]
    pkg = metadata.packages_distributions()[library]
    pkg_info = metadata.metadata(pkg[0])
    project_url = pkg_info["Project-URL"].splitlines()[0].split(" ")[1]
    try:
        license_ = pkg_info["License"]
    except KeyError:
        license_ = pkg_info.get("License-Expression", "")

    table = Table(show_header=False)
    table.add_row("Plugin", element.plugin)
    table.add_row("Description", pkg_info["Summary"])
    table.add_row("Version", pkg_info["Version"])
    table.add_row("License", license_)
    table.add_row("Project URL", project_url)
    console.print(table)

    table = Table("Element", "Type", "Module", "Description", title="Plugin Elements")
    for info in sorted(elements.values()):
        table.add_row(info.name, str(info.kind), info.module, info.short_description)
    console.print(table)
