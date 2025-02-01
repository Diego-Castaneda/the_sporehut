import RPi.GPIO as GPIO

print("loading `relayctrl`")

GPIO.setmode(GPIO.BCM)

RELAY_IN1_GPIO_PIN = 17
RELAY_IN2_GPIO_PIN = None
RELAY_IN3_GPIO_PIN = None
RELAY_IN4_GPIO_PIN = 27

GPIO.setup(RELAY_IN4_GPIO_PIN, GPIO.OUT)
GPIO.output(RELAY_IN4_GPIO_PIN, GPIO.HIGH)

GPIO.setup(RELAY_IN1_GPIO_PIN, GPIO.OUT)
GPIO.output(RELAY_IN1_GPIO_PIN, GPIO.HIGH)


def enable_relay(rpi_gpio_pin: int):
    GPIO.output(rpi_gpio_pin, GPIO.LOW)


def disable_relay(rpi_gpio_pin: int):
    GPIO.output(rpi_gpio_pin, GPIO.HIGH)
