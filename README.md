# Wine Macerator with Azure IoT Integration 🍷🤖

Wine Macerator is a Python project that utilizes various hardware components to automate the wine maceration process. The program controls an LCD display, a temperature sensor, and a relay for mixing. It also integrates with Azure IoT Hub for remote data logging.

![Wine Macerator Illustration](https://github.com/damiancyrana/wine-maceration-driver/blob/main/maceration-device.jpg?raw=true)

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Hardware Setup](#hardware-setup)
- [Configuration](#configuration)
- [Running the Program](#running-the-program)
- [Contribution](#contribution)
- [License](#license)

## Features

- 🌡️ Monitors temperature using a 1-wire temperature sensor.
- 🔄 Controls a relay for automated mixing during maceration.
- 📟 Displays status information on an LCD display.
- ☁️ Sends temperature data to Azure IoT Hub for remote monitoring.
- 🛑 Gracefully ends the process after a predefined maceration period.

## Prerequisites

- Raspberry Pi with Raspbian installed.
- Python 3.7+.
- Azure IoT Hub account and configuration.
- Hardware components:
    - 1-wire Temperature Sensor (e.g., DS18B20).
    - Relay Module.
    - I2C LCD Display.
    - Jumper wires and a breadboard.

## Installation

1. Clone this repository to your Raspberry Pi.

    ```sh
    git clone https://github.com/yourusername/wine-macerator.git
    cd wine-macerator
    ```

2. Install the required Python libraries.

    ```sh
    pip install RPLCD gpiozero w1thermsensor azure-iot-device
    ```

## Hardware Setup

Connect the hardware components as follows:

- **Temperature Sensor**: Connect the VCC pin to 3.3V, the GND pin to ground, and the DATA pin to GPIO4.
- **Relay Module**: Connect the VCC pin to 5V, the GND pin to ground, and the IN pin to GPIO26.
- **LCD Display**: Connect the VCC pin to 5V, the GND pin to ground, SDA to SDA, and SCL to SCL.

Refer to the datasheets for each component for detailed instructions.

## Configuration

1. Create a configuration file named `config.json` in the project directory with the following content:

    ```json
    {
        "IoTHubConnectionString": "Your_Azure_IoT_Hub_Connection_String"
    }
    ```

2. Replace `Your_Azure_IoT_Hub_Connection_String` with your Azure IoT Hub connection string.

## Running the Program

1. Run the program using Python.

    ```sh
    python maceration-driver.py
    ```

2. The LCD display will show the temperature, days remaining for maceration, and Azure IoT connection status.
3. The program will automatically stop after the predefined maceration period.


## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.
