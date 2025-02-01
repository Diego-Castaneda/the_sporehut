from typing import NamedTuple, TypedDict
import relayctrl

class DeviceConfig(TypedDict):
    name: str
    onoff_state: str
    gpio_pin: int


DEVICE_CONFIGS = {
    "FOGGER_FAN": DeviceConfig(name="Fogger Fan", onoff_state="off", gpio_pin=relayctrl.RELAY_IN4_GPIO_PIN),
    "FOGGER": DeviceConfig(name="Fogger", onoff_state="off", gpio_pin=relayctrl.RELAY_IN1_GPIO_PIN),
}


def get_initial_device_configs():
    return DEVICE_CONFIGS.copy()


def enable_device(device: DeviceConfig) -> DeviceConfig:
    updated_config = DeviceConfig(**device)
    relayctrl.enable_relay(device["gpio_pin"])
    updated_config["onoff_state"] = "on"
    return updated_config


def disable_device(device: DeviceConfig) -> DeviceConfig:
    updated_config = DeviceConfig(**device)
    relayctrl.disable_relay(device["gpio_pin"])
    updated_config["onoff_state"] = "off"
    return updated_config


def toggle_state(device: DeviceConfig) -> DeviceConfig:
    print("toggling state for device %s" % device)

    updated_device_config = DeviceConfig(**device)
    if device["onoff_state"] == "off":
        relayctrl.enable_relay(device["gpio_pin"])
        updated_device_config["onoff_state"] = "on"
    else:
        relayctrl.disable_relay(device["gpio_pin"])
        updated_device_config["onoff_state"] = "off"
    
    return updated_device_config