#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exposed Thing subclass that logs all interactions to InfluxDB if enabled.
"""

from wotpy2.wot.dictionaries.interaction import PropertyFragmentDict, ActionFragmentDict, EventFragmentDict
from wotpy2.wot.enums import TDChangeMethod, TDChangeType
from wotpy2.wot.events import (
    PropertyChangeEventInit,
    PropertyChangeEmittedEvent,
    ActionInvocationEventInit,
    ActionInvocationEmittedEvent,
    ThingDescriptionChangeEventInit,
)
from wotpy2.wot.exposed.thing import ExposedThing
from wotpy2.wot.td import ThingDescription


class InfluxExposedThing(ExposedThing):
    """ExposedThing subclass that logs all interactions to InfluxDB if enabled."""

    async def read_property(self, name):
        value = await super().read_property(name)
        if self._servient._influxdb_enabled:
            self._servient._influxdb.write_point(name, value)
        return value


    async def write_property(self, name, value):
        await super().write_property(name, value)
        if self._servient._influxdb_enabled:
            self._servient._influxdb.write_point(name, value)


    def _emit_property_change_event(self, name, value):
        super()._emit_property_change_event(name, value)
        if self._servient._influxdb_enabled:
            event_init = PropertyChangeEventInit(name=name, value=value)
            emitted_event = PropertyChangeEmittedEvent(init=event_init)
            self._servient._influxdb.write_point("event", str(emitted_event))


    async def invoke_action(self, name, input_value=None):
        result = await super().invoke_action(name, input_value)
        if self._servient._influxdb_enabled:
            event_init = ActionInvocationEventInit(action_name=name, return_value=result)
            emitted_event = ActionInvocationEmittedEvent(init=event_init)
            self._servient._influxdb.write_point("action", str(emitted_event))
        return result


    def emit_event(self, event_name, payload):
        super().emit_event(event_name, payload)
        if self._servient._influxdb_enabled:
            self._servient._influxdb.write_point("event", str(payload))


    def add_property(self, name, property_init, value=None):
        super().add_property(name, property_init, value)
        if self._servient._influxdb_enabled:
            event_data = ThingDescriptionChangeEventInit(
                td_change_type=TDChangeType.PROPERTY,
                method=TDChangeMethod.ADD,
                name=name,
                data=property_init.to_dict() if isinstance(property_init, PropertyFragmentDict) else property_init,
                description=ThingDescription.from_thing(self.thing).to_dict()
            )
            self._servient._influxdb.write_point("event", str(event_data))


    def remove_property(self, name):
        super().remove_property(name)
        if self._servient._influxdb_enabled:
            event_data = ThingDescriptionChangeEventInit(
                td_change_type=TDChangeType.PROPERTY,
                method=TDChangeMethod.REMOVE,
                name=name)
            self._servient._influxdb.write_point("event", str(event_data))


    def add_action(self, name, action_init, action_handler=None):
        super().add_action(name, action_init, action_handler)
        if self._servient._influxdb_enabled:
            event_data = ThingDescriptionChangeEventInit(
                td_change_type=TDChangeType.ACTION,
                method=TDChangeMethod.ADD,
                name=name,
                data=action_init.to_dict() if isinstance(action_init, ActionFragmentDict) else action_init,
                description=ThingDescription.from_thing(self.thing).to_dict()
            )
            self._servient._influxdb.write_point("event", str(event_data))


    def remove_action(self, name):
        super().remove_action(name)
        if self._servient._influxdb_enabled:
            event_data = ThingDescriptionChangeEventInit(
                td_change_type=TDChangeType.ACTION,
                method=TDChangeMethod.REMOVE,
                name=name)
            self._servient._influxdb.write_point("event", str(event_data))


    def add_event(self, name, event_init):
        super().add_event(name, event_init)
        if self._servient._influxdb_enabled:
            event_data = ThingDescriptionChangeEventInit(
                td_change_type=TDChangeType.EVENT,
                method=TDChangeMethod.ADD,
                name=name,
                data=event_init.to_dict() if isinstance(event_init, EventFragmentDict) else event_init,
                description=ThingDescription.from_thing(self.thing).to_dict()
            )
            self._servient._influxdb.write_point("event", str(event_data))


    def remove_event(self, name):
        super().remove_event(name)
        if self._servient._influxdb_enabled:
            event_data = ThingDescriptionChangeEventInit(
                td_change_type=TDChangeType.EVENT,
                method=TDChangeMethod.REMOVE,
                name=name)
            self._servient._influxdb.write_point("event", str(event_data))
