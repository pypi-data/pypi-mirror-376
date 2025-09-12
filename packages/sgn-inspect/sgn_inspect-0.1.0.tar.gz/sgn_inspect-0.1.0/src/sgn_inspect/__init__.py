# Copyright (C) 2025 Patrick Godwin
#
# This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# <https://mozilla.org/MPL/2.0/>.
#
# SPDX-License-Identifier: MPL-2.0


try:
    from ._version import version as __version__
except ModuleNotFoundError:
    import setuptools_scm

    __version__ = setuptools_scm.get_version(fallback_version="?.?.?")
