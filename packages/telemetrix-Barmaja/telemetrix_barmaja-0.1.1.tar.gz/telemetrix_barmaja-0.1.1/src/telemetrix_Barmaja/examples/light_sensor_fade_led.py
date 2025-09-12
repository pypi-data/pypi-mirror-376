# light_sensor_fade_led.py
# -----------------------------------------------------------
# LDR (A0) -> LED brightness (PWM on D9) using telemetrix_lite
#
# Wiring (voltage divider):
#   - LDR -> 5V
#   - 10k resistor -> GND
#   - Junction (LDR+10k) -> A0
# LED:
#   - D9 (PWM) -> 220Ω -> LED -> GND
#
# Mapping logic:
#   - Brighter room => LOWER A0 reading for typical divider (LDR R drops)
#   - We invert the value so brighter => brighter LED (feel free to flip)
#
# Teacher tips:
#   - Ask students to cover the LDR with a hand: reading goes HIGH, LED dims.
#   - Shine a phone flashlight: reading goes LOW, LED brightens.
#   - Optional: calibrate MIN/MAX by printing values in your room.
# -----------------------------------------------------------

import time
from telemetrix_Barmaja import TelemetrixSync

A0 = 0
LED = 9

# Optional: clamp and map helpers
def clamp(val, lo, hi):
    return lo if val < lo else hi if val > hi else val

def map_range(x, in_min, in_max, out_min, out_max):
    # linear map x from [in_min,in_max] to [out_min,out_max]
    if in_max == in_min:
        return out_min
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# Initial "guessed" calibration; adjust after printing a few readings
ADC_MIN = 100   # typical bright
ADC_MAX = 900   # typical dark

t = TelemetrixSync()
t.set_analog_input(A0)
t.set_output(LED)

try:
    while True:
        a = t.analog_read(A0, default=None)
        if a is None:
            time.sleep(0.05); continue
        # Invert so brighter => higher PWM
        a_clamped = clamp(a, ADC_MIN, ADC_MAX)
        inv = ADC_MAX - (a_clamped - ADC_MIN)  # invert within calibrated range
        pwm = map_range(inv, 0, (ADC_MAX - ADC_MIN), 0, 255)
        t.pwm_write(LED, pwm)
        print(f"A0={a:4d} -> PWM={pwm:3d}")
        time.sleep(0.05)
except KeyboardInterrupt:
    t.pwm_write(LED, 0); t.shutdown()
