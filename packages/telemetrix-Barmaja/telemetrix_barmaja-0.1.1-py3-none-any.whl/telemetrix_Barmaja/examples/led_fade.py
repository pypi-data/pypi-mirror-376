# led_fade.py
# -----------------------------------------------------------
# LED fade on PWM pin using telemetrix_lite
#
# Wiring:
#   - LED: PWM pin 9 -> 220Ω -> LED -> GND
# -----------------------------------------------------------

import time
from telemetrix_Barmaja import TelemetrixSync

LED = 9  # PWM-capable pin

t = TelemetrixSync()
t.set_output(LED)  # we'll use pwm_write; set_output is harmless

print("Fading LED on pin 9...")
try:
    while True:
        # Fade up
        for v in range(0, 256, 5):
            t.pwm_write(LED, v); time.sleep(0.02)
        # Fade down
        for v in range(255, -1, -5):
            t.pwm_write(LED, v); time.sleep(0.02)
except KeyboardInterrupt:
    t.shutdown()
