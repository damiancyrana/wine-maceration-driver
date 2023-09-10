from machine import Pin, I2C, Timer, RTC
import oled_sh1106 as sh1106
import ds18b20
import onewire
import utime

# Constants
RELAY_DURATION_MINUTES = 2
MIXTURE_INTERVAL_HOURS = 1
TEMP_UPDATE_INTERVAL_MINUTES = 1
MACERATION_DURATION_DAYS = 1

# Initializing Display
i2c_display = I2C(1, scl=Pin(3), sda=Pin(2), freq=100000)
display = sh1106.SH1106_I2C(128, 64, i2c_display, None, addr=0x3c)
display.rotate(True)
display.fill(0)
display.text('Wine Maceration', 10, 10, 1)
display.text('Driver', 40, 30, 1)
display.text('Damian Cyrana', 15, 50, 1)
display.show()
utime.sleep_ms(100)  # Add a delay after initializing the display

# Initializing RTC
i2c = I2C(1)
rtc = RTC()
year, month, day, _, hours, minutes, seconds, _ = rtc.datetime()

# Initializing GPIO pins
temperature_sensor_power_pin = Pin(17, Pin.OUT)
temperature_sensor_power_pin.low()  # Turn off by default
relay_pin = Pin(18, Pin.OUT)  
relay_pin.low()  # Turn off by default

# Initializing temperature sensor
ow = onewire.OneWire(Pin(16))
temp_sensor = ds18b20.DS18X20(ow)

# Global variables
relay_active = False
current_temperature = "Waiting for temp"
relay_next_activation = MIXTURE_INTERVAL_HOURS * 3600  # in seconds


def display_error(message):
    """Displays error messages on the OLED screen."""
    display.fill(0)
    display.text(message, 0, 30, 1)
    display.show()


def format_seconds_to_hms(seconds):
    """Converts seconds to a formatted hour:minute:second string."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def activate_relay():
    """Activates the relay."""
    global relay_active, relay_next_activation
    relay_pin.high()
    relay_active = True
    relay_next_activation = RELAY_DURATION_MINUTES * 60


def deactivate_relay():
    """Deactivates the relay."""
    global relay_active, relay_next_activation
    relay_pin.low()
    relay_active = False
    relay_next_activation = MIXTURE_INTERVAL_HOURS * 3600


def increment_time():
    """Increments the time values."""
    global hours, minutes, seconds
    seconds += 1
    if seconds >= 60:
        seconds = 0
        minutes += 1
        if minutes >= 60:
            minutes = 0
            hours += 1
            if hours >= 24:
                hours = 0


def update_display():
    """Updates the OLED screen with the current status."""
    global relay_next_activation
    
    increment_time()
    relay_next_activation -= 1
    if relay_next_activation <= 0:
        if relay_active:
            deactivate_relay()
        else:
            activate_relay()

    current_time = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
    display.fill(0)
    display.text(current_temperature, 0, 0, 1)
    
    if relay_active:
        display.text(f'Mixing:', 0, 24, 1)
        display.text(f'{format_seconds_to_hms(relay_next_activation)}', 65, 24, 1)
    else:
        display.text(f'Next:', 0, 24, 1)
        display.text(f'{format_seconds_to_hms(relay_next_activation)}', 46, 24, 1)
        
    display.text(current_time, 65, 50, 1)
    display.text(f'Day:{MACERATION_DURATION_DAYS}', 0, 50, 1)
    display.show()


def measure_temperature():
    """Measures the temperature using the DS18B20 sensor."""
    global current_temperature
    temperature_sensor_power_pin.high()
    utime.sleep_ms(100)
    roms = temp_sensor.scan()
    if roms:
        try:
            temp_sensor.convert_temp()
            utime.sleep_ms(750)
            temp = temp_sensor.read_temp(roms[0])
            current_temperature = 'Wine T = {:.1f} C'.format(temp)
        except Exception:
            display_error("Sensor Error")
            current_temperature = 'Sensor Error'
    else:
        current_temperature = 'No sensor'
    temperature_sensor_power_pin.low()


def set_rtc_date_time(year, month, day, hour, minute, second):
    """Sets the date and time for the RTC."""
    rtc.datetime((year, month, day, 0, hour, minute, second, 0))


days_elapsed = 0

if __name__ == "__main__":
    # Uncomment the below line only when you need to set the RTC date and time
    # set_rtc_date_time(2023, 9, 10, 09, 08, 0)
    
    display_timer = Timer(-1)
    display_timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: update_display())
    temp_measure_timer = Timer(-1)
    temp_measure_timer.init(period=TEMP_UPDATE_INTERVAL_MINUTES * 60 * 1000, mode=Timer.PERIODIC, callback=lambda t: measure_temperature())
    
    while True:
        if days_elapsed > MACERATION_DURATION_DAYS:
            display.fill(0)
            display.text('Maceration', 10, 10, 1)
            display.text('Completed!', 10, 30, 1)
            display.show()
            break
        utime.sleep(1)
        
        _, _, current_day, _, _, _, _, _ = rtc.datetime()
        if current_day != day:
            day = current_day
            days_elapsed += 1

