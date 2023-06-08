import time
import json
import logging
from RPLCD.i2c import CharLCD
from gpiozero import OutputDevice
from w1thermsensor import W1ThermSensor
from datetime import datetime, timedelta
from azure.iot.device import IoTHubDeviceClient


class AzureIoTConnect:
    """ Handles connection and message sending through Azure IoT Hub"""

    def __init__(self, config_file):
        """
        Initialize Azure IoT connection.
        :param config_file: Path to configuration file with connection string.
        """
        self.connection_string = self.load_connection_string(config_file)
        self.client = self.initialize_client()

    def load_connection_string(self, config_file):
        """
        Loads the connection string from the configuration file.
        :param config_file: Path to configuration file with connection string.
        :return: Connection string.
        """
        try:
            with open(config_file, "r") as file:
                config = json.load(file)
                return config["IoTHubConnectionString"]
        except FileNotFoundError as e:
            logging.error("Configuration file not found")
            raise e
        except KeyError as e:
            logging.error("ConnectionString not found in the configuration file")
            raise e

    def initialize_client(self):
        """
        Initializes the Azure IoT client.
        :return: Azure IoT client.
        """
        try:
            client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)
            return client
        except Exception as e:
            logging.error("Failed to initialize Azure IoT client")
            raise e

    def send_message(self, message):
        """
        Sends message to Azure IoT Hub.
        :param message: Message to be sent.
        """
        try:
            self.client.send_message(json.dumps(message))
        except Exception as e:
            logging.error("Failed to send message to Azure IoT Hub")
            raise e

    @property
    def is_connected(self):
        """
        :return: Connection status to Azure IoT Hub.
        """
        return self.client.connected


class WineMacerator:
    """ Handles the process of wine maceration """

    LCD_I2C_ADDRESS = 0x27
    RELAY_DURATION_MINUTES = 2
    MIXTURE_INTERVAL_HOURS = 6
    TEMP_UPDATE_INTERVAL_MINUTES = 15
    MACERATION_DURATION_DAYS = 14

    def __init__(self, config_file_path):
        """
        Initializes wine macerator with given config file.
        :param config_file_path: Path to configuration file for Azure IoT.
        """
        self.azure_iot = AzureIoTConnect(config_file_path)
        self.initialize_components()
        self.set_initial_times()

    def initialize_components(self):
        self.lcd = CharLCD(i2c_expander='PCF8574', address=self.LCD_I2C_ADDRESS, port=1, cols=16, rows=2, dotsize=8)
        self.sensor = W1ThermSensor()
        self.relay = OutputDevice(26, active_high=False)

    def set_initial_times(self):
        self.relay_end_time = None
        self.next_temp_update = datetime.now()
        self.next_relay_activation = datetime.now()
        self.next_second_update = datetime.now()
        self.end_maceration_time = datetime.now() + timedelta(days=self.MACERATION_DURATION_DAYS)

    def update_temperature(self):
        self.set_next_temp_update_time()
        temperature = self.get_temperature_from_sensor()
        self.display_info_on_lcd(temperature)
        self.azure_iot.send_message({"wine_temp": temperature})

    def set_next_temp_update_time(self):
        self.next_temp_update = datetime.now() + timedelta(minutes=self.TEMP_UPDATE_INTERVAL_MINUTES)

    def get_temperature_from_sensor(self):
        return self.sensor.get_temperature()

    def display_info_on_lcd(self, temperature):
        remaining_days = (self.end_maceration_time - datetime.now()).days
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(f'T:{temperature:.1f} D:{remaining_days}'.ljust(11))
        self.display_azure_connection_status()

    def display_azure_connection_status(self):
        self.lcd.cursor_pos = (0, 12)
        self.lcd.write_string("OK-A" if self.azure_iot.is_connected else "NO-A")

    def activate_relay(self):
        self.relay.on()
        self.set_relay_end_time()
        self.display_blending_started_on_lcd()

    def set_relay_end_time(self):
        self.relay_end_time = datetime.now() + timedelta(minutes=self.RELAY_DURATION_MINUTES)

    def display_blending_started_on_lcd(self):
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string('Mieszanie: --:--'.ljust(16))

    def deactivate_relay(self):
        self.relay.off()
        self.set_next_relay_activation_time()

    def set_next_relay_activation_time(self):
        self.next_relay_activation = datetime.now() + timedelta(hours=self.MIXTURE_INTERVAL_HOURS)

    def update_relay_timer(self):
        self.lcd.cursor_pos = (1, 0)
        remaining = (self.relay_end_time if self.relay.value else self.next_relay_activation) - datetime.now()
        self.display_time_on_lcd(remaining, self.relay.value)

    def display_time_on_lcd(self, remaining, relay_active):
        if relay_active:
            self.lcd.write_string(f'Blend: {int(remaining.total_seconds() / 60)}:{int(remaining.total_seconds() % 60):02d}'.ljust(16))
        else:
            self.lcd.write_string(f'Next: {int(remaining.total_seconds() / 3600)}:{int(remaining.total_seconds() % 3600 / 60):02d}:{int(remaining.total_seconds() % 60):02d}'.ljust(16))

    def run(self):
        self.display_azure_connection_status()
        while datetime.now() < self.end_maceration_time:
            current_time = datetime.now()

            if current_time >= self.next_temp_update:
                self.update_temperature()

            if self.relay.value == 1 and current_time >= self.relay_end_time:
                self.deactivate_relay()
            elif self.relay.value == 0 and current_time >= self.next_relay_activation:
                self.activate_relay()

            if current_time >= self.next_second_update:
                self.update_relay_timer()
                self.next_second_update = current_time + timedelta(seconds=1)

            next_event_time = min(self.next_temp_update, self.next_second_update, self.relay_end_time if self.relay.value else self.next_relay_activation)
            time.sleep(max(0, (next_event_time - current_time).total_seconds()))

        self.lcd.clear()
        self.lcd.write_string("Zakonczono proces")


if __name__ == "__main__":
    # Configure logger to not store logs locally.
    logging.basicConfig(stream=logging.NullHandler())

    try:
        config_file_path = "config.json"
        macerator = WineMacerator(config_file_path)
        macerator.run()
    except Exception as e:
        error_message = f"An error occurred: {e}"
        # Log error message to Azure IoT Hub.
        AzureIoTConnect(config_file_path).send_message({"error": error_message})
