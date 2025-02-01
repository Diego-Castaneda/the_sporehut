import time

import relayctrl

LAMP = relayctrl.RELAY_IN4_GPIO_PIN


if __name__ == "__main__":
    print("Enabling lamp")
    relayctrl.enable_relay(LAMP)
    time.sleep(1)
    print("Disabling lamp")
    relayctrl.disable_relay(LAMP)
    time.sleep(1)
    print("Enabling lamp")
    relayctrl.enable_relay(LAMP)
    time.sleep(1)
    print("Disabling lamp")
    relayctrl.disable_relay(LAMP)
