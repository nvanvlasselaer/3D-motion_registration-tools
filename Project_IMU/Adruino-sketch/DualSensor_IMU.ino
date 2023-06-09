#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
 
#define BNO055_SAMPLERATE_DELAY_MS (10)
 
// The two BNO055 modules, bnoB has the ADR pin wired to 3.3v to change its i2c address
// Both are wired: SCL to analog 5, SDA to analog 4, VIN to 5v, GRN to ground
Adafruit_BNO055 bnoA = Adafruit_BNO055(-1, BNO055_ADDRESS_A);
Adafruit_BNO055 bnoB = Adafruit_BNO055(-1, BNO055_ADDRESS_B);

void setup() {
Serial.begin(115200);
if(!bnoA.begin()) {
Serial.print("Ooops, BNO055(A) not detected");
while(1);
}
bnoA.setExtCrystalUse(true);
if(!bnoB.begin()) {
Serial.print("Ooops, BNO055(B) not detected");
while(1);
}
bnoB.setExtCrystalUse(true);
}

void loop() {
  uint8_t systemA, gyroA, accelA, mgA = 0;
  bnoA.getCalibration(&systemA, &gyroA, &accelA, &mgA);

  uint8_t systemB, gyroB, accelB, mgB = 0;
  bnoB.getCalibration(&systemB, &gyroB, &accelB, &mgB);

  imu::Quaternion quatA = bnoA.getQuat();
  imu::Quaternion quatB = bnoB.getQuat();

  Serial.print("{\"key\": \"/sensor/1\", \"value\": [");
  Serial.print(quatA.w());
  Serial.print(", ");
  Serial.print(quatA.x());
  Serial.print(", ");
  Serial.print(quatA.y());
  Serial.print(", ");
  Serial.print(quatA.z());
  Serial.print("], ");
  Serial.print("\"calibration\": {");
  Serial.print("\"system\": ");
  Serial.print(systemA);
  Serial.print(", \"gyro\": ");
  Serial.print(gyroA);
  Serial.print(", \"accel\": ");
  Serial.print(accelA);
  Serial.print(", \"mag\": ");
  Serial.print(mgA);
  Serial.print("}}\n");

  Serial.print("{\"key\": \"/sensor/2\", \"value\": [");
  Serial.print(quatB.w());
  Serial.print(", ");
  Serial.print(quatB.x());
  Serial.print(", ");
  Serial.print(quatB.y());
  Serial.print(", ");
  Serial.print(quatB.z());
  Serial.print("], ");
  Serial.print("\"calibration\": {");
  Serial.print("\"system\": ");
  Serial.print(systemB);
  Serial.print(", \"gyro\": ");
  Serial.print(gyroB);
  Serial.print(", \"accel\": ");
  Serial.print(accelB);
  Serial.print(", \"mag\": ");
  Serial.print(mgB);
  Serial.print("}}\n");

  delay(BNO055_SAMPLERATE_DELAY_MS);
}