#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT Protocol Binding implementation.

.. autosummary::
    :toctree: _mqtt

    handlers
    client
    enums
    runner
    server
"""

from wotpy2.support import is_mqtt_supported

if is_mqtt_supported() is False:
    raise NotImplementedError("MQTT binding is not supported in this platform")
