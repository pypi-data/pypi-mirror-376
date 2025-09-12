# light_sensor_led_on_off.py
# -----------------------------------------------------------
# LDR Light Sensor (A0) -> LED ON/OFF (D3) using telemetrix_lite
#
# Wiring:
#   - LDR voltage divider:
#       LDR one leg -> 5V
#       10k resistor -> GND
#       Junction LDR/10k -> A0
#   - LED: D3 -> 220Ω -> LED -> GND
#
# Notes:
#   - Adjust THRESHOLD based on your classroom light.
#   - With this divider: brighter room -> LOWER A0 reading (LDR R ↓),
#     darker room -> HIGHER A0 reading.
# -----------------------------------------------------------

import time
from telemetrix_Barmaja import TelemetrixSync

A0 = 0          # Analog channel A0
LED = 3         # PWM-capable pin for future fade upgrades
THRESHOLD = 500 # tweak 300..700 depending on your environment

t = TelemetrixSync()
t.set_analog_input(A0)
t.set_output(LED)

print("Reading LDR on A0. LED turns ON when it's dark (value > THRESHOLD).")
try:
    while True:
        val = t.analog_read(A0, default=None)
        if val is None:
            time.sleep(0.05); continue
        # Debug print
        print("A0 =", val)
        # Simple rule: dark -> LED ON
        if val > THRESHOLD:
            t.digital_write(LED, 1)
        else:
            t.digital_write(LED, 0)
        time.sleep(0.1)
except KeyboardInterrupt:
    t.shutdown()
