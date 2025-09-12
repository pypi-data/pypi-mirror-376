#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the RTSP server.
"""

from wotpy2.utils.enums import EnumListMixin


class RTSPSchemes(EnumListMixin):
    """Enumeration of RTSP schemes."""

    RTSP = "rtsp"
