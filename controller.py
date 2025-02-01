import time
from enum import auto, StrEnum
from multiprocessing import Event, Queue, Pipe, Process
from multiprocessing.connection import Connection
from queue import Empty, Full
from threading import Thread, Lock
from typing import Any, NamedTuple

from deviceconfigs import DeviceConfig, DEVICE_CONFIGS, toggle_state, get_initial_device_configs, enable_device, disable_device
from scd41 import get_scd41_device


class Payload(NamedTuple):
    fn_id: str
    args: Any
    kwargs: Any


class Message(NamedTuple):
    sender: Connection
    payload: Payload


class DeviceController:
    def __init__(self, message_q):
        self.message_q = message_q
    
    def _send(self, payload):
        receiver, sender = Pipe(duplex=False)
        try:
            self.message_q.put(Message(sender, payload), timeout=0.1)
        except Full:
            return None
        return receiver.recv()

    def get_device_configs(self):
        return self._send(Payload(fn_id="get_device_configs", args=(), kwargs={}))
    
    def toggle_on_off(self, device_id: str):
        return self._send(Payload(fn_id="toggle_on_off", args=(), kwargs={"device_id": device_id}))


# def is_humidity_low(humidity_sensor, threshold: float):
#     return humidity_sensor.relative_humidity < threshold

# def trigger_low_humidity(event_q, humidity_sensor):
import time
from functools import partial


# def trigger(trigger_is_active_fn, send_event, stop_event):
#     next_check_time = time.time()
#     while not stop_event.is_set():
#         if time.time() > next_check_time:
#             if trigger_is_active_fn() is True:
#                 send_event()
#             next_check_time = time.time() + 5


def wait_for_data_ready(humidity_sensor):
    while not humidity_sensor.data_ready:
        pass

def low_humidity(humidity_sensor, threshold: float) -> bool:
    ret = False
    wait_for_data_ready(humidity_sensor)
    if humidity_sensor.data_ready:
        humidity = humidity_sensor.relative_humidity
        is_low = humidity < threshold
        print("\nlow humidity check\nmeasurement: %f\nthreshold: %f\nhumidity_is_low: %s" % (humidity, threshold, is_low))
        ret = is_low
    return ret


def high_humidity(humidity_sensor, threshold: float) -> bool:
    ret = False
    wait_for_data_ready(humidity_sensor)
    humidity = humidity_sensor.relative_humidity
    is_high = humidity > threshold
    print("\nhigh humidity check\nmeasurement: %f\nthreshold: %f\nhumidity_is_high: %s" % (humidity, threshold, is_high))
    ret = is_high
    return ret


def send_enable_device_event(device_id: str, event_q):
    def _send_event():
        receiver, sender = Pipe(duplex=False)
        payload = Payload(fn_id="enable_device", args=(), kwargs={"device_id": device_id})
        message = Message(sender, payload)
        print("Sending message %s" % str(message))
        event_q.put(message)
        # return receiver.recv()
    return _send_event


def send_disable_device_event(device_id: str, event_q):
    def _send_event():
        receiver, sender = Pipe(duplex=False)
        payload = Payload(fn_id="disable_device", args=(), kwargs={"device_id": device_id})
        message = Message(sender, payload)
        print("Sending message %s" % str(message))
        event_q.put(message)
    return _send_event


def trigger(trigger_is_active_fn, events: list, shutdown_event):
    next_time_to_check = time.time()
    while not shutdown_event.is_set():
        if time.time() > next_time_to_check:
            if trigger_is_active_fn() is True:
                for event in events:
                    event()
            next_time_to_check = time.time() + 5


def setup_triggers(event_bus):
    print("connecting to scd41 sensor")
    smart_sensors = {
        "scd41": get_scd41_device()
    }

    def check_trigger(trigger_id, trigger_fn, on_trigger_events: dict):
        if trigger_fn() == True:
            print("Trigger detected %s, %s" % (trigger_id, trigger_fn.func.__name__))
            for event_name, event in on_trigger_events.items():
                print("Publishing event %s" % event_name)
                event()
    
    triggers = {}

    # setup trigger and events for low humidity conditions
    is_humidity_low = partial(low_humidity, smart_sensors["scd41"], threshold=90)
    on_humidity_low_events = {
        "enable_fogger": send_enable_device_event("FOGGER", event_bus),  # consider adding the trigger_id to the send enable/disable, so that it can be included in the message
        "enable_fogger_fan": send_enable_device_event("FOGGER_FAN", event_bus),
        # "send_text_notification": 'x',
    }
    triggers.update({
        "humidity_is_low_trigger": partial(check_trigger, "low_humidity_trigger", is_humidity_low, on_humidity_low_events)
    })

    # setup trigger and events for high humidity conditions
    is_humidity_high = partial(high_humidity, smart_sensors["scd41"], threshold=98)
    on_humidity_high_events = {
        "disable_fogger": send_disable_device_event("FOGGER", event_bus),
        "disable_fogger_fan": send_disable_device_event("FOGGER_FAN", event_bus),
    }
    triggers.update({
        "humidity_is_high_trigger": partial(check_trigger, "high_humidity_trigger", is_humidity_high, on_humidity_high_events)
    })

    return triggers


