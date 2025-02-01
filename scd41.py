"""
Prerequisites for Raspberry Pi

Enable I2C port: https://pi3g.com/enabling-and-checking-i2c-on-the-raspberry-pi-using-the-command-line-for-your-own-scripts/
- sudo raspi-config nonint get_i2c: 1 indicates port is disabled, 0 indicates port is enabled
- sudo raspi-config nonint do_i2c 0: enables the I2C port
- verify /dev/i2c-1 & /dev/i2c-2 exist. adafruit_extended_bus uses these buses

https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#control-drive-strength
"""
import time
import board
import adafruit_scd4x
from adafruit_extended_bus import ExtendedI2C as I2C
import smbus

import pandas as pd
from pathlib import Path


ROOT_DIR_PATH = Path(__file__).parent
DATA_DIR_PATH = ROOT_DIR_PATH / "data"


def get_scd41_device():
    details = {}
    i2c = I2C(1)
    scd4x = adafruit_scd4x.SCD4X(i2c)
    scd4x.start_periodic_measurement()
    return scd4x


if __name__ == "__main__":
    # i2c = board.I2C()
    i2c = I2C(1)
    scd4x = adafruit_scd4x.SCD4X(i2c)
    print("Serial number:", [hex(i) for i in scd4x.serial_number])

    scd4x.start_periodic_measurement()
    print("Waiting for first measurement....")

    data = pd.DataFrame(columns=["co2(ppm)", "temperature(C)", "humidity(%)"])
    data_filepath = DATA_DIR_PATH / f"scd41_data_{(time.strftime('%Y-%m-%dT%H%M%S'))}.csv"
    data.to_csv(data_filepath, index=False)

    while True:
        if scd4x.data_ready:
            co2_concentration = float(scd4x.CO2)
            temperature = float(scd4x.temperature)
            relative_humidity = float(scd4x.relative_humidity)
            print("CO2: %d ppm" % co2_concentration)
            print("Temperature: %0.1f *C" % temperature)
            print("Humidity: %0.1f %%" % relative_humidity)
            print()

            df = pd.DataFrame({
                "co2(ppm)": [co2_concentration],
                "temperature(C)": [temperature],
                "humidity(%)": [relative_humidity]
            })
            df.to_csv(data_filepath, header=None, index=False, mode="a")
            
        time.sleep(1)