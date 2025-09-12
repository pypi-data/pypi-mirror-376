#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the Zenoh protocol.
"""

import asyncio
import copy
import json
import logging
import pprint
import time
import uuid
from urllib import parse

import reactivex
import zenoh

from wotpy2.protocols.client import BaseProtocolClient
from wotpy2.protocols.enums import InteractionVerbs, Protocols
from wotpy2.protocols.exceptions import (ClientRequestTimeout,
                                        FormNotFoundException)
from wotpy2.protocols.zenoh.enums import ZenohSchemes
from wotpy2.protocols.zenoh.handlers.action import ActionZenohHandler
from wotpy2.protocols.zenoh.handlers.property import PropertyZenohHandler
from wotpy2.protocols.zenoh.utils import build_zenoh_config
from wotpy2.protocols.utils import is_scheme_form
from wotpy2.utils.utils import handle_observer_finalization
from wotpy2.wot.events import (EmittedEvent, PropertyChangeEmittedEvent,
                              PropertyChangeEventInit)


class ZenohClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the Zenoh protocol."""

    DELIVER_TERMINATE_LOOP_SLEEP_SECS = 0.1
    SLEEP_SECS_DELIVER_ERR = 1.0

    DEFAULT_DELIVER_TIMEOUT_SECS = 1
    DEFAULT_MSG_WAIT_TIMEOUT_SECS = 5
    DEFAULT_MSG_TTL_SECS = 15
    DEFAULT_STOP_LOOP_TIMEOUT_SECS = 60

    def __init__(self,
                 deliver_timeout_secs=DEFAULT_DELIVER_TIMEOUT_SECS,
                 msg_wait_timeout_secs=DEFAULT_MSG_WAIT_TIMEOUT_SECS,
                 msg_ttl_secs=DEFAULT_MSG_TTL_SECS,
                 timeout_default=None,
                 stop_loop_timeout_secs=DEFAULT_STOP_LOOP_TIMEOUT_SECS):
        self._deliver_timeout_secs = deliver_timeout_secs
        self._msg_wait_timeout_secs = msg_wait_timeout_secs
        self._msg_ttl_secs = msg_ttl_secs
        self._timeout_default = timeout_default
        self._stop_loop_timeout_secs = stop_loop_timeout_secs
        self._deliver_stop_events = {}
        self._msg_conditions = {}
        self._session = {}
        self._subscribers = {}
        self._messages = {}
        self._topics = {}
        self._logr = logging.getLogger(__name__)

    async def _init_client(self, router_url):
        """Initializes and connects a client to the given router URL."""

        if router_url in self._session:
            return

        config = build_zenoh_config(router_url)

        self._logr.debug("Connecting Zenoh client to {} with config: {}".format(
            router_url, pprint.pformat(config)))

        self._session[router_url] = zenoh.open(config)

    async def _new_message(self, router_url, msg, topic):
        """Adds the message to the internal queue and notifies all topic listeners."""

        assert router_url in self._msg_conditions, "Unknown router in conditions"
        assert topic in self._msg_conditions[router_url], "Unknown topic"

        if router_url not in self._messages:
            self._messages[router_url] = {}

        if topic not in self._messages[router_url]:
            self._messages[router_url][topic] = []

        self._messages[router_url][topic].append({
            "id": uuid.uuid4().hex,
            "data": json.loads(msg),
            "time": time.time()
        })

        async with self._msg_conditions[router_url][topic]:
            self._msg_conditions[router_url][topic].notify_all()

        self._clean_messages(router_url)

    async def _deliver(self, router_url, msg, topic):
        """Loop that receives the messages from the router."""

        assert router_url in self._session

        try:
            await self._new_message(router_url, msg, topic)
        except Exception as ex:
            self._logr.warning(
                "Error processing message: {}".format(ex),
                exc_info=True)

    async def _stop_deliver_loop(self, router_url, topic):
        """Asks the message delivery loop to stop gracefully."""

        try:
            self._subscribers[router_url][topic].undeclare()
        except KeyError:
            pass

    async def _disconnect_client(self, router_url, topic):
        """Cleans all resources."""

        try:
            self._logr.debug(
                "Stopping message delivery loop: {}".format(router_url))
            await self._stop_deliver_loop(router_url, topic)
        except Exception as ex:
            self._logr.warning(
                "Error stopping deliver loop: {}".format(ex),
                exc_info=True)

        self._subscribers[router_url].pop(topic, None)
        if self._subscribers[router_url]:
            return

        try:
            self._logr.debug(
                "Disconnecting Zenoh client: {}".format(router_url))
            self._session[router_url].close()
        except Exception as ex:
            self._logr.warning(
                "Error disconnecting: {}".format(ex),
                exc_info=True)

        self._session.pop(router_url, None)
        self._subscribers.pop(router_url, None)
        self._messages.pop(router_url, None)
        self._msg_conditions.pop(router_url, None)
        self._topics.pop(router_url, None)

    async def _subscribe(self, router_url, topic):
        """Subscribes to a topic."""

        loop = asyncio.get_running_loop()

        # Zenoh callbacks run on a different thread. Using asyncio.run() would
        # create a different loop that creates overhead
        def listener(sample):
            msg = sample.payload.to_string()
            topic = str(sample.key_expr)
            coro = self._deliver(router_url, msg, topic)
            asyncio.run_coroutine_threadsafe(coro, loop)

        if router_url not in self._session:
            return

        if router_url not in self._msg_conditions:
            self._msg_conditions[router_url] = {}

        if topic not in self._msg_conditions[router_url]:
            self._msg_conditions[router_url][topic] = \
                asyncio.Condition()

        if router_url not in self._topics:
            self._topics[router_url] = set()

        self._topics[router_url].add((topic))

        if router_url not in self._subscribers:
            self._subscribers[router_url] = {}
        self._subscribers[router_url][topic] = self._session[router_url].declare_subscriber(topic, listener)

    async def _publish(self, router_url, topic, payload):
        """Publishes a message with the given payload in a topic."""

        if router_url not in self._session:
            return

        self._session[router_url].put(topic, payload)

    def _topic_messages(self, router_url, topic, from_time=None, ignore_ids=None):
        """Returns a generator that yields the messages in the
        delivered messages queue for the given topic."""

        if router_url not in self._messages:
            return

        if topic not in self._messages[router_url]:
            return

        for msg in self._messages[router_url][topic]:
            is_on_time = from_time is None or msg["time"] >= from_time
            is_ignored = ignore_ids is not None and msg["id"] in ignore_ids

            if is_on_time and not is_ignored:
                yield msg["id"], msg["data"], msg["time"]

    def _clean_messages(self, router_url):
        """Removes the messages that have expired according to the TTL."""

        if router_url not in self._messages:
            return

        now = time.time()

        self._messages[router_url] = {
            topic: [
                msg for msg in self._messages[router_url][topic]
                if (now - msg["time"]) < self._msg_ttl_secs
            ] for topic in self._messages[router_url]
        }

    def _next_match(self, router_url, topic, func):
        """Returns the first message match in the internal messages queue or None."""

        return next((item for item in self._topic_messages(router_url, topic) if func(item)), None)

    async def _wait_condition(self, condition):
        """Acquires the lock of the condition and waits on it."""

        async with condition:
            await condition.wait()

    async def _wait_on_message(self, router_url, topic):
        """Waits for the arrival of a message in the given topic."""

        assert router_url in self._msg_conditions, "Unknown router URL"
        assert topic in self._msg_conditions[router_url], "Unknown topic"

        try:
            await asyncio.wait_for(
                self._wait_condition(
                    self._msg_conditions[router_url][topic]),
                    timeout=self._msg_wait_timeout_secs)
        except asyncio.TimeoutError:
            pass

    @classmethod
    def _pick_zenoh_href(cls, td, forms, op=None):
        """Picks the most appropriate Zenoh form href from the given list of forms."""

        def is_op_form(form):
            try:
                return op is None or op == form.op or op in form.op
            except TypeError:
                return False

        return next((
            form.href for form in forms
            if is_scheme_form(form, td.base, ZenohSchemes.ZENOH) and is_op_form(form)
        ), None)

    @classmethod
    def _parse_href(cls, href):
        """Take an Zenoh form href and returns
        the Zenoh router URL and the topic separately."""

        modified_href = href.replace("tcp/", "")
        parsed_href = parse.urlparse(modified_href)

        assert parsed_href.scheme and parsed_href.netloc and parsed_href.path

        return {
            "router_url": "tcp/{}".format(parsed_href.netloc),
            "topic": parsed_href.path.lstrip("/").rstrip("/")
        }

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.ZENOH

    def is_supported_interaction(self, td, name):
        """Returns True if the any of the Forms for the Interaction
        with the given name is supported in this Protocol Binding client."""

        forms = td.get_forms(name)

        forms_zenoh = [
            form for form in forms
            if is_scheme_form(form, td.base, ZenohSchemes.list())
        ]

        return len(forms_zenoh) > 0

    async def invoke_action(self, td, name, input_value, timeout=None):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        timeout = timeout if timeout else self._timeout_default

        href = self._pick_zenoh_href(td, td.get_action_forms(name))

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)
        router_url = parsed_href["router_url"]

        topic_invoke = parsed_href["topic"]
        topic_result = ActionZenohHandler.to_result_topic(topic_invoke)

        try:
            await self._init_client(router_url)
            await self._subscribe(router_url, topic_result)

            input_data = {
                "id": uuid.uuid4().hex,
                "input": input_value
            }

            input_payload = json.dumps(input_data).encode()

            await self._publish(router_url, topic_invoke, input_payload)

            ini = time.time()

            while True:
                self._logr.debug(
                    "Checking invocation topic: {}".format(topic_result))

                if timeout and (time.time() - ini) > timeout:
                    self._logr.warning(
                        "Timeout invoking Action: {}".format(topic_result))
                    raise ClientRequestTimeout

                msg_match = self._next_match(
                    router_url, topic_result,
                    lambda item: item[1].get("id") == input_data.get("id"))

                if not msg_match:
                    await self._wait_on_message(router_url, topic_result)
                    continue

                msg_id, msg_data, msg_time = msg_match

                if msg_data.get("error", None) is not None:
                    raise Exception(msg_data.get("error"))
                else:
                    return msg_data.get("result")
        finally:
            await self._disconnect_client(router_url, topic_result)

    async def write_property(self, td, name, value, timeout=None, wait_ack=True):
        """Updates the value of a Property on a remote Thing.
        Due to the Zenoh binding design this coroutine yields as soon as the write message has
        been published and will not wait for a custom write handler that yields to another coroutine
        Returns a Future."""

        timeout = timeout if timeout else self._timeout_default

        href_write = self._pick_zenoh_href(
            td, td.get_property_forms(name),
            op=InteractionVerbs.WRITE_PROPERTY)

        if href_write is None:
            raise FormNotFoundException()

        parsed_href_write = self._parse_href(href_write)
        router_url = parsed_href_write["router_url"]

        topic_write = parsed_href_write["topic"]
        topic_ack = PropertyZenohHandler.to_write_ack_topic(topic_write)

        try:
            await self._init_client(router_url)
            await self._subscribe(router_url, topic_ack)

            write_data = {
                "action": "write",
                "value": value,
                "ack": uuid.uuid4().hex
            }

            write_payload = json.dumps(write_data).encode()

            await self._publish(router_url, topic_write, write_payload)

            if not wait_ack:
                return

            ini = time.time()

            while True:
                self._logr.debug(
                    "Checking write ACK topic: {}".format(topic_ack))

                if timeout and (time.time() - ini) > timeout:
                    self._logr.warning(
                        "Timeout writing Property: {}".format(topic_ack))
                    raise ClientRequestTimeout

                msg_match = self._next_match(
                    router_url, topic_ack,
                    lambda item: item[1].get("ack") == write_data.get("ack"))

                if msg_match:
                    break

                await self._wait_on_message(router_url, topic_ack)
        finally:
            await self._disconnect_client(router_url, topic_ack)

    async def read_property(self, td, name, timeout=None):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        timeout = timeout if timeout else self._timeout_default

        forms = td.get_property_forms(name)

        href_read = self._pick_zenoh_href(
            td, forms,
            op=InteractionVerbs.READ_PROPERTY)

        href_obsv = self._pick_zenoh_href(
            td, forms,
            op=InteractionVerbs.OBSERVE_PROPERTY)

        if href_read is None or href_obsv is None:
            raise FormNotFoundException()

        parsed_href_read = self._parse_href(href_read)
        parsed_href_obsv = self._parse_href(href_obsv)

        topic_read = parsed_href_read["topic"]
        topic_obsv = parsed_href_obsv["topic"]

        router_read = parsed_href_read["router_url"]
        router_obsv = parsed_href_obsv["router_url"]

        try:
            await self._init_client(router_read)
            router_obsv != router_read and (await self._init_client(router_obsv))

            await self._subscribe(router_obsv, topic_obsv)

            read_time = time.time()
            read_payload = json.dumps({"action": "read"}).encode()

            await self._publish(router_read, topic_read, read_payload)

            ini = time.time()

            while True:
                self._logr.debug(
                    "Checking property update topic: {}".format(topic_obsv))

                if timeout and (time.time() - ini) > timeout:
                    self._logr.warning(
                        "Timeout reading Property: {}".format(topic_obsv))
                    raise ClientRequestTimeout

                msg_match = self._next_match(
                    router_obsv, topic_obsv,
                    lambda item: item[2] >= read_time)

                if not msg_match:
                    await self._wait_on_message(router_obsv, topic_obsv)
                    continue

                msg_id, msg_data, msg_time = msg_match

                return msg_data.get("value")
        finally:
            await self._disconnect_client(router_read, topic_read)
            await self._disconnect_client(router_obsv, topic_obsv)

    def _build_subscribe(self, router_url, topic, next_item_builder):
        """Builds the subscribe function that should be passed when
        constructing an Observable to listen for messages on an Zenoh topic."""

        def subscribe(observer, scheduler):
            """Subscriber function that listens for Zenoh messages
            on a given topic and passes them to the Observer."""

            state = {}

            async def deliver_message(sample, observer):
                msg_data = json.loads(sample.payload.to_string())
                try:
                    next_item = next_item_builder(msg_data)
                    observer.on_next(next_item)
                except Exception as ex:
                    self._logr.warning(
                        "Subscription message error: {}".format(ex), exc_info=True)

            @handle_observer_finalization(observer)
            async def callback():
                loop = asyncio.get_running_loop()

                def listener(sample):
                    coro = deliver_message(sample, observer)
                    asyncio.run_coroutine_threadsafe(coro, loop)

                config = build_zenoh_config(router_url)
                state["session"] = zenoh.open(config)

                self._logr.debug("Subscribing on <{}> to {} with config: {}".format(
                    router_url, topic, config))
                state["subscriber"] = state["session"].declare_subscriber(topic, listener)

                # Infinite loop that sleeps to keep the Zenoh subscription alive
                while True:
                    await asyncio.sleep(5000)

            def unsubscribe():
                """Disconnects from the Zenoh router and stops the message delivering loop."""

                async def disconnect():
                    try:
                        state["subscriber"].undeclare()
                        state["session"].close()
                    except Exception as ex:
                        self._logr.warning(
                            "Subscription disconnection error: {}".format(ex))

                asyncio.create_task(disconnect())

            asyncio.create_task(callback())

            return unsubscribe

        return subscribe

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        forms = td.get_property_forms(name)

        href = self._pick_zenoh_href(
            td, forms,
            op=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        router_url = parsed_href["router_url"]
        topic = parsed_href["topic"]

        def next_item_builder(msg_data):
            msg_value = msg_data.get("value")
            init = PropertyChangeEventInit(name=name, value=msg_value)
            return PropertyChangeEmittedEvent(init=init)

        subscribe = self._build_subscribe(
            router_url=router_url,
            topic=topic,
            next_item_builder=next_item_builder)

        # noinspection PyUnresolvedReferences
        return reactivex.create(subscribe)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        forms = td.get_event_forms(name)

        href = self._pick_zenoh_href(
            td, forms,
            op=InteractionVerbs.SUBSCRIBE_EVENT)

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        router_url = parsed_href["router_url"]
        topic = parsed_href["topic"]

        def next_item_builder(msg_data):
            return EmittedEvent(init=msg_data.get("data"), name=name)

        subscribe = self._build_subscribe(
            router_url=router_url,
            topic=topic,
            next_item_builder=next_item_builder)

        # noinspection PyUnresolvedReferences
        return reactivex.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