def shutdown_triggers(triggers: dict):
    pass


def trigger_watch(triggers: dict, shutdown_event):
    time_to_check = time.time()

    while not shutdown_event.is_set():
        if time.time() > time_to_check:
            for trigger_id, check_trigger_fn in triggers.items():
                print("\n==================== Checking trigger %s ====================" % trigger_id)
                check_trigger_fn()
            
            time_to_check = time.time() + 5

    shutdown_triggers(triggers)


class TriggerState(StrEnum):
    TRIGGER_ACTIVE = auto()
    TRIGGER_IDLE = auto()
    TRIGGER_PENDING = auto()


class DeviceManager:

    def __init__(self):
        self.message_q = Queue()
        self.stop_event = Event()
        self._message_listener_handle = Process(target=self._message_listener, args=())
        self._triggers = setup_triggers(self.message_q)
        self._trigger_watch = Thread(target=trigger_watch, args=(self._triggers, self.stop_event))
    
    def start(self):
        self._message_listener_handle.start()
        self._trigger_watch.start()
    
    def get_controller(self):
        return DeviceController(self.message_q)

    def _message_listener(self):
        deviceconfigs = get_initial_device_configs()
        print("Initial device configs: %s" % deviceconfigs)

        def dequeue_message() -> Message:
            message = None
            try:
                message = self.message_q.get_nowait()
            except Empty:
                pass
            return message
        
        while not self.stop_event.is_set():
            if message := dequeue_message():
                fn_id = message.payload.fn_id
                kwargs = message.payload.kwargs

                if fn_id == "toggle_on_off":
                    
                    device_id = kwargs["device_id"]
                    print("incoming device config %s" % deviceconfigs[device_id])
                    updated_config: DeviceConfig = toggle_state(deviceconfigs.get(device_id))
                    
                    deviceconfigs.update({device_id: updated_config})
                    message.sender.send(deviceconfigs[device_id])
                    print("outgoing config %s" % deviceconfigs[device_id])
                
                elif fn_id == "get_device_configs":
                    message.sender.send(deviceconfigs.copy())
                
                elif fn_id == "enable_device":
                    device_id = kwargs["device_id"]
                    updated_config = enable_device(deviceconfigs.get(device_id))
                    deviceconfigs.update({device_id: updated_config})
                
                elif fn_id == "disable_device":
                    device_id = kwargs["device_id"]
                    updated_config = disable_device(deviceconfigs.get(device_id))
                    deviceconfigs.update({device_id: updated_config})



        # scd4x = get_scd41_device()

        # self._triggers = {
        #     "low_humidity_trigger": 
        #     Thread(
        #         target=trigger, 
        #         kwargs={
        #             "trigger_is_active_fn": partial(low_humidity, humidity_sensor=scd4x, threshold=25, lock=self.scd_lock),
        #             "events": [
        #                 send_enable_device_event("FOGGER", self.message_q),
        #                 send_enable_device_event("FOGGER_FAN", self.message_q),
        #             ],
        #             "shutdown_event": self.stop_event,
        #         }
        #     ),
        #     "high_humidity_trigger": 
        #     Thread(
        #         target=trigger, 
        #         kwargs={
        #             "trigger_is_active_fn": partial(high_humidity, humidity_sensor=scd4x, threshold=28, lock=self.scd_lock),
        #             "events": [
        #                 send_disable_device_event("FOGGER", self.message_q),
        #                 send_disable_device_event("FOGGER_FAN", self.message_q),
        #             ],
        #             "shutdown_event": self.stop_event,
        #         }
        #     ),
        # }

        # for trigger_id, trigger_thread in self._triggers.items():
        #     print("Starting trigger thread %s" % trigger_id)
        #     trigger_thread.start()