#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP Protocol Binding implementation.

.. autosummary::
    :toctree: _coap

    resources
    authenticator
    client
    credential
    enums
    server
"""

from wotpy2.support import is_coap_supported

if is_coap_supported() is False:
    raise NotImplementedError("CoAP binding is not supported in this platform")
