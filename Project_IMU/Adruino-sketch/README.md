# BNO055 Sensor Data Readme

This folder contains an Arduino sketch that reads data from two BNO055 sensors and sends the sensor readings and calibration information over the serial port.

## Dependencies

The following libraries are required for running the code:

- [Wire](https://www.arduino.cc/en/Reference/Wire): This library provides I2C communication functions.
- [Adafruit_Sensor](https://github.com/adafruit/Adafruit_Sensor): A base class for sensor libraries that provides common functions.
- [Adafruit_BNO055](https://github.com/adafruit/Adafruit_BNO055): A library for the BNO055 sensor, providing functions for accessing sensor data and performing sensor fusion calculations.
- [imumaths](https://github.com/adafruit/Adafruit_BNO055): A utility library for performing sensor fusion calculations.

## Hardware Setup

To use this code, you need the following hardware components:

- Arduino board (e.g., Arduino Uno)
- Two BNO055 sensors (Adafruit 9-DOF Absolute Orientation IMU Fusion Breakout - BNO055)
- Jumper wires

Wire the hardware as follows:

- Connect the SCL pin of the BNO055 sensors to analog pin 5 on the Arduino board.
- Connect the SDA pin of the BNO055 sensors to analog pin 4 on the Arduino board. 
- Connect the VIN pin of the BNO055 sensors to the 5V power supply of the Arduino board.
- Connect the GRN pin of the BNO055 sensors to the ground of the Arduino board.

If you want to change the I2C address of one of the sensors, you can wire the ADR pin to 3.3V. Otherwise, the default I2C addresses will be used.

## Installation and Usage

1. Connect the Arduino board to your computer.
2. Open the Arduino IDE or compatible development environment.
3. Install the required libraries (Wire, Adafruit_Sensor, Adafruit_BNO055, imumaths) if you haven't already.
4. Open the `BNO055_SensorData.ino` sketch from this repository in the Arduino IDE.
5. Verify and upload the sketch to your Arduino board.
6. Open the serial monitor in the Arduino IDE or a serial terminal application.
7. Set the baud rate of the serial monitor or application to 115200.
8. You should start seeing the sensor data and calibration information printed in JSON format in the serial monitor.

## Customization

- If you have changed the I2C address of one of the sensors, modify the constructor arguments for `bnoA` and `bnoB` in the sketch accordingly.
- If you have connected an external crystal oscillator, remove the `bnoA.setExtCrystalUse(true);` and `bnoB.setExtCrystalUse(true);` lines.

## Contributing

Contributions to this project are welcome. If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This code is licensed under the [MIT License](LICENSE).