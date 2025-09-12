# ultrasonic_lcd_telemetrix_Barmaja.py
# -----------------------------------------------------------
# Example: HC-SR04 Ultrasonic Distance Sensor + 16x2 I2C LCD
# using telemetrix_lite wrapper
#
# ----------------- WIRING -----------------
# HC-SR04:
#   - VCC  -> 5V
#   - GND  -> GND
#   - TRIG -> Arduino D7
#   - ECHO -> Arduino D6
#
# LCD with I2C backpack (PCF8574, typical address 0x27 or 0x3F):
#   - GND  -> GND
#   - VCC  -> 5V
#   - SDA  -> A4  (Uno/Nano)
#   - SCL  -> A5  (Uno/Nano)
#
# ----------------- SOFTWARE -----------------
# 1. Make sure your Arduino is flashed with Telemetrix4Arduino.ino
# 2. Install Python libraries:
#       pip install telemetrix telemetrix-lite pyserial
# 3. Run this script:
#       python ultrasonic_lcd_telemetrix_lite.py
#
# ----------------- TROUBLESHOOTING -----------------
# - If LCD shows nothing → try addr=0x3F instead of 0x27
# - If text is garbled → power-cycle Arduino + LCD, check 5V power
# - If distance always None → check TRIG/ECHO wiring, target must be 2–400 cm
# - If port error → close Arduino IDE Serial Monitor (it locks the COM port)
#
# -----------------------------------------------------------

import time
from telemetrix_Barmaja import TelemetrixSync

TRIG, ECHO = 7, 6        # pins for ultrasonic sensor
LCD_ADDR = 0x27          # change to 0x3F if needed

t = TelemetrixSync()              # auto-detect Arduino
t.sonar_config(TRIG, ECHO)        # configure ultrasonic pins
t.i2c_init(addr=LCD_ADDR)         # initialize I2C LCD
t.lcd_print(0, 0, "Distance (cm)") # print header on first line

try:
    while True:
        dist_cm = t.sonar_read(TRIG)  # get distance in cm (or None)
        if dist_cm is not None:
            # clear second line before writing new value
            t.lcd_print(1, 0, " " * 16)
            t.lcd_print(1, 0, f"{dist_cm:5.1f}")
            print("cm:", dist_cm)  # also print in console for debugging
        time.sleep(0.3)
except KeyboardInterrupt:
    t.shutdown()
