# Copyright (C) 2025 Patrick Godwin
#
# This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# <https://mozilla.org/MPL/2.0/>.
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import inspect
import re
import sys
import typing
from dataclasses import dataclass
from enum import IntEnum, auto
from functools import cached_property, total_ordering
from typing import Callable

from sgn.base import Element, SinkElement, SourceElement, TransformElement
from typing_extensions import Self

if sys.version_info < (3, 11):
    from importlib_metadata import EntryPoint, entry_points
else:
    from importlib.metadata import EntryPoint, entry_points


class ElementType(IntEnum):
    """Used to inform a particular element's type, i.e. source."""

    SOURCE = auto()
    "a source element"

    TRANSFORM = auto()
    "a transform element"

    SINK = auto()
    "a sink element"

    INVALID = auto()
    "not an element"

    def __str__(self) -> str:
        return self.name.lower()

    @typing.no_type_check
    @classmethod
    def from_element(
        cls, element: type[Element] | Callable[..., Element]
    ) -> ElementType:
        """Determine an element's type from an element class.

        Parameters
        ----------
        element : type[Element] | Callable[..., Element]
            The element class or class method constructor associated with an
            element class.

        Returns
        -------
        ElementType
            The element's type.

        """
        if inspect.ismethod(element):
            element = element.__self__
        if issubclass(element, SourceElement):
            return ElementType.SOURCE
        if issubclass(element, TransformElement):
            return ElementType.TRANSFORM
        if issubclass(element, SinkElement):
            return ElementType.SINK
        msg = f"{element} is not an element"
        raise TypeError(msg)


@dataclass
@total_ordering
class ElementInfo:
    """Useful information associated with an element.

    Parameters
    ----------
    name : str
        The element's name (class).
    extra : str
        The extra package this element can be found in. The empty string
        represents no extra, or a base element.
    module : str
        The module the element can be found in, represented as a string.
    kind : ElementType
        The type of element, i.e. source element.
    element : Element | None
        If the element is not broken, a reference to this element's class.
    description : str | None
        If the element is not broken, the documentation associated with this
        element.
    """

    name: str
    module: str
    kind: ElementType
    element: Element | None = None
    description: str | None = None

    @property
    def broken(self) -> bool:
        """Whether this element is broken."""
        return self.kind is ElementType.INVALID

    @cached_property
    def plugin(self) -> str:
        """The plugin associated with this element.

        This is tied to the library, where base sgn elements by default are
        associated with the base plugin.
        """
        library = self.module.split(".")[0]
        plugin = re.sub(r"[-_]", "", library).removeprefix("sgn")
        return plugin if plugin else "base"

    @cached_property
    def short_description(self) -> str | None:
        """A one line description associated with this element, if not broken."""
        if not self.description:
            return None
        return self.description.splitlines()[0]

    @classmethod
    def from_entrypoint(cls, entrypoint: EntryPoint) -> Self:
        """Create an ElementInfo from a package entry point.

        Parameters
        ----------
        entrypoint : EntryPoint
            The package entry point associated with an element.

        Returns
        -------
        ElementInfo
            The element information.

        """
        module = entrypoint.module
        try:
            element = entrypoint.load()
            kind = ElementType.from_element(element)
        except Exception:
            element = None
            kind = ElementType.INVALID
            description = None
        else:
            description = element.__doc__
        return cls(entrypoint.name, module, kind, element, description)

    def _ordering(self) -> tuple[str, int, str]:
        plugin_order = "" if self.plugin == "base" else self.plugin
        return (plugin_order, self.kind.value, self.name)

    def __eq__(self, other) -> bool:
        return self._ordering() == other._ordering()

    def __gt__(self, other) -> bool:
        return self._ordering() > other._ordering()


def discover_elements() -> dict[str, ElementInfo]:
    """Discover all elements registered via entry points.

    Note that non-base elements are only discoverable after installing the
    corresponding extra package associated with a plugin.

    Returns
    -------
    dict[str, ElementInfo]
        A mapping between element names and their information.

    """
    elements: dict[str, ElementInfo] = {}
    entrypoints = entry_points(group="sgn_elements")
    for name in entrypoints.names:
        elements[name] = ElementInfo.from_entrypoint(entrypoints[name])
    return elements
