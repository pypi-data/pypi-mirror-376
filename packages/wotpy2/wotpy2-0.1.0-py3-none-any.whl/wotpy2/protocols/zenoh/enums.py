#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the Zenoh protocol binding.
"""

from wotpy2.utils.enums import EnumListMixin


class ZenohSchemes(EnumListMixin):
    """Enumeration of Zenoh schemes."""

    ZENOH = "zenoh"
