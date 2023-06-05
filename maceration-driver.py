import time
from datetime import datetime, timedelta

from RPLCD.i2c import CharLCD
from gpiozero import OutputDevice
from w1thermsensor import W1ThermSensor


class WineMacerator:
    """A class to manage a wine macerator using a temperature sensor, an LCD display and a relay."""
    
    LCD_ADDR = 0x27
    RELAY_DURATION_MIN = 1
    MIXTURE_INTERVAL_HR = 0.25
    TEMP_UPDATE_INTERVAL_MIN = 1

    def __init__(self):
        """Initializes the macerator components and sets the initial times."""
        self.initialize_components()
        self.set_initial_times()


    def initialize_components(self):
        """Initializes the LCD, the temperature sensor and the relay."""
        self.lcd = CharLCD(i2c_expander='PCF8574', address=self.LCD_ADDR, port=1, cols=16, rows=2, dotsize=8)
        self.sensor = W1ThermSensor()
        self.relay = OutputDevice(26, active_high=False)


    def set_initial_times(self):
        """Sets the initial times for the next temperature update, the next relay activation, and the next second update."""
        self.relay_end_time = None
        self.next_temp_update = datetime.now()
        self.next_relay_activation = datetime.now()
        self.next_second_update = datetime.now()


    def update_temperature(self):
        """Updates the temperature displayed on the LCD."""
        self.set_next_temp_update_time()
        temperature = self.get_temperature_from_sensor()
        self.display_temperature_on_lcd(temperature)


    def set_next_temp_update_time(self):
        """Sets the next temperature update time."""
        self.next_temp_update = datetime.now() + timedelta(minutes=self.TEMP_UPDATE_INTERVAL_MIN)


    def get_temperature_from_sensor(self):
        """Returns the temperature read from the sensor."""
        return self.sensor.get_temperature()


    def display_temperature_on_lcd(self, temperature):
        """Displays the given temperature on the LCD."""
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(f'Wine T: {temperature:.1f} C'.ljust(16))


    def activate_relay(self):
        """Activates the relay and updates the LCD to show that blending has started."""
        self.relay.on()
        self.set_relay_end_time()
        self.display_blending_started_on_lcd()


    def set_relay_end_time(self):
        """Sets the relay end time."""
        self.relay_end_time = datetime.now() + timedelta(minutes=self.RELAY_DURATION_MIN)


    def display_blending_started_on_lcd(self):
        """Displays on the LCD that blending has started."""
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string('Mieszanie: --:--'.ljust(16))


    def deactivate_relay(self):
        """Deactivates the relay."""
        self.relay.off()
        self.set_next_relay_activation_time()


    def set_next_relay_activation_time(self):
        """Sets the next relay activation time."""
        self.next_relay_activation = datetime.now() + timedelta(hours=self.MIXTURE_INTERVAL_HR)


    def update_relay_timer(self):
        """Updates the relay timer displayed on the LCD."""
        self.lcd.cursor_pos = (1, 0)
        remaining = (self.relay_end_time if self.relay.value else self.next_relay_activation) - datetime.now()
        self.display_time_on_lcd(remaining, self.relay.value)


    def display_time_on_lcd(self, remaining, relay_active):
        """Displays the given remaining time on the LCD, depending on whether the relay is active or not."""
        if relay_active:
            self.lcd.write_string(f'Mieszanie: {int(remaining.total_seconds() / 60)}:{int(remaining.total_seconds() % 60):02d}'.ljust(16))
        else:
            self.lcd.write_string(f'Nast.za: {int(remaining.total_seconds() / 3600)}:{int(remaining.total_seconds() % 3600 / 60):02d}:{int(remaining.total_seconds() % 60):02d}'.ljust(16))


    def run(self):
        """Runs the macerator, periodically updating the temperature, activating and deactivating the relay, and updating the relay timer."""
        while True:
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


if __name__ == "__main__":
    macerator = WineMacerator()
    macerator.run()
    